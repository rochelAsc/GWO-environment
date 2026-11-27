import numpy as np

from scripts.gwo_pfs import gwo_pfs
from scripts.gwo_pfs_fuzzy import gwo_pfs_fuzzy
from scripts.gwo_pfs_surrogate import gwo_pfs_surrogate


PROCESSING = np.asarray([
    [3, 7, 2], [8, 1, 5], [4, 6, 3], [2, 9, 4], [7, 3, 6],
], dtype=np.int64)


class ConstantModel:
    def predict(self, features):
        return np.zeros(len(features), dtype=float)


def _assert_same_result(left, right, fitness_field):
    assert left.best_fitness == right.best_fitness
    assert np.array_equal(left.best_permutation, right.best_permutation)
    assert np.array_equal(left.convergence, right.convergence)
    assert getattr(left, fitness_field) == getattr(right, fitness_field)


def _observer_that_mutates(calls):
    def observe(generation, positions):
        calls.append((generation, positions.shape))
        positions[:] = 0.0
    return observe


def test_baseline_observer_does_not_change_search_and_receives_all_populations():
    expected = gwo_pfs(PROCESSING, n_wolves=5, iterations=3, seed=19)
    calls = []
    observed = gwo_pfs(
        PROCESSING, n_wolves=5, iterations=3, seed=19,
        population_observer=_observer_that_mutates(calls),
    )
    _assert_same_result(expected, observed, "evaluations")
    assert calls == [(-1, (5, 5)), (0, (5, 5)), (1, (5, 5)), (2, (5, 5))]


def test_fuzzy_observer_does_not_change_search_and_receives_all_populations():
    expected = gwo_pfs_fuzzy(PROCESSING, n_wolves=5, iterations=3, seed=23)
    calls = []
    observed = gwo_pfs_fuzzy(
        PROCESSING, n_wolves=5, iterations=3, seed=23,
        population_observer=_observer_that_mutates(calls),
    )
    _assert_same_result(expected, observed, "evaluations")
    assert calls == [(-1, (5, 5)), (0, (5, 5)), (1, (5, 5)), (2, (5, 5))]


def test_surrogate_observer_does_not_change_search_and_receives_all_populations():
    model = ConstantModel()
    expected = gwo_pfs_surrogate(
        PROCESSING, model, n_wolves=5, iterations=3, seed=29, top_k=2,
    )
    calls = []
    observed = gwo_pfs_surrogate(
        PROCESSING, model, n_wolves=5, iterations=3, seed=29, top_k=2,
        population_observer=_observer_that_mutates(calls),
    )
    _assert_same_result(expected, observed, "exact_evaluations")
    assert observed.surrogate_predictions == expected.surrogate_predictions
    assert calls == [(-1, (5, 5)), (0, (5, 5)), (1, (5, 5)), (2, (5, 5))]
