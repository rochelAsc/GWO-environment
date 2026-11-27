from __future__ import annotations

import numpy as np
import pytest

from experiments.meta_learning.scripts.run_surrogate_model_comparison_pilot import (
    _features_batch,
    _make_estimators,
    _unique_rows,
)


def test_features_batch_matches_week4_permutation_encoder() -> None:
    permutations = np.asarray([[2, 0, 1], [1, 2, 0]], dtype=np.int32)
    expected = np.vstack([
        np.asarray([1.0, 2.0, 0.0]) / 2,
        np.asarray([2.0, 0.0, 1.0]) / 2,
    ])
    np.testing.assert_allclose(_features_batch(permutations), expected)


def test_features_batch_rejects_non_matrix() -> None:
    with pytest.raises(ValueError, match="2D"):
        _features_batch(np.asarray([0, 1, 2]))


def test_unique_rows_detects_duplicates() -> None:
    assert _unique_rows(np.asarray([[0, 1, 2], [2, 1, 0]], dtype=np.int32))
    assert not _unique_rows(np.asarray([[0, 1, 2], [0, 1, 2]], dtype=np.int32))


def test_estimator_factory_has_expected_models_and_single_thread() -> None:
    estimators = _make_estimators(123)
    assert set(estimators) == {
        "mlp_64x64", "random_forest", "extra_trees", "hist_gradient_boosting"
    }
    assert estimators["random_forest"].n_estimators == 300
    assert estimators["random_forest"].n_jobs == 1
    assert estimators["extra_trees"].n_estimators == 300
    assert estimators["extra_trees"].n_jobs == 1
    assert estimators["hist_gradient_boosting"].max_iter == 300
