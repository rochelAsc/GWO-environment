import numpy as np
import pytest
from scipy.stats import qmc

from experiments.meta_learning.scripts.run_surrogate_learning_curve_v2 import (
    diagnose_permutation_distribution,
    generate_lhs_dataset,
    generate_lhs_permutations,
    generate_uniform_permutations,
)


def test_lhs_design_is_global_and_each_dimension_occupies_each_stratum_once():
    count, n_jobs, seed = 40, 8, 456
    permutations, attempts = generate_lhs_permutations(n_jobs, count, seed)
    assert attempts >= 1
    assert permutations.shape == (count, n_jobs)
    assert len({tuple(row) for row in permutations}) == count
    accepted = None
    for attempt in range(100):
        rng = np.random.default_rng(np.random.SeedSequence([seed, attempt]))
        keys = qmc.LatinHypercube(d=n_jobs, seed=rng).random(n=count)
        decoded = np.argsort(keys, axis=1, kind="stable")
        if len({tuple(row.tolist()) for row in decoded}) == count:
            accepted = keys
            assert attempts == attempt + 1
            break
    assert accepted is not None
    for dimension in range(n_jobs):
        strata = np.floor(accepted[:, dimension] * count).astype(int)
        assert np.array_equal(np.sort(strata), np.arange(count))


def test_lhs_dataset_returns_exact_labels_and_unique_permutations():
    processing_times = np.array([
        [2, 3, 4, 5, 2, 4, 3, 5],
        [3, 2, 5, 4, 3, 5, 2, 4],
        [4, 5, 2, 3, 5, 2, 4, 3],
        [2, 4, 3, 5, 4, 3, 5, 2],
    ])
    X, y, permutations, attempts = generate_lhs_dataset(
        processing_times, 20, 789, max_attempts=100
    )
    assert X.shape == (20, 8)
    assert y.shape == (20,)
    assert permutations.shape == (20, 8)
    assert len({tuple(row) for row in permutations}) == 20
    assert attempts >= 1


def test_lhs_rejects_impossible_sample_count():
    with pytest.raises(ValueError, match="only"):
        generate_lhs_permutations(3, 7, 1)


def test_distribution_diagnostics_are_reproducible_and_complete():
    processing_times = np.ones((8, 3), dtype=int)
    _, _, permutations = generate_uniform_permutations(processing_times, 30, 123)
    first, positions_a, precedence_a = diagnose_permutation_distribution(permutations, 99)
    second, positions_b, precedence_b = diagnose_permutation_distribution(permutations, 99)
    assert first == second
    assert np.array_equal(positions_a, positions_b)
    assert np.allclose(precedence_a, precedence_b)
    assert first["unique_permutations"] == 30
    assert first["duplicate_permutations"] == 0
    assert first["pairwise_diagnostic_sample_count"] == 30
    assert positions_a.shape == (8, 8)
    assert precedence_a.shape == (8, 8)
    assert len(first["permutation_sha256"]) == 64
