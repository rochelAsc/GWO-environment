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


def test_extractor_is_invariant_to_path_and_filename(tmp_path):
    from pathlib import Path
    import shutil

    from experiments.meta_learning.scripts.extract_instance_features import (
        FEATURE_VERSION,
        extract_directory,
        extract_instance_features,
    )
    from scripts.pfs_taillard import load_taillard_instance

    src = Path("data/benchmarks/taillard/ta001.txt")
    a = tmp_path / "alpha"
    b = tmp_path / "beta" / "nested"
    a.mkdir()
    b.mkdir(parents=True)
    shutil.copy(src, a / "ta001.txt")
    shutil.copy(src, b / "ta001.txt")
    feats = extract_instance_features(load_taillard_instance(src).processing_times)
    assert extract_instance_features(load_taillard_instance(a / "ta001.txt").processing_times) == feats
    assert extract_instance_features(load_taillard_instance(b / "ta001.txt").processing_times) == feats
    frame = extract_directory(a)
    assert frame.loc[0, "feature_version"] == FEATURE_VERSION
    assert frame.loc[0, "instance"] == "ta001"
    assert frame.loc[0, "sha256"] == frame.loc[0, "sha256"]


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


def test_stratified_taillard_pilot_instances_parse_and_have_finite_features():
    from pathlib import Path
    from scripts.pfs_taillard import load_taillard_instance

    expected = {
        "ta001": (20, 5), "ta011": (20, 10), "ta021": (20, 20),
        "ta031": (50, 5), "ta041": (50, 10), "ta051": (50, 20),
        "ta061": (100, 5), "ta071": (100, 10), "ta081": (100, 20),
        "ta091": (200, 10), "ta101": (200, 20), "ta111": (500, 20),
    }
    root = Path("data/benchmarks/taillard")
    for name, dimensions in expected.items():
        instance = load_taillard_instance(root / f"{name}.txt")
        assert (instance.n_jobs, instance.n_machines) == dimensions
        features = extract_instance_features(instance.processing_times)
        assert all(np.isfinite(value) for value in features.values())
