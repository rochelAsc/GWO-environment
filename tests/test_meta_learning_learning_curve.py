import numpy as np
import pytest

from experiments.meta_learning.scripts.run_surrogate_learning_curve import (
    evaluate_predictions,
    generate_lhs_dataset,
    generate_uniform_permutations,
    geometric_sample_sizes,
)


def test_geometric_sample_sizes_match_log_spaced_protocol():
    assert geometric_sample_sizes(300, 4000, 5) == [300, 573, 1095, 2093, 4000]


@pytest.mark.parametrize(
    "minimum,maximum,points",
    [(1, 100, 1), (100, 10, 5), (100, 100, 5)],
)
def test_geometric_sample_sizes_reject_invalid_ranges(minimum, maximum, points):
    with pytest.raises(ValueError):
        geometric_sample_sizes(minimum, maximum, points)


def test_uniform_permutation_generator_is_unique_and_valid():
    processing_times = np.array([
        [2, 3, 4],
        [3, 2, 5],
        [4, 5, 2],
        [2, 4, 3],
    ])
    X, y, permutations = generate_uniform_permutations(processing_times, 20, 123)
    assert X.shape == (20, 4)
    assert y.shape == (20,)
    assert permutations.shape == (20, 4)
    assert len({tuple(row) for row in permutations}) == 20
    assert all(np.array_equal(np.sort(row), np.arange(4)) for row in permutations)


def test_lhs_generator_decodes_unique_valid_permutations():
    processing_times = np.array([
        [2, 3, 4],
        [3, 2, 5],
        [4, 5, 2],
        [2, 4, 3],
    ])
    X, y, permutations = generate_lhs_dataset(processing_times, 20, 456)
    assert X.shape == (20, 4)
    assert y.shape == (20,)
    assert permutations.shape == (20, 4)
    assert len({tuple(row) for row in permutations}) == 20
    assert all(np.array_equal(np.sort(row), np.arange(4)) for row in permutations)


def test_selection_metrics_are_perfect_for_exact_predictions():
    y = np.array([5, 1, 4, 2, 3, 6, 7, 8, 9, 10], dtype=float)
    metrics = evaluate_predictions(y, y.copy())
    assert metrics["rmse"] == 0
    assert metrics["mae"] == 0
    assert metrics["r2"] == 1
    assert metrics["spearman"] == pytest.approx(1)
    assert metrics["kendall_tau_b"] == pytest.approx(1)
    assert metrics["top3_recall"] == 1
    assert metrics["top3_regret"] == 0
