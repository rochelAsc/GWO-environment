import numpy as np
import pytest

from scripts.legacy_pfs import FlowShopEngine, load_legacy_pfs_instance, parse_legacy_pfs_text


def _engine():
    return FlowShopEngine(
        n_jobs=2,
        n_machines=2,
        proc_times=((2, 3), (4, 1)),
        due_dates=(4, 10),
    )


def _reference_total_tardiness(processing, due_dates, permutation):
    machines = len(processing[0])
    available = [0] * machines
    completion = [0] * len(processing)
    for job in permutation:
        previous = 0
        for machine in range(machines):
            finish = max(previous, available[machine]) + processing[job][machine]
            available[machine] = finish
            previous = finish
        completion[job] = previous
    return sum(max(0, completion[job] - due_dates[job])
               for job in range(len(processing)))


def test_parser_reads_legacy_layout_and_reorders_machine_pairs():
    raw = """2 2
metadata retained as opaque line
1 3 0 2
0 4 1 1
Duedate
4
10
"""
    jobs, machines, processing, due_dates = parse_legacy_pfs_text(raw)
    assert (jobs, machines) == (2, 2)
    assert processing.tolist() == [[2, 3], [4, 1]]
    assert due_dates.tolist() == [4, 10]


def test_parser_rejects_missing_file_without_synthetic_fallback(tmp_path):
    missing = tmp_path / "does-not-exist.txt"
    with pytest.raises(FileNotFoundError, match="PFS instance not found"):
        load_legacy_pfs_instance(missing)


@pytest.mark.parametrize(
    "raw, message",
    [
        ("2 2\nmeta\n0 2 0 3\n0 4 1 1\nDuedate\n4\n10\n", "duplicate machine id"),
        ("2 2\nmeta\n0 2 1\n0 4 1 1\nDuedate\n4\n10\n", "expected 4 integers"),
        ("2 2\nmeta\n0 2 1 3\n0 4 1 1\n4\n10\n", "Duedate marker"),
        ("2 2\nmeta\n0 2 1 3\n0 4 1 1\nDuedate\n4\n", "expected 2 due-date rows"),
        ("1 1\nmeta\n0 0\nDuedate\n4\n", "processing times must be positive"),
        ("1 1\nmeta\n0 2\nDuedate\n-1\n", "non-negative due date"),
    ],
)
def test_parser_rejects_malformed_instances(raw, message):
    with pytest.raises(ValueError, match=message):
        parse_legacy_pfs_text(raw, source="fixture.txt")


def test_loader_and_static_methods_work_from_class_and_instance(tmp_path):
    path = tmp_path / "instance.txt"
    path.write_text(
        "2 2\nmeta\n0 2 1 3\n0 4 1 1\nDuedate\n4\n10\n",
        encoding="utf-8",
    )
    via_class = FlowShopEngine.carregar_instancia_txt(path)
    via_instance = _engine().carregar_instancia_txt(path)
    assert via_class[0:2] == (2, 2)
    assert np.array_equal(via_class[2], via_instance[2])
    assert np.array_equal(via_class[3], via_instance[3])


def test_pfs_evaluator_matches_independent_schedule_recurrence():
    engine = _engine()
    for permutation in ([0, 1], [1, 0]):
        keys = np.empty(2)
        keys[list(permutation)] = [0.1, 0.9]
        observed = engine.evaluate(keys, objective="Tardiness")
        expected = _reference_total_tardiness(
            ((2, 3), (4, 1)), (4, 10), permutation
        )
        assert observed == expected


def test_makespan_and_tardiness_for_known_schedule():
    engine = _engine()
    keys = [0.1, 0.9]  # sequence [0, 1]
    assert engine.evaluate(keys, objective="Makespan") == 7
    assert engine.evaluate(keys, objective="Tardiness") == 1
    assert engine.cfo_count == 2


def test_non_pfs_mode_uses_one_sequence_per_machine():
    engine = _engine()
    # Machine 0: [0, 1]; machine 1: [1, 0].
    keys = [0.1, 0.9, 0.9, 0.1]
    assert engine.evaluate(keys, mode="per_machine", objective="Makespan") == 10


def test_evaluate_with_permutation_validates_complete_job_set():
    engine = _engine()
    assert engine.evaluate_with_permutation([0, 1]) == 1
    for invalid in ([0], [0, 0], [0, 2], [0, 1.5]):
        with pytest.raises(ValueError, match="permutation"):
            engine.evaluate_with_permutation(invalid)


@pytest.mark.parametrize(
    "processing, due_dates",
    [
        (((1,), ()), (0, 0)),
        (((1,), (2,)), (0,)),
        (((0,), (2,)), (0, 0)),
        (((1.5,), (2,)), (0, 0)),
        (((1,), (2,)), (-1, 0)),
    ],
)
def test_constructor_rejects_invalid_instance_arrays(processing, due_dates):
    with pytest.raises(ValueError):
        FlowShopEngine(len(processing), len(processing[0]), processing, due_dates)


def test_potts_lower_bound_is_callable_from_class_and_instance():
    args = (2, 1, np.array([[3], [2]]), np.array([2, 10]))
    assert FlowShopEngine.calcular_lower_bound_potts(*args) == 1.0
    assert _engine().calcular_lower_bound_potts(*args) == 1.0


def test_invalid_objective_is_rejected():
    with pytest.raises(ValueError, match="objective"):
        _engine().evaluate([0.1, 0.9], objective="unknown")
