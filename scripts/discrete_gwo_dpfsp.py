"""Random-key Grey Wolf Optimizer for the DPFSP-DD.

The search equations follow Mirjalili et al. (2014). The random-key
representation and decoder are a problem-specific adaptation, not a
canonical discrete GWO.
"""
from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from typing import Literal

import numpy as np

from scripts.dpfsp_dd import DPFSPInstance, DPFSPEvaluator

Decay = Literal["linear", "quadratic"]


@dataclass(frozen=True, slots=True)
class GWOResult:
    """Best decoded solution and reproducibility counters."""

    best_solution: tuple[tuple[int, ...], ...]
    best_fitness: int
    evaluations: int
    generations: int
    history: tuple[int, ...]
    best_position: tuple[float, ...]
    unique_decoded_solutions: int
    coordinate_saturation_fraction: float


class RandomKeyDecoder:
    """Decode 2n continuous keys into factory assignments and job orders."""

    def __init__(self, instance: DPFSPInstance):
        if not isinstance(instance, DPFSPInstance):
            raise TypeError("instance must be a DPFSPInstance")
        self.instance = instance
        self.dimension = 2 * instance.jobs

    def decode(self, position: np.ndarray | list[float] | tuple[float, ...]) -> tuple[tuple[int, ...], ...]:
        keys = np.asarray(position, dtype=float)
        if keys.ndim != 1 or keys.size != self.dimension:
            raise ValueError(f"position must be a 1-D vector of length {self.dimension}")
        if not np.all(np.isfinite(keys)):
            raise ValueError("position must contain only finite values")

        n = self.instance.jobs
        factories = self.instance.factories
        assignment_keys = np.clip(keys[:n], 0.0, 1.0)
        priority_keys = np.clip(keys[n:], 0.0, 1.0)

        # x == 1 maps to the final factory rather than the invalid index F.
        factory_ids = np.minimum((assignment_keys * factories).astype(int), factories - 1)
        assigned: list[list[int]] = [[] for _ in range(factories)]
        for job, factory in enumerate(factory_ids):
            assigned[int(factory)].append(job)

        solution: list[tuple[int, ...]] = []
        for jobs in assigned:
            if not jobs:
                solution.append(())
                continue
            job_array = np.asarray(jobs, dtype=int)  # ascending IDs
            order = np.argsort(priority_keys[job_array], kind="stable")
            solution.append(tuple(int(job_array[index]) for index in order))
        return tuple(solution)


