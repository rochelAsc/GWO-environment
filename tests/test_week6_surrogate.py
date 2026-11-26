from __future__ import annotations

import numpy as np
import pytest

from scripts.gwo_pfs_surrogate import gwo_pfs_surrogate


class RankingModel:
    def __init__(self, reverse: bool = False):
        self.calls = 0
        self.reverse = reverse

    def predict(self, features):
        self.calls += 1
        scores = np.arange(len(features), dtype=float)
        return scores[::-1] if self.reverse else scores


def sample_processing_times():
    return np.asarray([
        [2, 3, 1],
        [4, 1, 2],
        [3, 2, 4],
        [1, 4, 3],
    ], dtype=np.int64)


def test_surrogate_budget_and_trace_are_exactly_counted():
    model = RankingModel()
    result = gwo_pfs_surrogate(
        sample_processing_times(), model, n_wolves=6, iterations=4, seed=7, top_k=2
    )
    assert result.exact_evaluations == 6 + 2 * 4
    assert result.surrogate_predictions == 6 * 4
    assert result.inference_batches == 4
    assert model.calls == 4
    assert len(result.trace) == 2 * 4
    assert result.convergence.shape == (5,)
    assert np.all(np.diff(result.convergence) <= 0)


def test_surrogate_result_is_deterministic_for_fixed_seed():
    p = sample_processing_times()
    first = gwo_pfs_surrogate(p, RankingModel(), n_wolves=6, iterations=4, seed=19)
    second = gwo_pfs_surrogate(p, RankingModel(), n_wolves=6, iterations=4, seed=19)
    assert first.best_fitness == second.best_fitness
    np.testing.assert_array_equal(first.best_permutation, second.best_permutation)
    np.testing.assert_array_equal(first.convergence, second.convergence)
    np.testing.assert_array_equal(first.final_population, second.final_population)


def test_top_k_selection_uses_lowest_predictions_stably():
    result = gwo_pfs_surrogate(
        sample_processing_times(), RankingModel(reverse=True),
        n_wolves=6, iterations=1, seed=3, top_k=2,
    )
    assert {row["candidate_index"] for row in result.trace} == {4, 5}
    assert [row["predicted_rank"] for row in result.trace] == [1, 2]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_wolves": 2},
        {"iterations": 0},
        {"top_k": 0},
        {"top_k": 7, "n_wolves": 6},
        {"a_exponent": 0},
    ],
)
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        gwo_pfs_surrogate(sample_processing_times(), RankingModel(), **kwargs)


def test_non_finite_predictions_are_rejected():
    class InvalidModel:
        def predict(self, features):
            return np.full(len(features), np.nan)

    with pytest.raises(ValueError, match="finite"):
        gwo_pfs_surrogate(
            sample_processing_times(), InvalidModel(),
            n_wolves=6, iterations=1,
        )
