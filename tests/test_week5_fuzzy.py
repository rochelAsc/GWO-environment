import numpy as np
import pytest

from scripts.fuzzy_controller import MamdaniGWOController, population_diversity
from scripts.gwo_pfs_fuzzy import gwo_pfs_fuzzy
from scripts.pfs_taillard import load_taillard_instance


def test_controller_output_is_bounded_and_deterministic():
    controller = MamdaniGWOController()
    for diversity in (0.0, 0.25, 0.5, 0.75, 1.0):
        for stagnation in (0.0, 0.25, 0.5, 0.75, 1.0):
            value = controller(diversity, stagnation)
            assert 0.5 <= value <= 1.5
            assert value == controller(diversity, stagnation)


@pytest.mark.parametrize("args", [(-0.1, 0.5), (1.1, 0.5), (0.5, float("nan"))])
def test_controller_rejects_invalid_inputs(args):
    with pytest.raises(ValueError):
        MamdaniGWOController()(*args)


def test_diversity_known_values_and_validation():
    positions = np.array([[0.0, 0.0], [1.0, 1.0]])
    assert population_diversity(positions) == pytest.approx(1.0)
    assert population_diversity(np.zeros((3, 2))) == 0.0
    with pytest.raises(ValueError):
        population_diversity(np.array([[0.0, 2.0], [1.0, 0.0]]))


def test_fuzzy_gwo_respects_budget_and_is_reproducible():
    p = load_taillard_instance("data/benchmarks/taillard/ta001.txt").processing_times
    kwargs = dict(n_wolves=6, iterations=5, seed=123, stagnation_window=3)
    first = gwo_pfs_fuzzy(p, **kwargs)
    second = gwo_pfs_fuzzy(p, **kwargs)
    assert first.evaluations == 6 * 6
    assert first.best_fitness == second.best_fitness
    assert np.array_equal(first.convergence, second.convergence)
    assert first.trace == second.trace
    assert np.all(np.diff(first.convergence) <= 0)
    diversity_values = [row["diversity"] for row in first.trace]
    assert all(0.0 <= value <= 1.0 for value in diversity_values)
    assert np.ptp(diversity_values) > 1e-9, "Fuzzy diversity must be recomputed from the evolving population"
    assert all(0.5 <= row["fuzzy_scale"] <= 1.5 for row in first.trace)
    assert all(0.0 <= row["a"] <= 2.0 for row in first.trace)


def test_fuzzy_gwo_rejects_invalid_budget_parameters():
    p = np.ones((4, 2), dtype=np.int64)
    with pytest.raises(ValueError):
        gwo_pfs_fuzzy(p, n_wolves=2)
    with pytest.raises(ValueError):
        gwo_pfs_fuzzy(p, stagnation_window=0)
