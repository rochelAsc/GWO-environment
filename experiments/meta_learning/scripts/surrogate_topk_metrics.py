"""Top-k selection metrics for PFSP makespan surrogates.

Contract (master runbook S-A1, 2026-11-27)
------------------------------------------
Makespan is lower-is-better. Empates are common on integer makespans.

Policies
~~~~~~~~
- ``strict``: select exactly ``k`` indices. Primary key = score ascending;
  secondary key = original row index ascending (stable, deterministic).
- ``inclusive``: include every candidate whose score equals the score at
  strict position ``k`` (1-based). The selected set can be larger than ``k``.

Do not compare metrics computed under different policies.

Recall
~~~~~~
``|real ∩ predicted| / |real|`` using the sets produced by the same policy.
For ``inclusive``, the denominator is the (variable) size of the real set.

Regret
~~~~~~
- ``best_selected_regret`` = ``min(y_true[selected]) - min(y_true)``
- ``mean_selected_regret`` = ``mean(y_true[selected]) - min(y_true)``

Historical field ``top{k}_regret`` in learning-curve CSVs equals
``best_selected_regret`` under a non-stable argsort strict policy. Keep those
CSVs immutable; use this module for new evaluations.
"""
from __future__ import annotations

from typing import Iterable, Literal

import numpy as np

Policy = Literal["strict", "inclusive"]


def _as_1d(values: np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be 1D")
    if arr.size == 0:
        raise ValueError(f"{name} must be non-empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must contain only finite values")
    return arr


def _validate_k(k: int, n: int) -> int:
    if not isinstance(k, (int, np.integer)) or isinstance(k, bool):
        raise ValueError("k must be a positive integer")
    k_int = int(k)
    if k_int < 1:
        raise ValueError("k must be >= 1")
    if n < 1:
        raise ValueError("scores must be non-empty")
    return min(k_int, n)


def topk_indices_strict(scores: np.ndarray, k: int) -> np.ndarray:
    """Return exactly min(k, n) indices: score asc, then index asc."""
    scores_1d = _as_1d(scores, "scores")
    k_eff = _validate_k(k, scores_1d.size)
    order = np.lexsort((np.arange(scores_1d.size), scores_1d))
    return order[:k_eff].astype(np.int64, copy=False)


def topk_indices_inclusive(scores: np.ndarray, k: int) -> np.ndarray:
    """Return indices with score <= score at strict position k (tied frontier)."""
    scores_1d = _as_1d(scores, "scores")
    k_eff = _validate_k(k, scores_1d.size)
    strict = topk_indices_strict(scores_1d, k_eff)
    threshold = scores_1d[strict[-1]]
    selected = np.flatnonzero(scores_1d <= threshold)
    # Deterministic order: score asc, then index asc.
    order = np.lexsort((selected, scores_1d[selected]))
    return selected[order].astype(np.int64, copy=False)


def select_topk(scores: np.ndarray, k: int, policy: Policy = "strict") -> np.ndarray:
    """Select top-k indices under the named policy."""
    if policy == "strict":
        return topk_indices_strict(scores, k)
    if policy == "inclusive":
        return topk_indices_inclusive(scores, k)
    raise ValueError(f"unknown policy: {policy!r}")


def topk_selection_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    k: int,
    *,
    policy: Policy = "strict",
) -> dict[str, float]:
    """Compute recall and regret metrics for one k and one policy."""
    truth = _as_1d(y_true, "y_true")
    pred = _as_1d(y_pred, "y_pred")
    if truth.shape != pred.shape:
        raise ValueError("y_true and y_pred must have the same shape")
    k_eff = _validate_k(k, truth.size)

    real_idx = select_topk(truth, k_eff, policy=policy)
    pred_idx = select_topk(pred, k_eff, policy=policy)
    real_set = set(real_idx.tolist())
    pred_set = set(pred_idx.tolist())
    if not real_set:
        raise ValueError("real top-k set is empty")

    selected_makespans = truth[pred_idx]
    best_true = float(np.min(truth))
    best_selected = float(np.min(selected_makespans))
    mean_selected = float(np.mean(selected_makespans))

    return {
        "k_requested": float(k),
        "k_effective": float(k_eff),
        "policy_strict": 1.0 if policy == "strict" else 0.0,
        "real_set_size": float(len(real_set)),
        "predicted_set_size": float(len(pred_set)),
        "recall": float(len(real_set & pred_set) / len(real_set)),
        "best_selected_regret": best_selected - best_true,
        "mean_selected_regret": mean_selected - best_true,
        "mean_selected_makespan": mean_selected,
    }


def random_topk_baseline(
    y_true: np.ndarray,
    k: int,
    *,
    n_repetitions: int = 200,
    seed: int = 20261127,
    policy: Policy = "strict",
) -> dict[str, float]:
    """Estimate recall/regret of random selection with a fixed seed.

    For ``strict``, each trial draws exactly ``k`` distinct indices.
    For ``inclusive``, the real inclusive set size is used as the draw size so
    the random set matches the variable denominator used by recall.
    """
    truth = _as_1d(y_true, "y_true")
    k_eff = _validate_k(k, truth.size)
    if n_repetitions < 1:
        raise ValueError("n_repetitions must be >= 1")

    real_idx = select_topk(truth, k_eff, policy=policy)
    real_set = set(real_idx.tolist())
    draw_size = len(real_set) if policy == "inclusive" else k_eff
    best_true = float(np.min(truth))
    rng = np.random.default_rng(seed)

    recalls = np.empty(n_repetitions, dtype=float)
    best_regrets = np.empty(n_repetitions, dtype=float)
    mean_regrets = np.empty(n_repetitions, dtype=float)
    for i in range(n_repetitions):
        chosen = rng.choice(truth.size, size=draw_size, replace=False)
        chosen_set = set(chosen.tolist())
        selected = truth[chosen]
        recalls[i] = len(real_set & chosen_set) / len(real_set)
        best_regrets[i] = float(np.min(selected) - best_true)
        mean_regrets[i] = float(np.mean(selected) - best_true)

    return {
        "k_requested": float(k),
        "policy_strict": 1.0 if policy == "strict" else 0.0,
        "n_repetitions": float(n_repetitions),
        "seed": float(seed),
        "draw_size": float(draw_size),
        "recall_mean": float(np.mean(recalls)),
        "recall_std": float(np.std(recalls, ddof=1)) if n_repetitions > 1 else 0.0,
        "best_selected_regret_mean": float(np.mean(best_regrets)),
        "mean_selected_regret_mean": float(np.mean(mean_regrets)),
    }


def evaluate_topk_suite(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    ks: Iterable[int] = (3, 10, 50),
    *,
    policies: Iterable[Policy] = ("strict", "inclusive"),
) -> dict[str, float]:
    """Flattened metric dict with explicit policy and regret names."""
    out: dict[str, float] = {}
    for policy in policies:
        for k in ks:
            metrics = topk_selection_metrics(y_true, y_pred, int(k), policy=policy)
            prefix = f"top{int(k)}_{policy}"
            out[f"{prefix}_recall"] = metrics["recall"]
            out[f"{prefix}_best_selected_regret"] = metrics["best_selected_regret"]
            out[f"{prefix}_mean_selected_regret"] = metrics["mean_selected_regret"]
            out[f"{prefix}_mean_selected_makespan"] = metrics["mean_selected_makespan"]
            out[f"{prefix}_real_set_size"] = metrics["real_set_size"]
            out[f"{prefix}_predicted_set_size"] = metrics["predicted_set_size"]
    return out
