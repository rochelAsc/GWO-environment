import numpy as np

from experiments.meta_learning.scripts.recover_surrogate_learning_curve_v2 import (
    _features_batch,
    _uniform_permutations,
    _unique_rows,
)


def test_features_batch_matches_week4_single_permutation_encoder():
    permutations = np.array([
        [2, 0, 1, 3],
        [1, 3, 0, 2],
    ], dtype=np.int32)
    features = _features_batch(permutations)
    expected = np.array([
        [1.0 / 3.0, 2.0 / 3.0, 0.0, 1.0],
        [2.0 / 3.0, 0.0, 1.0, 1.0 / 3.0],
    ])
    np.testing.assert_allclose(features, expected)


def test_uniform_generation_is_deterministic_and_nested():
    first = _uniform_permutations(jobs=8, count=40, seed=1234)
    second = _uniform_permutations(jobs=8, count=40, seed=1234)
    np.testing.assert_array_equal(first, second)
    assert _unique_rows(first)
    assert first.shape == (40, 8)


def test_unique_rows_detects_duplicates_without_tuple_conversion():
    assert _unique_rows(np.array([[0, 1, 2], [1, 2, 0]], dtype=np.int32))
    assert not _unique_rows(np.array([[0, 1, 2], [0, 1, 2]], dtype=np.int32))
