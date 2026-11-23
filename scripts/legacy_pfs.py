"""Strict, testable implementation of the historical single-factory PFS engine.

This module characterizes the file layout assumed by the original Colab export.
It does not claim that the unavailable historical instance files have been
recovered or that this format is a canonical Taillard format.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np


def _integer_array(values, *, name: str, ndim: int) -> np.ndarray:
    raw = np.asarray(values)
    if np.iscomplexobj(raw):
        raise ValueError(f"{name} must contain real numeric values")
    if raw.ndim != ndim:
        raise ValueError(f"{name} must be {ndim}-dimensional; got shape {raw.shape}")
    if not np.issubdtype(raw.dtype, np.number) or not np.all(np.isfinite(raw)):
        raise ValueError(f"{name} must contain finite numeric values")
    if not np.all(raw == np.floor(raw)):
        raise ValueError(f"{name} must contain integers")
    return raw.astype(np.int64, copy=True)


def parse_legacy_pfs_text(text: str, *, source: str = "<text>"):
    """Parse the legacy layout: dimensions, one metadata line, job rows,
    Duedate marker, then one due date per job.

    Each processing row contains exactly M pairs (zero-based machine id,
    positive processing time). The metadata line is retained as opaque input
    because the historical parser skipped it without interpreting it.
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")

    lines = [(number, line.strip()) for number, line in enumerate(text.splitlines(), 1)
             if line.strip()]
    if len(lines) < 4:
        raise ValueError(f"{source}: incomplete instance")

    def integers(line_number: int, value: str, description: str) -> list[int]:
        try:
            return [int(token) for token in value.split()]
        except ValueError as exc:
            raise ValueError(
                f"{source}: line {line_number}: {description} must contain integers"
            ) from exc

    header_number, header = lines[0]
    dimensions = integers(header_number, header, "dimension header")
    if len(dimensions) != 2 or any(value <= 0 for value in dimensions):
        raise ValueError(
            f"{source}: line {header_number}: expected two positive integers (jobs machines)"
        )
    jobs, machines = dimensions

    marker_positions = [index for index, (_, value) in enumerate(lines)
                        if value.casefold() == "duedate"]
    if len(marker_positions) != 1:
        raise ValueError(
            f"{source}: expected exactly one Duedate marker; found {len(marker_positions)}"
        )
    marker = marker_positions[0]
    processing_rows = lines[2:marker]
    due_rows = lines[marker + 1:]

    if len(processing_rows) != jobs:
        raise ValueError(
            f"{source}: expected {jobs} processing rows after metadata line; "
            f"found {len(processing_rows)}"
        )
    if len(due_rows) != jobs:
        raise ValueError(f"{source}: expected {jobs} due-date rows; found {len(due_rows)}")

    processing = np.zeros((jobs, machines), dtype=np.int64)
    expected_machine_ids = set(range(machines))
    for job, (line_number, row_text) in enumerate(processing_rows):
        tokens = integers(line_number, row_text, f"processing row for job {job}")
        if len(tokens) != 2 * machines:
            raise ValueError(
                f"{source}: line {line_number}: expected {2 * machines} integers "
                f"(machine/time pairs); found {len(tokens)}"
            )
        seen = set()
        for offset in range(0, len(tokens), 2):
            machine_id, processing_time = tokens[offset:offset + 2]
            if machine_id not in expected_machine_ids:
                raise ValueError(
                    f"{source}: line {line_number}: machine id {machine_id} "
                    f"is outside 0..{machines - 1}"
                )
            if machine_id in seen:
                raise ValueError(
                    f"{source}: line {line_number}: duplicate machine id {machine_id}"
                )
            if processing_time <= 0:
                raise ValueError(
                    f"{source}: line {line_number}: processing times must be positive"
                )
            processing[job, machine_id] = processing_time
            seen.add(machine_id)
        if seen != expected_machine_ids:
            raise ValueError(
                f"{source}: line {line_number}: each machine id must appear exactly once"
            )

    due_dates = []
    for job, (line_number, due_text) in enumerate(due_rows):
        values = integers(line_number, due_text, f"due date for job {job}")
        if len(values) != 1 or values[0] < 0:
            raise ValueError(
                f"{source}: line {line_number}: expected one non-negative due date"
            )
        due_dates.append(values[0])

    return jobs, machines, processing, np.asarray(due_dates, dtype=np.int64)


def load_legacy_pfs_instance(path: str | Path, *, encoding: str = "utf-8-sig"):
    instance_path = Path(path)
    if not instance_path.is_file():
        raise FileNotFoundError(f"PFS instance not found: {instance_path}")
    return parse_legacy_pfs_text(
        instance_path.read_text(encoding=encoding), source=str(instance_path)
    )


