"""Synchronous Grey Wolf Optimizer for PFSP using random-key encoding."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scripts.pfs_taillard import makespan


@dataclass
class GWOResult:
    best_fitness: int
    best_permutation: np.ndarray
    convergence: np.ndarray
    evaluations: int


def decode_random_keys(keys: np.ndarray) -> np.ndarray:
    keys = np.asarray(keys, dtype=float)
    if keys.ndim != 1 or keys.size == 0 or not np.all(np.isfinite(keys)):
        raise ValueError("keys must be a non-empty finite vector")
    return np.argsort(keys, kind="stable")


def gwo_pfs(
    processing_times: np.ndarray,
    *,
    n_wolves: int = 30,
    iterations: int = 500,
    seed: int = 0,
) -> GWOResult:
    """Run GWO with canonical alpha/beta/delta equations and synchronous updates.

    Random keys map continuous positions to permutations by stable argsort.
    The three leaders are frozen during each generation. The parameter a
    decreases linearly from 2 to 0 across the configured iterations.
    """
    p = np.asarray(processing_times)
    if p.ndim != 2 or p.shape[0] == 0 or p.shape[1] == 0:
        raise ValueError("processing_times must be a non-empty matrix")
    if n_wolves < 3:
        raise ValueError("n_wolves must be at least 3")
    if iterations < 1:
        raise ValueError("iterations must be positive")

    rng = np.random.default_rng(seed)
    n_jobs = p.shape[0]
    positions = rng.uniform(0.0, 1.0, size=(n_wolves, n_jobs))
    fitness = np.asarray(
        [makespan(p, decode_random_keys(wolf)) for wolf in positions],
        dtype=np.int64,
    )
    evaluations = n_wolves

    leader_indices = np.argsort(fitness, kind="stable")[:3]
    leaders = positions[leader_indices].copy()
    leader_fitness = fitness[leader_indices].copy()
    best_position = leaders[0].copy()
    best_fitness = int(leader_fitness[0])
    history = [best_fitness]

    for iteration in range(iterations):
        a = 2.0 - 2.0 * iteration / iterations
        # All wolves use the same frozen alpha/beta/delta from this generation.
        r1 = rng.random((3, n_wolves, n_jobs))
        r2 = rng.random((3, n_wolves, n_jobs))
        A = 2.0 * a * r1 - a
        C = 2.0 * r2

        candidates = []
        for leader_idx in range(3):
            leader = leaders[leader_idx]
            D = np.abs(C[leader_idx] * leader[None, :] - positions)
            candidates.append(leader[None, :] - A[leader_idx] * D)
        new_positions = np.mean(candidates, axis=0)
        new_positions = np.clip(new_positions, 0.0, 1.0)

        new_fitness = np.asarray(
            [makespan(p, decode_random_keys(wolf)) for wolf in new_positions],
            dtype=np.int64,
        )
        evaluations += n_wolves

        # Update the persistent alpha/beta/delta archive only after the
        # complete generation has been evaluated (synchronous semantics).
        pool_positions = np.vstack((leaders, new_positions))
        pool_fitness = np.concatenate((leader_fitness, new_fitness))
        order = np.argsort(pool_fitness, kind="stable")[:3]
        leaders = pool_positions[order].copy()
        leader_fitness = pool_fitness[order].copy()

        if int(leader_fitness[0]) < best_fitness:
            best_fitness = int(leader_fitness[0])
            best_position = leaders[0].copy()
        history.append(best_fitness)

    return GWOResult(
        best_fitness=best_fitness,
        best_permutation=decode_random_keys(best_position),
        convergence=np.asarray(history, dtype=np.int64),
        evaluations=evaluations,
    )