def canonical_solution_key(solution: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    """Canonicalize labels of identical factories for uniqueness/grouping."""
    return tuple(sorted(tuple(sequence) for sequence in solution))


class RandomKeyGWO:
    """Synchronous GWO using random keys and the real DPFSP-DD evaluator.

    max_evaluations includes the initial population. Only complete population
    batches are evaluated; a partial final generation is never run.
    """

    def __init__(
        self,
        instance: DPFSPInstance,
        *,
        n_wolves: int = 30,
        max_evaluations: int = 5940,
        seed: int | None = None,
        a_decay: Decay = "linear",
    ):
        if isinstance(n_wolves, bool) or not isinstance(n_wolves, Integral) or n_wolves < 3:
            raise ValueError("n_wolves must be an integer >= 3")
        if isinstance(max_evaluations, bool) or not isinstance(max_evaluations, Integral):
            raise TypeError("max_evaluations must be an integer")
        if max_evaluations < n_wolves:
            raise ValueError("max_evaluations must cover the initial population")
        if a_decay not in ("linear", "quadratic"):
            raise ValueError("a_decay must be 'linear' or 'quadratic'")
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, Integral)):
            raise TypeError("seed must be an integer or None")

        self.instance = instance
        self.evaluator = DPFSPEvaluator(instance)
        self.decoder = RandomKeyDecoder(instance)
        self.n_wolves = int(n_wolves)
        self.max_evaluations = int(max_evaluations)
        self.seed = None if seed is None else int(seed)
        self.a_decay = a_decay
        self.n_evals = 0
        self.generations = 0

        # Number of complete update batches after the initial population.
        self.max_generations = self.max_evaluations // self.n_wolves - 1

    def _compute_a(self, iteration: int) -> float:
        if self.max_generations <= 0:
            return 0.0
        progress = iteration / self.max_generations
        if self.a_decay == "linear":
            return 2.0 * (1.0 - progress)
        return 2.0 * (1.0 - progress**2)

    def _update_positions(
        self,
        positions: np.ndarray,
        leaders: tuple[np.ndarray, np.ndarray, np.ndarray],
        a: float,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Update a full generation against one frozen snapshot of leaders."""
        candidates = []
        for leader in leaders:
            r1 = rng.random(size=positions.shape)
            r2 = rng.random(size=positions.shape)
            coefficient_a = 2.0 * a * r1 - a
            coefficient_c = 2.0 * r2
            distance = np.abs(coefficient_c * leader[np.newaxis, :] - positions)
            candidates.append(leader[np.newaxis, :] - coefficient_a * distance)
        updated = (candidates[0] + candidates[1] + candidates[2]) / 3.0
        return np.clip(updated, 0.0, 1.0)

    def optimize(self) -> GWOResult:
        rng = np.random.default_rng(self.seed)
        self.n_evals = 0
        self.generations = 0

        positions = rng.random((self.n_wolves, self.decoder.dimension))
        fitness = np.empty(self.n_wolves, dtype=np.int64)
        decoded: list[tuple[tuple[int, ...], ...]] = []
        unique_solutions: set[tuple[tuple[int, ...], ...]] = set()
        saturated_coordinates = 0
        generated_coordinates = 0
        for index, position in enumerate(positions):
            solution = self.decoder.decode(position)
            decoded.append(solution)
            unique_solutions.add(canonical_solution_key(solution))
            fitness[index] = self.evaluator.evaluate(solution).total_tardiness
            self.n_evals += 1

        # Stable ordering makes ties reproducible. Leaders are a best-so-far archive.
        order = np.argsort(fitness, kind="stable")
        leader_positions = [positions[index].copy() for index in order[:3]]
        leader_fitness = [int(fitness[index]) for index in order[:3]]
        leader_solutions = [decoded[index] for index in order[:3]]
        history = [leader_fitness[0]]

        for generation in range(self.max_generations):
            # Freeze alpha, beta and delta for every wolf in this generation.
            frozen_leaders = tuple(position.copy() for position in leader_positions)
            new_positions = self._update_positions(
                positions, frozen_leaders, self._compute_a(generation), rng
            )
            saturated_coordinates += int(np.count_nonzero((new_positions == 0.0) | (new_positions == 1.0)))
            generated_coordinates += int(new_positions.size)

            new_fitness = np.empty(self.n_wolves, dtype=np.int64)
            new_solutions: list[tuple[tuple[int, ...], ...]] = []
            for index, position in enumerate(new_positions):
                solution = self.decoder.decode(position)
                new_solutions.append(solution)
                unique_solutions.add(canonical_solution_key(solution))
                new_fitness[index] = self.evaluator.evaluate(solution).total_tardiness
                self.n_evals += 1

            # Merge the previous best-so-far archive with the whole new generation.
            pool_positions = leader_positions + [row.copy() for row in new_positions]
            pool_fitness = np.asarray(leader_fitness + new_fitness.tolist(), dtype=np.int64)
            pool_solutions = leader_solutions + new_solutions
            pool_order = np.argsort(pool_fitness, kind="stable")[:3]
            leader_positions = [pool_positions[index].copy() for index in pool_order]
            leader_fitness = [int(pool_fitness[index]) for index in pool_order]
            leader_solutions = [pool_solutions[index] for index in pool_order]

            positions = new_positions
            self.generations += 1
            history.append(leader_fitness[0])

        return GWOResult(
            best_solution=leader_solutions[0],
            best_fitness=leader_fitness[0],
            evaluations=self.n_evals,
            generations=self.generations,
            history=tuple(history),
            best_position=tuple(float(value) for value in leader_positions[0]),
            unique_decoded_solutions=len(unique_solutions),
            coordinate_saturation_fraction=(
                saturated_coordinates / generated_coordinates if generated_coordinates else 0.0
            ),
        )
