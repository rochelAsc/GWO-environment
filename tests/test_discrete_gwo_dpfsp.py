import pytest

from scripts.discrete_gwo_dpfsp import (
    RandomKeyDecoder,
    RandomKeyGWO,
    canonical_solution_key,
)
from scripts.dpfsp_dd import DPFSPInstance


def _instance(factories=2):
    return DPFSPInstance(
        processing_times=((2, 3), (1, 4), (3, 2), (2, 1)),
        due_dates=(4, 8, 5, 7),
        factories=factories,
    )


def test_decoder_assigns_every_job_once_and_orders_by_priority():
    instance = _instance()
    decoder = RandomKeyDecoder(instance)
    # Assignment keys: jobs 0,2 -> factory 0; jobs 1,3 -> factory 1.
    # Priority keys create order [2,0] and [3,1].
    position = [0.1, 0.8, 0.2, 0.9, 0.8, 0.2, 0.1, 0.7]
    solution = decoder.decode(position)
    assert solution == ((2, 0), (1, 3))
    assert sorted(job for sequence in solution for job in sequence) == [0, 1, 2, 3]


def test_decoder_handles_zero_and_one_boundaries():
    decoder = RandomKeyDecoder(_instance())
    solution = decoder.decode([0.0, 1.0, 0.0, 1.0, 0.4, 0.3, 0.2, 0.1])
    assert solution == ((2, 0), (3, 1))


def test_decoder_clips_finite_values_outside_bounds():
    decoder = RandomKeyDecoder(_instance())
    solution = decoder.decode([-5, 5, -2, 2, 0.1, 0.2, 0.3, 0.4])
    assert solution == ((0, 2), (1, 3))


def test_decoder_preserves_job_id_order_on_priority_ties():
    decoder = RandomKeyDecoder(_instance())
    solution = decoder.decode([0.1] * 4 + [0.5] * 4)
    assert solution == ((0, 1, 2, 3), ())


@pytest.mark.parametrize("position", [
    [0.1, 0.2],
    [[0.1] * 8],
    [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, float("nan")],
    [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, float("inf")],
])
def test_decoder_rejects_invalid_vectors(position):
    with pytest.raises(ValueError):
        RandomKeyDecoder(_instance()).decode(position)


def test_one_factory_decoder_produces_one_complete_sequence():
    decoder = RandomKeyDecoder(_instance(factories=1))
    solution = decoder.decode([0.2, 0.4, 0.6, 0.8, 0.4, 0.3, 0.2, 0.1])
    assert solution == ((3, 2, 1, 0),)


def test_factory_label_canonicalization():
    assert canonical_solution_key(((2, 0), (1, 3), ())) == ((), (1, 3), (2, 0))


def test_gwo_respects_exact_population_batch_budget():
    result = RandomKeyGWO(
        _instance(), n_wolves=4, max_evaluations=12, seed=7
    ).optimize()
    assert result.evaluations == 12
    assert result.generations == 2
    assert len(result.history) == 3
    assert result.unique_decoded_solutions >= 1
    assert 0.0 <= result.coordinate_saturation_fraction <= 1.0


def test_gwo_does_not_run_partial_final_generation():
    result = RandomKeyGWO(
        _instance(), n_wolves=4, max_evaluations=11, seed=7
    ).optimize()
    assert result.evaluations == 8
    assert result.generations == 1


def test_gwo_is_reproducible_for_same_seed():
    first = RandomKeyGWO(
        _instance(), n_wolves=5, max_evaluations=15, seed=123
    ).optimize()
    second = RandomKeyGWO(
        _instance(), n_wolves=5, max_evaluations=15, seed=123
    ).optimize()
    assert first == second


def test_gwo_best_so_far_history_is_nonincreasing():
    result = RandomKeyGWO(
        _instance(), n_wolves=6, max_evaluations=30, seed=19,
        a_decay="quadratic",
    ).optimize()
    assert all(
        later <= earlier
        for earlier, later in zip(result.history, result.history[1:])
    )


def test_gwo_result_is_valid_for_independent_evaluator():
    instance = _instance()
    result = RandomKeyGWO(
        instance, n_wolves=5, max_evaluations=10, seed=5
    ).optimize()
    from scripts.dpfsp_dd import DPFSPEvaluator

    evaluated = DPFSPEvaluator(instance).evaluate(result.best_solution)
    assert evaluated.total_tardiness == result.best_fitness


def test_gwo_validates_configuration():
    with pytest.raises(ValueError, match=">= 3"):
        RandomKeyGWO(_instance(), n_wolves=2)
    with pytest.raises(ValueError, match="initial population"):
        RandomKeyGWO(_instance(), n_wolves=5, max_evaluations=4)
    with pytest.raises(ValueError, match="a_decay"):
        RandomKeyGWO(_instance(), a_decay="exponential")
