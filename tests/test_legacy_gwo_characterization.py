"""Characterization tests for the historical GWO embedded in the Colab export.

The export contains Colab magics and is not importable as a Python module. These
tests compile only the exact GWO class block from that export, without copying
or changing its implementation.
"""
from pathlib import Path

import numpy as np
import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LEGACY_EXPORT = REPOSITORY_ROOT / "scripts" / "sistemas_inteligentes_entregavel.py"


@pytest.fixture
def legacy_gwo_class():
    source = LEGACY_EXPORT.read_text(encoding="utf-8")
    start_marker = "class GWO:"
    end_marker = '\n"""## 3. Funções de Benchmark'
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    class_source = source[start:end]

    namespace = {"np": np}
    exec(compile(class_source, str(LEGACY_EXPORT), "exec"), namespace)
    return namespace["GWO"]


def test_evaluation_budget_includes_initial_population(legacy_gwo_class):
    gwo = legacy_gwo_class(
        obj_func=lambda x: float(np.sum(x**2)),
        dim=2,
        lb=0.0,
        ub=1.0,
        n_wolves=4,
        max_iter=3,
        seed=11,
    )

    _, _, history = gwo.optimize()

    assert gwo.n_evals == 4 * (3 + 1)
    assert len(history) == 3 + 1


@pytest.mark.parametrize(
    "strategy, expected",
    [
        ("linear", [2.0, 4.0 / 3.0, 2.0 / 3.0, 0.0]),
        ("exponential", [2.0, 16.0 / 9.0, 10.0 / 9.0, 0.0]),
        ("sqrt", [2.0, 2.0 * np.sqrt(2.0 / 3.0), 2.0 / np.sqrt(3.0), 0.0]),
    ],
)
def test_decay_formulas_and_effective_iteration_schedule(
    legacy_gwo_class, strategy, expected
):
    gwo = legacy_gwo_class(
        obj_func=lambda x: float(np.sum(x**2)),
        dim=1,
        lb=0.0,
        ub=1.0,
        n_wolves=3,
        max_iter=3,
        seed=0,
        a_decay=strategy,
    )

    observed = [gwo._compute_a(t) for t in range(4)]
    assert np.allclose(observed, expected)
    # optimize() executes t=0, 1, 2; t=3 is never used.
    assert gwo.max_iter - 1 == 2


def test_history_is_best_so_far_and_population_stays_bounded(legacy_gwo_class):
    gwo = legacy_gwo_class(
        obj_func=lambda x: float(np.sum(x**2)),
        dim=3,
        lb=0.0,
        ub=1.0,
        n_wolves=5,
        max_iter=7,
        seed=23,
    )

    best_position, best_score, history = gwo.optimize()

    assert len(history) == 8
    assert np.all(np.diff(history) <= 0)
    assert np.isclose(history[-1], best_score)
    assert np.all((best_position >= 0.0) & (best_position <= 1.0))


def test_seed_reproduces_result_and_evaluation_trace(legacy_gwo_class):
    def run():
        trace = []

        def objective(x):
            trace.append(np.array(x, copy=True))
            return float(np.sum(x**2))

        gwo = legacy_gwo_class(
            obj_func=objective,
            dim=2,
            lb=0.0,
            ub=1.0,
            n_wolves=4,
            max_iter=2,
            seed=19,
        )
        position, score, history = gwo.optimize()
        return trace, position, score, history

    first = run()
    second = run()

    assert len(first[0]) == 4 * (2 + 1)
    assert np.allclose(first[0], second[0])
    assert np.allclose(first[1], second[1])
    assert first[2] == second[2]
    assert np.allclose(first[3], second[3])


def test_first_generation_uses_sequential_in_place_leader_updates(
    legacy_gwo_class,
):
    evaluated = []

    def objective(x):
        evaluated.append(np.array(x, copy=True))
        return float(np.sum(x**2))

    gwo = legacy_gwo_class(
        obj_func=objective,
        dim=2,
        lb=0.0,
        ub=1.0,
        n_wolves=4,
        max_iter=1,
        seed=7,
    )
    gwo.optimize()

    # Entries 0..3 are the initial population. Entries 4..7 are the
    # immediately evaluated positions of wolves 0..3 in sequential order.
    expected_updated_population = np.array(
        [
            [0.6007997851331993, 0.23338549594899602],
            [1.0, 0.4354097072318277],
            [0.5548613695212169, 0.21497431386968857],
            [0.8287622194980152, 0.8829441794531888],
        ]
    )
    assert len(evaluated) == 8
    assert np.allclose(evaluated[4:], expected_updated_population, atol=1e-12)

    # Wolf 1's move uses wolf 0's newly promoted alpha; wolf 2 then uses
    # wolf 0's and wolf 1's current hierarchy. This golden trace would
    # change under frozen-leader/synchronous generation updates.
    assert np.allclose(
        evaluated[5], [1.0, 0.4354097072318277], atol=1e-12
    )
