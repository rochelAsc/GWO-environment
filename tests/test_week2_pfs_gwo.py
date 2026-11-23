import itertools

import numpy as np
import pytest

from scripts.gwo_pfs import decode_random_keys, gwo_pfs
from scripts.pfs_taillard import load_taillard_instance, makespan


def test_taillard_instances_have_expected_dimensions_and_metadata():
    small = load_taillard_instance("data/benchmarks/taillard/ta001.txt")
    medium = load_taillard_instance("data/benchmarks/taillard/ta011.txt")
    assert (small.n_jobs, small.n_machines) == (20, 5)
    assert (medium.n_jobs, medium.n_machines) == (20, 10)
    assert (small.published_seed, small.upper_bound, small.lower_bound) == (
        873654221, 1278, 1232
    )
    assert (medium.published_seed, medium.upper_bound, medium.lower_bound) == (
        587595453, 1582, 1448
    )


def test_decoder_is_a_permutation_and_stable_on_ties():
    assert decode_random_keys(np.array([0.4, 0.1, 0.3, 0.2])).tolist() == [1, 3, 2, 0]
    assert decode_random_keys(np.array([0.2, 0.2, 0.1])).tolist() == [2, 0, 1]


def test_makespan_matches_hand_calculated_two_job_two_machine_case():
    p = np.array([[2, 3], [4, 1]], dtype=np.int64)
    assert makespan(p, [0, 1]) == 7
    assert makespan(p, [1, 0]) == 9


def test_makespan_matches_exhaustive_reference_for_small_instance():
    p = np.array([[2, 3], [1, 4], [3, 2], [2, 1]], dtype=np.int64)
    for permutation in itertools.permutations(range(4)):
        completion = np.zeros(2, dtype=int)
        for job in permutation:
            completion[0] += p[job, 0]
            completion[1] = max(completion[0], completion[1]) + p[job, 1]
        assert makespan(p, permutation) == completion[-1]


@pytest.mark.parametrize("permutation", [[0, 0], [0], [0, 2], [-1, 0]])
def test_makespan_rejects_invalid_permutations(permutation):
    with pytest.raises(ValueError):
        makespan(np.array([[1, 2], [3, 4]]), permutation)


def test_gwo_is_reproducible_and_respects_evaluation_budget():
    p = load_taillard_instance("data/benchmarks/taillard/ta001.txt").processing_times
    first = gwo_pfs(p, n_wolves=6, iterations=8, seed=123)
    second = gwo_pfs(p, n_wolves=6, iterations=8, seed=123)
    assert first.best_fitness == second.best_fitness
    assert np.array_equal(first.best_permutation, second.best_permutation)
    assert np.array_equal(first.convergence, second.convergence)
    assert first.evaluations == 6 * 9
    assert first.population_diversity.shape == (9,)
    assert np.ptp(first.population_diversity) > 1e-9
    assert first.convergence.size == 9
    assert np.all(np.diff(first.convergence) <= 0)


def test_gwo_rejects_invalid_configuration():
    p = np.ones((3, 2), dtype=np.int64)
    with pytest.raises(ValueError):
        gwo_pfs(p, n_wolves=2, iterations=5)
    with pytest.raises(ValueError):
        gwo_pfs(p, n_wolves=3, iterations=0)
