"""Taillard PFSP parser and makespan evaluator (single permutation, no due dates)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np


@dataclass(frozen=True)
class TaillardInstance:
    name: str
    processing_times: np.ndarray
    published_seed: int | None = None
    upper_bound: int | None = None
    lower_bound: int | None = None

    @property
    def n_jobs(self) -> int:
        return int(self.processing_times.shape[0])

    @property
    def n_machines(self) -> int:
        return int(self.processing_times.shape[1])


def load_taillard_instance(path: str | Path) -> TaillardInstance:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    lines = []
    comment_numeric_rows = []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if "#" in raw:
            comment = raw.split("#", 1)[1]
            numbers = [int(x) for x in re.findall(r"\d+", comment)]
            if len(numbers) >= 5:
                comment_numeric_rows.append(numbers)
        line = raw.split("#", 1)[0].strip()
        if line:
            lines.append(line)

    if not lines:
        raise ValueError(f"{path}: empty instance")

    # Standard PISCO mirror format has a dimensions line followed by n job rows.
    # Also accept the classic Taillard header with n, m, seed, UB, LB on one line.
    first = [int(x) for x in re.findall(r"-?\d+", lines[0])]
    if len(first) >= 5:
        n_jobs, n_machines, seed, ub, lb = first[:5]
        data_lines = lines[1:]
    elif len(first) == 2:
        n_jobs, n_machines = first
        metadata_row = next(
            (row for row in comment_numeric_rows
             if row[0] == n_jobs and row[1] == n_machines),
            None,
        )
        if metadata_row is not None:
            _, _, seed, ub, lb = metadata_row[:5]
        else:
            seed = ub = lb = None
        data_lines = lines[1:]
    elif len(lines) >= 2:
        n_jobs, n_machines = int(lines[0]), int(lines[1])
        seed = ub = lb = None
        data_lines = lines[2:]
    else:
        raise ValueError(f"{path}: cannot parse dimensions")

    if n_jobs <= 0 or n_machines <= 0:
        raise ValueError(f"{path}: dimensions must be positive")

    values = []
    for line in data_lines:
        row = [int(x) for x in line.split()]
        values.extend(row)

    expected = n_jobs * n_machines
    if len(values) != expected:
        raise ValueError(
            f"{path}: expected {expected} processing times, found {len(values)}"
        )
    matrix = np.asarray(values, dtype=np.int64).reshape(n_jobs, n_machines)
    if np.any(matrix <= 0):
        raise ValueError(f"{path}: processing times must be positive")

    return TaillardInstance(
        name=path.stem,
        processing_times=matrix,
        published_seed=seed,
        upper_bound=ub,
        lower_bound=lb,
    )


def makespan(processing_times: np.ndarray, permutation) -> int:
    """Evaluate PFSP Cmax using the standard completion-time recurrence."""
    p = np.asarray(processing_times)
    order = np.asarray(permutation)
    if p.ndim != 2 or p.shape[0] == 0 or p.shape[1] == 0:
        raise ValueError("processing_times must be a non-empty 2D matrix")
    if not np.issubdtype(p.dtype, np.integer) or np.any(p <= 0):
        raise ValueError("processing_times must contain positive integers")
    if order.ndim != 1 or order.size != p.shape[0]:
        raise ValueError("permutation must contain exactly one job id per job")
    if not np.issubdtype(order.dtype, np.integer):
        if not np.all(np.isfinite(order)) or not np.all(order == np.floor(order)):
            raise ValueError("permutation must contain integer job ids")
    order = order.astype(np.int64, copy=False)
    if not np.array_equal(np.sort(order), np.arange(p.shape[0])):
        raise ValueError("permutation must contain every job exactly once")

    completion = np.zeros(p.shape[1], dtype=np.int64)
    for job in order:
        completion[0] += p[job, 0]
        for machine in range(1, p.shape[1]):
            completion[machine] = max(
                completion[machine], completion[machine - 1]
            ) + p[job, machine]
    return int(completion[-1])
