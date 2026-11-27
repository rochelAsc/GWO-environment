"""Surrogate-assisted synchronous random-key GWO for Taillard PFSP."""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable

import numpy as np

from scripts.gwo_pfs import decode_random_keys
from scripts.pfs_taillard import makespan
from scripts.run_week4_surrogate import random_keys_features


@dataclass
class SurrogateGWOResult:
    best_fitness: int
    best_permutation: np.ndarray
    convergence: np.ndarray
    exact_evaluations: int
    surrogate_predictions: int
    inference_batches: int
    exact_evaluation_seconds: float
    surrogate_seconds: float
    final_population: np.ndarray
    trace: list[dict[str, float | int | str]]


def gwo_pfs_surrogate(
    processing_times: np.ndarray,
    model: Any,
    *,
    n_wolves: int = 30,
    iterations: int = 500,
    seed: int = 0,
    top_k: int = 3,
    a_start: float = 2.0,
    a_end: float = 0.0,
    a_exponent: float = 1.0,
    population_observer: Callable[[int, np.ndarray], None] | None = None,
) -> SurrogateGWOResult:
    """Run GWO, using the model only to screen candidates before exact evaluation.

    The initial population is evaluated exactly. Every generation predicts all
    new candidates in one batch, exactly evaluates the top-k predictions, and
    updates the elite archive using exact fitness only.
    """
    p = np.asarray(processing_times)
    if p.ndim != 2 or p.shape[0] == 0 or p.shape[1] == 0:
        raise ValueError("processing_times must be a non-empty matrix")
    if n_wolves < 3 or iterations < 1:
        raise ValueError("n_wolves must be >= 3 and iterations must be positive")
    if not 1 <= top_k <= n_wolves:
        raise ValueError("top_k must be in [1, n_wolves]")
    if not all(np.isfinite(v) for v in (a_start, a_end, a_exponent)):
        raise ValueError("schedule parameters must be finite")
    if a_start <= a_end or a_end < 0 or a_exponent <= 0:
        raise ValueError("require a_start > a_end >= 0 and exponent > 0")
    if not callable(getattr(model, "predict", None)):
        raise TypeError("model must provide predict(features)")

    rng = np.random.default_rng(seed)
    n_jobs = p.shape[0]
    positions = rng.uniform(0.0, 1.0, size=(n_wolves, n_jobs))
    exact_seconds = 0.0
    surrogate_seconds = 0.0
    exact_evaluations = 0
    surrogate_predictions = 0
    inference_batches = 0

    def evaluate_exact(keys: np.ndarray) -> int:
        nonlocal exact_seconds, exact_evaluations
        started = time.perf_counter()
        value = int(makespan(p, decode_random_keys(keys)))
        exact_seconds += time.perf_counter() - started
        exact_evaluations += 1
        return value

    if population_observer is not None:
        population_observer(-1, positions.copy())
    initial_fitness = np.asarray([evaluate_exact(w) for w in positions], dtype=np.int64)
    order = np.argsort(initial_fitness, kind="stable")[:3]
    leaders = positions[order].copy()
    leader_fitness = initial_fitness[order].copy()
    best_position = leaders[0].copy()
    best_fitness = int(leader_fitness[0])
    history = [best_fitness]
    trace: list[dict[str, float | int | str]] = []

    for iteration in range(iterations):
        progress = iteration / iterations
        if a_start == 2.0 and a_end == 0.0 and a_exponent == 1.0:
            a = 2.0 - 2.0 * iteration / iterations
        else:
            a = a_end + (a_start - a_end) * (1.0 - progress) ** a_exponent

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
        if population_observer is not None:
            population_observer(iteration, new_positions.copy())

        infer_start = time.perf_counter()
        features = np.vstack([random_keys_features(row) for row in new_positions])
        predicted = np.asarray(model.predict(features), dtype=np.float64).reshape(-1)
        surrogate_seconds += time.perf_counter() - infer_start
        surrogate_predictions += int(predicted.size)
        inference_batches += 1
        if predicted.size != n_wolves or not np.all(np.isfinite(predicted)):
            raise ValueError("model.predict must return one finite prediction per wolf")

        selected = np.argsort(predicted, kind="stable")[:top_k]
        exact_selected = np.asarray(
            [evaluate_exact(new_positions[index]) for index in selected],
            dtype=np.int64,
        )

        selected_permutations = [
            tuple(int(job) for job in decode_random_keys(new_positions[index]))
            for index in selected
        ]
        duplicate_count = len(selected_permutations) - len(set(selected_permutations))

        pool_positions = np.vstack((leaders, new_positions[selected]))
        pool_fitness = np.concatenate((leader_fitness, exact_selected))
        elite_order = np.argsort(pool_fitness, kind="stable")[:3]
        leaders = pool_positions[elite_order].copy()
        leader_fitness = pool_fitness[elite_order].copy()
        positions = new_positions

        if int(leader_fitness[0]) < best_fitness:
            best_fitness = int(leader_fitness[0])
            best_position = leaders[0].copy()
        history.append(best_fitness)

        for rank, (candidate_index, predicted_value, exact_value) in enumerate(
            zip(selected, predicted[selected], exact_selected), start=1
        ):
            trace.append({
                "iteration": iteration,
                "candidate_index": int(candidate_index),
                "predicted_rank": rank,
                "predicted_makespan": float(predicted_value),
                "exact_makespan": int(exact_value),
                "selected_duplicate_count_generation": int(duplicate_count),
            })

    expected_exact = n_wolves + top_k * iterations
    expected_predictions = n_wolves * iterations
    if exact_evaluations != expected_exact or surrogate_predictions != expected_predictions:
        raise RuntimeError("internal evaluation counters do not match the configured budget")

    return SurrogateGWOResult(
        best_fitness=best_fitness,
        best_permutation=decode_random_keys(best_position),
        convergence=np.asarray(history, dtype=np.int64),
        exact_evaluations=exact_evaluations,
        surrogate_predictions=surrogate_predictions,
        inference_batches=inference_batches,
        exact_evaluation_seconds=exact_seconds,
        surrogate_seconds=surrogate_seconds,
        final_population=positions.copy(),
        trace=trace,
    )