class FlowShopEngine:
    """Characterized PFS evaluator from the historical Colab implementation."""

    def __init__(self, n_jobs, n_machines, proc_times, due_dates):
        self.proc_times = _integer_array(
            proc_times, name="proc_times", ndim=2
        )
        self.due_dates = _integer_array(due_dates, name="due_dates", ndim=1)
        if self.proc_times.shape != (n_jobs, n_machines):
            raise ValueError(
                f"proc_times shape must be {(n_jobs, n_machines)}; "
                f"got {self.proc_times.shape}"
            )
        if n_jobs < 1 or n_machines < 1:
            raise ValueError("n_jobs and n_machines must be positive")
        if np.any(self.proc_times <= 0):
            raise ValueError("processing times must be positive")
        if self.due_dates.shape != (n_jobs,):
            raise ValueError(f"due_dates must contain exactly {n_jobs} values")
        if np.any(self.due_dates < 0):
            raise ValueError("due_dates must be non-negative")
        self.n_jobs = int(n_jobs)
        self.n_machines = int(n_machines)
        self.cfo_count = 0

    @staticmethod
    def carregar_instancia_txt(caminho_arquivo):
        """Strict replacement for the historical silent-synthetic fallback."""
        return load_legacy_pfs_instance(caminho_arquivo)

    @staticmethod
    def calcular_lower_bound_potts(num_jobs, num_machines, p_matrix, due_dates):
        processing = _integer_array(p_matrix, name="p_matrix", ndim=2)
        due = _integer_array(due_dates, name="due_dates", ndim=1)
        if processing.shape != (num_jobs, num_machines):
            raise ValueError("p_matrix dimensions do not match num_jobs/num_machines")
        if due.shape != (num_jobs,):
            raise ValueError("due_dates length does not match num_jobs")
        if num_jobs < 1 or num_machines < 1 or np.any(processing <= 0) or np.any(due < 0):
            raise ValueError("invalid processing times or due dates")

        max_lateness_global = -float("inf")
        for machine in range(num_machines):
            releases = (np.sum(processing[:, :machine], axis=1)
                        if machine > 0 else np.zeros(num_jobs))
            tails = (np.sum(processing[:, machine + 1:], axis=1)
                     if machine < num_machines - 1 else np.zeros(num_jobs))
            adjusted_due = due - tails
            remaining = processing[:, machine].astype(float)
            time = 0.0
            machine_lateness = -float("inf")

            while np.any(remaining > 0):
                available = (releases <= time) & (remaining > 0)
                if not np.any(available):
                    time = float(np.min(releases[(releases > time) & (remaining > 0)]))
                    continue

                candidates = np.flatnonzero(available)
                job = int(candidates[np.argmin(adjusted_due[candidates])])
                future_releases = releases[(releases > time) & (remaining > 0)]
                next_release = (float(np.min(future_releases))
                                if future_releases.size else float("inf"))
                elapsed = min(remaining[job], next_release - time)
                time += elapsed
                remaining[job] -= elapsed

                if remaining[job] <= 1e-7:
                    machine_lateness = max(
                        machine_lateness, time - adjusted_due[job]
                    )

            max_lateness_global = max(max_lateness_global, machine_lateness)
        return float(max_lateness_global)

    def bucket_sort_decode(self, keys):
        values = np.asarray(keys, dtype=float)
        if values.ndim != 1 or values.size < self.n_jobs:
            raise ValueError(f"keys must be a 1D vector with at least {self.n_jobs} values")
        if not np.all(np.isfinite(values)):
            raise ValueError("keys must contain only finite values")
        return np.argsort(values[:self.n_jobs])

    def _evaluate_sequences(self, sequences, objective):
        if objective not in {"Makespan", "Tardiness"}:
            raise ValueError("objective must be 'Makespan' or 'Tardiness'")
        finish_times = np.zeros((self.n_machines, self.n_jobs), dtype=np.int64)

        machine_time = 0
        for job in sequences[0]:
            machine_time += self.proc_times[job, 0]
            finish_times[0, job] = machine_time

        for machine in range(1, self.n_machines):
            machine_time = 0
            for job in sequences[machine]:
                start = max(machine_time, finish_times[machine - 1, job])
                machine_time = start + self.proc_times[job, machine]
                finish_times[machine, job] = machine_time

        completion = finish_times[-1]
        if objective == "Makespan":
            return int(np.max(completion))
        return int(np.maximum(0, completion - self.due_dates).sum())

    def evaluate(self, keys, mode="PFS", objective="Tardiness"):
        if mode == "PFS":
            sequence = self.bucket_sort_decode(keys)
            sequences = [sequence] * self.n_machines
        else:
            values = np.asarray(keys, dtype=float)
            expected = self.n_jobs * self.n_machines
            if values.ndim != 1 or values.size != expected:
                raise ValueError(
                    f"non-PFS mode requires exactly {expected} keys"
                )
            if not np.all(np.isfinite(values)):
                raise ValueError("keys must contain only finite values")
            sequences = [
                np.argsort(values[machine * self.n_jobs:(machine + 1) * self.n_jobs])
                for machine in range(self.n_machines)
            ]
        self.cfo_count += 1
        return self._evaluate_sequences(sequences, objective)

    def evaluate_with_permutation(self, permutation, objective="Tardiness"):
        values = np.asarray(permutation)
        if values.ndim != 1 or values.size != self.n_jobs:
            raise ValueError(f"permutation must contain exactly {self.n_jobs} job ids")
        if not np.issubdtype(values.dtype, np.integer):
            if not np.all(np.isfinite(values)) or not np.all(values == np.floor(values)):
                raise ValueError("permutation must contain integer job ids")
        sequence = values.astype(np.int64, copy=False)
        if not np.array_equal(np.sort(sequence), np.arange(self.n_jobs)):
            raise ValueError("permutation must contain every job id exactly once")
        self.cfo_count += 1
        return self._evaluate_sequences([sequence] * self.n_machines, objective)
