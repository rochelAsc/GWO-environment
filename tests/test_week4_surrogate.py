import numpy as np
import pytest

from scripts.run_week4_surrogate import (
    generate_dataset,
    permutation_features,
    regression_metrics,
)


def test_permutation_features_encode_job_positions():
    # Processing order is job 2, then 0, then 1.
    features = permutation_features(np.array([2, 0, 1]))
    np.testing.assert_allclose(features, [0.5, 1.0, 0.0])


@pytest.mark.parametrize("permutation", [
    np.array([], dtype=int),
    np.array([0, 0, 1]),
    np.array([0, 1, 3]),
])
def test_permutation_features_reject_invalid_orders(permutation):
    with pytest.raises(ValueError):
        permutation_features(permutation)


def test_lhs_dataset_is_reproducible_and_uses_unique_permutations():
    processing_times = np.array([
        [2, 3, 1],
        [4, 1, 2],
        [3, 2, 4],
        [1, 4, 3],
    ], dtype=np.int64)
    x1, y1, unique1 = generate_dataset(processing_times, 80, seed=17)
    x2, y2, unique2 = generate_dataset(processing_times, 80, seed=17)

    np.testing.assert_array_equal(x1, x2)
    np.testing.assert_array_equal(y1, y2)
    assert unique1 == unique2 == len(y1)
    assert len({tuple(row) for row in x1}) == len(x1)
    assert np.all((x1 >= 0.0) & (x1 <= 1.0))


def test_regression_metrics_report_expected_errors():
    metrics = regression_metrics(
        np.array([10.0, 20.0, 30.0]),
        np.array([11.0, 18.0, 31.0]),
    )
    assert metrics["mse"] == pytest.approx(2.0)
    assert metrics["rmse"] == pytest.approx(np.sqrt(2.0))
    assert metrics["mae"] == pytest.approx(4.0 / 3.0)
    assert metrics["spearman_rho"] == pytest.approx(1.0)
