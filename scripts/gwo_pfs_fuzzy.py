"""Synchronous random-key GWO with a Mamdani adaptive exploration controller."""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from scripts.fuzzy_controller import MamdaniGWOController, population_diversity
from scripts.gwo_pfs import decode_random_keys
from scripts.pfs_taillard import makespan


@dataclass
class FuzzyGWOResult:
    best_fitness: int
    best_permutation: np.ndarray
    convergence: np.ndarray
    evaluations: int
    trace: list[dict[str, float | int]]


def gwo_pfs_fuzzy(
    processing_times: np.ndarray,
    *,
    n_wolves: int = 30,
    iterations: int = 500,
    seed: int = 0,
    stagnation_window: int = 20,
    a_start: float = 2.0,
    a_end: float = 0.0,
) -> FuzzyGWOResult:
    """Run GWO under the Week 5 fixed evaluation budget.

    The linear schedule is the reference envelope. Mamdani output scales its
    current a value in [0.5, 1.5], clipped to [0, 2]. Stagnation is the
    number of consecutive non-improving generations divided by a fixed window.
    """
    p = np.asarray(processing_times)
    if p.ndim != 2 or p.shape[0] == 0 or p.shape[1] == 0:
        raise ValueError("processing_times must be a non-empty matrix")
    if n_wolves < 3 or iterations < 1 or stagnation_window < 1:
        raise ValueError("n_wolves >= 3, iterations >= 1 and window >= 1 required")
    if not np.isfinite(a_start) or not np.isfinite(a_end) or a_start <= a_end or a_end < 0:
        raise ValueError("require finite a_start > a_end >= 0")

    rng = np.random.default_rng(seed)
    controller = MamdaniGWOController()
    n_jobs = p.shape[0]
    positions = rng.uniform(0.0, 1.0, size=(n_wolves, n_jobs))
    fitness = np.asarray([makespan(p, decode_random_keys(w)) for w in positions], dtype=np.int64)
    evaluations = n_wolves
    order = np.argsort(fitness, kind="stable")[:3]
    leaders, leader_fitness = positions[order].copy(), fitness[order].copy()
    best_position, best_fitness = leaders[0].copy(), int(leader_fitness[0])
    best_history = [best_fitness]
    stagnant_generations = 0
    trace: list[dict[str, float | int]] = []

    for iteration in range(iterations):
        diversity = population_diversity(positions)
        stagnation = min(stagnant_generations / stagnation_window, 1.0)
        scale = controller(diversity, stagnation)
        progress = iteration / iterations
        base_a = a_end + (a_start - a_end) * (1.0 - progress)
        a = float(np.clip(base_a * scale, 0.0, 2.0))

        r1 = rng.random((3, n_wolves, n_jobs))
        r2 = rng.random((3, n_wolves, n_jobs))
        candidates = []
        for leader_idx in range(3):
            leader = leaders[leader_idx]
            A = 2.0 * a * r1[leader_idx] - a
            C = 2.0 * r2[leader_idx]
            distance = np.abs(C * leader[None, :] - positions)
            candidates.append(leader[None, :] - A * distance)
        new_positions = np.clip(np.mean(candidates, axis=0), 0.0, 1.0)
        new_fitness = np.asarray(
            [makespan(p, decode_random_keys(w)) for w in new_positions], dtype=np.int64
        )
        evaluations += n_wolves

        pool_positions = np.vstack((leaders, new_positions))
        pool_fitness = np.concatenate((leader_fitness, new_fitness))
        selected = np.argsort(pool_fitness, kind="stable")[:3]
        leaders, leader_fitness = pool_positions[selected].copy(), pool_fitness[selected].copy()
        improved = int(leader_fitness[0]) < best_fitness
        if improved:
            best_fitness = int(leader_fitness[0])
            best_position = leaders[0].copy()
            stagnant_generations = 0
        else:
            stagnant_generations += 1
        best_history.append(best_fitness)
        trace.append({
            "iteration": iteration,
            "diversity": diversity,
            "stagnation": stagnation,
            "fuzzy_scale": scale,
            "a": a,
            "best_fitness": best_fitness,
            "improved": int(improved),
        })

    return FuzzyGWOResult(
        best_fitness=best_fitness,
        best_permutation=decode_random_keys(best_position),
        convergence=np.asarray(best_history, dtype=np.int64),
        evaluations=evaluations,
        trace=trace,
    )
