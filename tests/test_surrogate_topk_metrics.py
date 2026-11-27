from __future__ import annotations

import numpy as np
import pytest

from experiments.meta_learning.scripts.surrogate_topk_metrics import (
    evaluate_topk_suite,
    random_topk_baseline,
    select_topk,
    topk_indices_inclusive,
    topk_indices_strict,
    topk_selection_metrics,
)


def test_strict_uses_index_as_secondary_key_on_ties() -> None:
    scores = np.asarray([5.0, 1.0, 1.0, 2.0], dtype=float)
    assert topk_indices_strict(scores, 2).tolist() == [1, 2]


def test_inclusive_expands_frontier_ties() -> None:
    scores = np.asarray([4.0, 1.0, 2.0, 2.0, 3.0], dtype=float)
    # Strict top-2: indices 1,2 (scores 1,2). Inclusive adds the other 2.
    assert topk_indices_strict(scores, 2).tolist() == [1, 2]
    assert topk_indices_inclusive(scores, 2).tolist() == [1, 2, 3]


def test_all_values_equal_strict_takes_first_k_indices() -> None:
    scores = np.asarray([7.0, 7.0, 7.0, 7.0], dtype=float)
    assert topk_indices_strict(scores, 2).tolist() == [0, 1]
    assert topk_indices_inclusive(scores, 2).tolist() == [0, 1, 2, 3]


def test_k_one_and_k_larger_than_n() -> None:
    scores = np.asarray([3.0, 1.0, 2.0], dtype=float)
    assert topk_indices_strict(scores, 1).tolist() == [1]
    assert topk_indices_strict(scores, 10).tolist() == [1, 2, 0]


def test_constant_prediction_is_deterministic() -> None:
    y_true = np.asarray([5.0, 1.0, 2.0, 4.0], dtype=float)
    y_pred = np.asarray([9.0, 9.0, 9.0, 9.0], dtype=float)
    metrics = topk_selection_metrics(y_true, y_pred, k=2, policy="strict")
    assert metrics["predicted_set_size"] == 2.0
    assert metrics["best_selected_regret"] == pytest.approx(0.0)
    assert metrics["mean_selected_regret"] == pytest.approx((5.0 + 1.0) / 2 - 1.0)


def test_inverse_ranking_has_zero_recall_when_no_overlap() -> None:
    y_true = np.asarray([1.0, 2.0, 3.0, 4.0, 5.0], dtype=float)
    y_pred = np.asarray([5.0, 4.0, 3.0, 2.0, 1.0], dtype=float)
    metrics = topk_selection_metrics(y_true, y_pred, k=2, policy="strict")
    assert metrics["recall"] == 0.0
    assert metrics["best_selected_regret"] == pytest.approx(3.0)


def test_optimal_selected_zero_best_regret() -> None:
    y_true = np.asarray([10.0, 1.0, 8.0, 7.0], dtype=float)
    y_pred = np.asarray([9.0, 0.0, 5.0, 4.0], dtype=float)
    metrics = topk_selection_metrics(y_true, y_pred, k=1, policy="strict")
    assert metrics["recall"] == 1.0
    assert metrics["best_selected_regret"] == 0.0


def test_no_optimal_selected() -> None:
    y_true = np.asarray([1.0, 5.0, 6.0], dtype=float)
    y_pred = np.asarray([9.0, 0.0, 1.0], dtype=float)
    metrics = topk_selection_metrics(y_true, y_pred, k=1, policy="strict")
    assert metrics["recall"] == 0.0
    assert metrics["best_selected_regret"] == pytest.approx(4.0)


def test_inclusive_recall_uses_expanded_denominator() -> None:
    y_true = np.asarray([1.0, 2.0, 2.0, 5.0], dtype=float)
    y_pred = np.asarray([0.0, 9.0, 8.0, 7.0], dtype=float)
    metrics = topk_selection_metrics(y_true, y_pred, k=2, policy="inclusive")
    # Real inclusive set = {0,1,2}; predicted strict-frontier for k=2 around
    # pred scores selects index 0 only at top, then expands? pred top2 strict
    # is [0,3] (0 and 7); threshold 7 includes all with pred<=7 -> {0,3}.
    assert metrics["real_set_size"] == 3.0
    assert metrics["predicted_set_size"] == 2.0
    assert metrics["recall"] == pytest.approx(1.0 / 3.0)


def test_row_permutation_invariance_with_stable_secondary_key() -> None:
    y_true = np.asarray([3.0, 1.0, 1.0, 4.0], dtype=float)
    y_pred = np.asarray([2.5, 0.5, 0.6, 3.0], dtype=float)
    base = topk_selection_metrics(y_true, y_pred, k=2, policy="strict")

    perm = np.asarray([3, 0, 2, 1], dtype=int)
    y_true_p = y_true[perm]
    y_pred_p = y_pred[perm]
    # Re-index selected sets via values, not raw indices.
    base_real = set(y_true[select_topk(y_true, 2)].tolist())
    perm_real = set(y_true_p[select_topk(y_true_p, 2)].tolist())
    assert base_real == perm_real
    perm_metrics = topk_selection_metrics(y_true_p, y_pred_p, k=2, policy="strict")
    assert perm_metrics["recall"] == base["recall"]
    assert perm_metrics["best_selected_regret"] == base["best_selected_regret"]
    assert perm_metrics["mean_selected_regret"] == base["mean_selected_regret"]


def test_evaluate_topk_suite_names_distinguish_regret_definitions() -> None:
    y_true = np.asarray([1.0, 2.0, 3.0, 4.0], dtype=float)
    y_pred = np.asarray([1.5, 2.5, 0.5, 4.5], dtype=float)
    suite = evaluate_topk_suite(y_true, y_pred, ks=(2,), policies=("strict",))
    assert "top2_strict_best_selected_regret" in suite
    assert "top2_strict_mean_selected_regret" in suite
    assert suite["top2_strict_best_selected_regret"] != suite["top2_strict_mean_selected_regret"]


def test_random_baseline_is_seed_deterministic() -> None:
    y_true = np.asarray([1.0, 2.0, 3.0, 4.0, 5.0], dtype=float)
    a = random_topk_baseline(y_true, k=2, n_repetitions=50, seed=11)
    b = random_topk_baseline(y_true, k=2, n_repetitions=50, seed=11)
    assert a == b
    c = random_topk_baseline(y_true, k=2, n_repetitions=50, seed=12)
    assert a["recall_mean"] != c["recall_mean"] or a["best_selected_regret_mean"] != c[
        "best_selected_regret_mean"
    ]


def test_rejects_mismatched_shapes_and_non_finite() -> None:
    with pytest.raises(ValueError, match="same shape"):
        topk_selection_metrics(np.asarray([1.0, 2.0]), np.asarray([1.0]), k=1)
    with pytest.raises(ValueError, match="finite"):
        topk_indices_strict(np.asarray([1.0, np.nan]), 1)
    with pytest.raises(ValueError, match="unknown policy"):
        select_topk(np.asarray([1.0, 2.0]), 1, policy="weird")  # type: ignore[arg-type]
