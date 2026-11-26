import numpy as np
import pytest

from experiments.meta_learning.scripts.extract_instance_features import (
    extract_instance_features,
)


def test_feature_extraction_is_deterministic_and_uses_expected_dimensions():
    p = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.int64)
    first = extract_instance_features(p)
    second = extract_instance_features(p.copy())
    assert first == second
    assert first["n_jobs"] == 3
    assert first["n_machines"] == 3
    assert first["jobs_per_machine"] == 1.0
    assert first["processing_mean"] == 5.0
    assert first["job_load_mean"] == 15.0
    assert first["machine_load_mean"] == 15.0


def test_features_do_not_depend_on_filename_or_benchmark_metadata():
    p = np.array([[2, 7], [4, 3], [6, 5]], dtype=np.int64)
    assert extract_instance_features(p) == extract_instance_features(p.copy())


@pytest.mark.parametrize(
    "matrix",
    [
        np.array([]),
        np.array([1, 2, 3]),
        np.array([[1, 0], [2, 3]], dtype=np.int64),
        np.array([[1.0, 2.0], [3.0, 4.0]]),
    ],
)
def test_invalid_processing_matrices_are_rejected(matrix):
    with pytest.raises(ValueError):
        extract_instance_features(matrix)


def test_single_machine_instance_has_defined_adjacent_correlations():
    features = extract_instance_features(np.array([[2], [3], [4]], dtype=np.int64))
    assert features["adjacent_machine_corr_mean"] == 0.0
    assert features["adjacent_machine_corr_std"] == 0.0
