"""Independent data model, parser and evaluator for DPFSP with Total Tardiness.

This module deliberately has no dependency on GWO, Fuzzy, Surrogate or NumPy.
"""
from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from pathlib import Path
from typing import Sequence


def _require_int(value: object, name: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
    result = int(value)
    if result < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {result}")
    return result


@dataclass(frozen=True, slots=True)
class DPFSPInstance:
    """Immutable DPFSP-DD instance; job and machine identifiers are zero-based."""

    processing_times: tuple[tuple[int, ...], ...]
    due_dates: tuple[int, ...]
    factories: int

    def __post_init__(self) -> None:
        factories = _require_int(self.factories, "factories", minimum=1)
        object.__setattr__(self, "factories", factories)
        try:
            processing = tuple(tuple(row) for row in self.processing_times)
            due_dates = tuple(self.due_dates)
        except TypeError as exc:
            raise TypeError("processing_times and due_dates must be iterable") from exc
        if not processing:
            raise ValueError("processing_times must contain at least one job")
        machines = len(processing[0])
        if machines < 1:
            raise ValueError("processing_times must contain at least one machine")
        for job, row in enumerate(processing):
            if len(row) != machines:
                raise ValueError(f"processing_times row {job} has {len(row)} machines; expected {machines}")
            for machine, value in enumerate(row):
                _require_int(value, f"processing_times[{job}][{machine}]", minimum=1)
        if len(due_dates) != len(processing):
            raise ValueError(f"due_dates has {len(due_dates)} values; expected {len(processing)}")
        for job, value in enumerate(due_dates):
            _require_int(value, f"due_dates[{job}]", minimum=0)
        object.__setattr__(self, "processing_times",
                           tuple(tuple(int(value) for value in row) for row in processing))
        object.__setattr__(self, "due_dates", tuple(int(value) for value in due_dates))

    @property
    def jobs(self) -> int:
        return len(self.processing_times)

    @property
    def machines(self) -> int:
        return len(self.processing_times[0])


@dataclass(frozen=True, slots=True)
class DPFSPResult:
    """Auditable objective and schedule details returned by the evaluator."""

    total_tardiness: int
    completion_times: tuple[int, ...]
    tardiness: tuple[int, ...]
    factory_by_job: tuple[int, ...]
    position_by_job: tuple[int, ...]
    # [factory][position][machine] -> operation completion time
    operation_completion_times: tuple[tuple[tuple[int, ...], ...], ...]


def parse_dpfsp_instance_text(text: str, *, source: str = "<text>") -> DPFSPInstance:
    """Parse n/m, F, processing rows of machine/time pairs, Duedate and due dates."""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    lines = [(number, line.strip()) for number, line in enumerate(text.splitlines(), 1) if line.strip()]
    if len(lines) < 3:
        raise ValueError(f"{source}: expected headers and instance body")

    def parse_ints(line_number: int, value: str, context: str) -> list[int]:
        try:
            return [int(token) for token in value.split()]
        except ValueError as exc:
            raise ValueError(f"{source}: line {line_number}: {context} must contain integers") from exc

    header_line, header_value = lines[0]
    dimensions = parse_ints(header_line, header_value, "dimension header")
    if len(dimensions) != 2:
        raise ValueError(f"{source}: line {header_line}: expected exactly 'jobs machines'")
    jobs = _require_int(dimensions[0], "jobs", minimum=1)
    machines = _require_int(dimensions[1], "machines", minimum=1)

    factory_line, factory_value = lines[1]
    factory_tokens = parse_ints(factory_line, factory_value, "factory header")
    if len(factory_tokens) != 1:
        raise ValueError(f"{source}: line {factory_line}: expected exactly one factory count")
    factories = _require_int(factory_tokens[0], "factories", minimum=1)

    marker_indices = [i for i, (_, value) in enumerate(lines) if value.casefold() == "duedate"]
    if len(marker_indices) != 1:
        raise ValueError(f"{source}: expected exactly one Duedate marker; found {len(marker_indices)}")
    marker = marker_indices[0]
    if marker < 2:
        raise ValueError(f"{source}: Duedate marker appears before processing rows")
    processing_lines, due_lines = lines[2:marker], lines[marker + 1:]
    if len(processing_lines) != jobs:
        raise ValueError(f"{source}: expected {jobs} processing rows; found {len(processing_lines)}")
    if len(due_lines) != jobs:
        raise ValueError(f"{source}: expected {jobs} due-date rows; found {len(due_lines)}")

    matrix: list[tuple[int, ...]] = []
    expected_ids = set(range(machines))
    for job, (line_number, value) in enumerate(processing_lines):
        tokens = parse_ints(line_number, value, f"processing row for job {job}")
        if len(tokens) != 2 * machines:
            raise ValueError(f"{source}: line {line_number}: expected {2 * machines} integers; found {len(tokens)}")
        row = [0] * machines
        seen: set[int] = set()
        for offset in range(0, len(tokens), 2):
            machine_id, processing_time = tokens[offset:offset + 2]
            if machine_id not in expected_ids:
                raise ValueError(f"{source}: line {line_number}: machine id {machine_id} is outside 0..{machines - 1}")
            if machine_id in seen:
                raise ValueError(f"{source}: line {line_number}: duplicate machine id {machine_id}")
            _require_int(processing_time, f"job {job}, machine {machine_id} processing time", minimum=1)
            seen.add(machine_id)
            row[machine_id] = processing_time
        if seen != expected_ids:
            raise ValueError(f"{source}: line {line_number}: machine ids must be exactly {sorted(expected_ids)}")
        matrix.append(tuple(row))

    due_dates: list[int] = []
    for job, (line_number, value) in enumerate(due_lines):
        tokens = parse_ints(line_number, value, f"due date for job {job}")
        if len(tokens) != 1:
            raise ValueError(f"{source}: line {line_number}: expected exactly one due date integer")
        due_dates.append(_require_int(tokens[0], f"due_dates[{job}]", minimum=0))
    return DPFSPInstance(tuple(matrix), tuple(due_dates), factories)


def load_dpfsp_instance(path: str | Path, *, encoding: str = "utf-8-sig") -> DPFSPInstance:
    """Load and parse a plain-text DPFSP-DD instance file."""
    instance_path = Path(path)
    if not instance_path.is_file():
        raise FileNotFoundError(f"DPFSP-DD instance not found: {instance_path}")
    return parse_dpfsp_instance_text(instance_path.read_text(encoding=encoding), source=str(instance_path))


class DPFSPEvaluator:
    """Deterministic evaluator for decoded factory sequences."""

    def __init__(self, instance: DPFSPInstance):
        if not isinstance(instance, DPFSPInstance):
            raise TypeError("instance must be a DPFSPInstance")
        self.instance = instance

    def evaluate(self, solution: Sequence[Sequence[int]]) -> DPFSPResult:
        """Evaluate exactly F sequences; empty factory sequences are allowed."""
        if isinstance(solution, (str, bytes)):
            raise TypeError("solution must be a sequence of factory job sequences")
        try:
            factory_sequences = tuple(tuple(sequence) for sequence in solution)
        except TypeError as exc:
            raise TypeError("solution must be an iterable of job sequences") from exc
        if len(factory_sequences) != self.instance.factories:
            raise ValueError(f"solution has {len(factory_sequences)} factory sequences; expected {self.instance.factories}")

        seen: set[int] = set()
        factory_by_job = [-1] * self.instance.jobs
        position_by_job = [-1] * self.instance.jobs
        completion_times = [0] * self.instance.jobs
        tardiness = [0] * self.instance.jobs
        operation_schedules: list[tuple[tuple[int, ...], ...]] = []

        for factory, sequence in enumerate(factory_sequences):
            machine_available = [0] * self.instance.machines
            factory_schedule: list[tuple[int, ...]] = []
            for position, job_id in enumerate(sequence):
                job = _require_int(job_id, f"solution[{factory}][{position}]", minimum=0)
                if job >= self.instance.jobs:
                    raise ValueError(f"job id {job} at factory {factory}, position {position} is outside 0..{self.instance.jobs - 1}")
                if job in seen:
                    raise ValueError(f"job {job} appears more than once in solution")
                seen.add(job)
                factory_by_job[job], position_by_job[job] = factory, position

                previous_machine_completion = 0
                row_completion: list[int] = []
                for machine, processing_time in enumerate(self.instance.processing_times[job]):
                    start = max(previous_machine_completion, machine_available[machine])
                    finish = start + processing_time
                    row_completion.append(finish)
                    previous_machine_completion = finish
                    machine_available[machine] = finish
                factory_schedule.append(tuple(row_completion))
                completion_times[job] = row_completion[-1]
                tardiness[job] = max(0, completion_times[job] - self.instance.due_dates[job])
            operation_schedules.append(tuple(factory_schedule))

        missing = sorted(set(range(self.instance.jobs)) - seen)
        if missing:
            raise ValueError(f"solution is missing jobs: {missing}")
        return DPFSPResult(
            total_tardiness=sum(tardiness),
            completion_times=tuple(completion_times),
            tardiness=tuple(tardiness),
            factory_by_job=tuple(factory_by_job),
            position_by_job=tuple(position_by_job),
            operation_completion_times=tuple(operation_schedules),
        )
