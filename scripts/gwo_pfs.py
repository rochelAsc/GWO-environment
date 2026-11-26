"""Synchronous Grey Wolf Optimizer for PFSP using random-key encoding."""
from __future__ import annotations
from dataclasses import dataclass
import time
import numpy as np
from scripts.pfs_taillard import makespan

@dataclass
class GWOResult:
    best_fitness: int
    best_permutation: np.ndarray
    convergence: np.ndarray
    evaluations: int
    final_population: np.ndarray
    exact_evaluation_seconds: float

def decode_random_keys(keys: np.ndarray) -> np.ndarray:
    keys = np.asarray(keys, dtype=float)
    if keys.ndim != 1 or keys.size == 0 or not np.all(np.isfinite(keys)):
        raise ValueError("keys must be a non-empty finite vector")
    return np.argsort(keys, kind="stable")

def gwo_pfs(
    processing_times: np.ndarray, *, n_wolves: int = 30, iterations: int = 500,
    seed: int = 0, a_start: float = 2.0, a_end: float = 0.0,
    a_exponent: float = 1.0,
) -> GWOResult:
    """Run synchronous GWO with configurable power-law a schedule."""
    p = np.asarray(processing_times)
    if p.ndim != 2 or p.shape[0] == 0 or p.shape[1] == 0:
        raise ValueError("processing_times must be a non-empty matrix")
    if n_wolves < 3:
        raise ValueError("n_wolves must be at least 3")
    if iterations < 1:
        raise ValueError("iterations must be positive")
    if not np.isfinite(a_start) or not np.isfinite(a_end) or not np.isfinite(a_exponent):
        raise ValueError("a schedule parameters must be finite")
    if a_start <= a_end or a_end < 0:
        raise ValueError("a_start must be greater than a_end, and a_end non-negative")
    if a_exponent <= 0:
        raise ValueError("a_exponent must be positive")

    rng = np.random.default_rng(seed)
    n_jobs = p.shape[0]
    exact_evaluation_seconds = 0.0

    def evaluate(keys):
        nonlocal exact_evaluation_seconds
        started = time.perf_counter()
        value = makespan(p, decode_random_keys(keys))
        exact_evaluation_seconds += time.perf_counter() - started
        return value

    positions = rng.uniform(0.0, 1.0, size=(n_wolves, n_jobs))
    fitness = np.asarray([evaluate(w) for w in positions], dtype=np.int64)
    evaluations = n_wolves
    leader_indices = np.argsort(fitness, kind="stable")[:3]
    leaders = positions[leader_indices].copy()
    leader_fitness = fitness[leader_indices].copy()
    best_position = leaders[0].copy()
    best_fitness = int(leader_fitness[0])
    history = [best_fitness]

    for iteration in range(iterations):
        progress = iteration / iterations
        if a_start == 2.0 and a_end == 0.0 and a_exponent == 1.0:
            a = 2.0 - 2.0 * iteration / iterations
        else:
            a = a_end + (a_start - a_end) * (1.0 - progress) ** a_exponent
        r1 = rng.random((3, n_wolves, n_jobs))
        r2 = rng.random((3, n_wolves, n_jobs))
        A = 2.0 * a * r1 - a
        C = 2.0 * r2
        candidates = []
        for leader_idx in range(3):
            leader = leaders[leader_idx]
            D = np.abs(C[leader_idx] * leader[None, :] - positions)
            candidates.append(leader[None, :] - A[leader_idx] * D)
        new_positions = np.clip(np.mean(candidates, axis=0), 0.0, 1.0)
        new_fitness = np.asarray([evaluate(w) for w in new_positions], dtype=np.int64)
        evaluations += n_wolves
        pool_positions = np.vstack((leaders, new_positions))
        pool_fitness = np.concatenate((leader_fitness, new_fitness))
        order = np.argsort(pool_fitness, kind="stable")[:3]
        leaders = pool_positions[order].copy()
        leader_fitness = pool_fitness[order].copy()
        positions = new_positions
        if int(leader_fitness[0]) < best_fitness:
            best_fitness = int(leader_fitness[0])
            best_position = leaders[0].copy()
        history.append(best_fitness)

    return GWOResult(
        best_fitness=best_fitness,
        best_permutation=decode_random_keys(best_position),
        convergence=np.asarray(history, dtype=np.int64),
        evaluations=evaluations,
        final_population=positions.copy(),
        exact_evaluation_seconds=exact_evaluation_seconds,
    )
