import numpy as np
import pytest
from scripts.gwo_pfs import gwo_pfs
from scripts.pfs_taillard import load_taillard_instance

def test_default_schedule_matches_explicit_week2_schedule():
    p = load_taillard_instance("data/benchmarks/taillard/ta001.txt").processing_times
    a = gwo_pfs(p, n_wolves=9, iterations=4, seed=7)
    b = gwo_pfs(p, n_wolves=9, iterations=4, seed=7, a_start=2.0, a_end=0.0, a_exponent=1.0)
    assert a.best_fitness == b.best_fitness
    assert np.array_equal(a.convergence, b.convergence)

@pytest.mark.parametrize("wolves", [9, 10, 15, 18, 30, 45])
def test_candidate_populations_preserve_exact_budget(wolves):
    budget = 15030
    iterations = budget // wolves - 1
    assert wolves * (iterations + 1) == budget

def test_custom_schedule_is_reproducible():
    p = load_taillard_instance("data/benchmarks/taillard/ta001.txt").processing_times
    kwargs = dict(n_wolves=10, iterations=8, seed=42, a_start=2.2, a_end=0.2, a_exponent=1.4)
    a, b = gwo_pfs(p, **kwargs), gwo_pfs(p, **kwargs)
    assert a.best_fitness == b.best_fitness
    assert np.array_equal(a.convergence, b.convergence)

@pytest.mark.parametrize("params", [
    {"a_start": 1.0, "a_end": 1.0, "a_exponent": 1.0},
    {"a_start": 1.0, "a_end": 1.1, "a_exponent": 1.0},
    {"a_start": 2.0, "a_end": -0.1, "a_exponent": 1.0},
    {"a_start": 2.0, "a_end": 0.0, "a_exponent": 0.0},
])
def test_invalid_schedule_parameters_are_rejected(params):
    with pytest.raises(ValueError):
        gwo_pfs(np.ones((3, 2), dtype=np.int64), n_wolves=3, iterations=2, **params)
