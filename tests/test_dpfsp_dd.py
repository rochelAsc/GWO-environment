import pytest

from scripts.dpfsp_dd import DPFSPInstance, DPFSPEvaluator, parse_dpfsp_instance_text


def test_case_a_one_machine_one_factory():
    result = DPFSPEvaluator(DPFSPInstance(((3,), (2,)), (2, 10), 1)).evaluate([[0, 1]])
    assert result.completion_times == (3, 5)
    assert result.tardiness == (1, 0)
    assert result.total_tardiness == 1


def test_case_b_two_machines_one_factory():
    result = DPFSPEvaluator(DPFSPInstance(((2, 3), (4, 1)), (4, 10), 1)).evaluate([[0, 1]])
    assert result.completion_times == (5, 7)
    assert result.tardiness == (1, 0)
    assert result.total_tardiness == 1
    assert result.operation_completion_times == (((2, 5), (6, 7)),)


def test_case_c_two_independent_factories():
    result = DPFSPEvaluator(DPFSPInstance(((3,), (4,)), (2, 3), 2)).evaluate([[0], [1]])
    assert result.completion_times == (3, 4)
    assert result.tardiness == (1, 1)
    assert result.total_tardiness == 2


def test_case_d_empty_factory_is_valid():
    result = DPFSPEvaluator(DPFSPInstance(((3,), (4,)), (2, 3), 2)).evaluate([[0, 1], []])
    assert result.total_tardiness == 5
    assert result.operation_completion_times[1] == ()


@pytest.mark.parametrize("solution, message", [
    ([[0, 0]], "more than once"),
    ([[0]], "missing jobs"),
    ([[-1, 0]], "must be >= 0"),
    ([[0, 2]], "outside"),
    ([[0, 1], []], "expected 1"),
])
def test_invalid_solutions_are_rejected(solution, message):
    instance = DPFSPInstance(((1,), (1,)), (0, 0), 1)
    with pytest.raises(ValueError, match=message):
        DPFSPEvaluator(instance).evaluate(solution)


@pytest.mark.parametrize("processing, due_dates, factories", [
    (((1,), ()), (0, 0), 1),
    (((1,), (2,)), (0,), 1),
    (((0,),), (0,), 1),
    (((1,),), (-1,), 1),
    (((1,),), (0,), 0),
    (((1, 2), (3,)), (0, 0), 1),
])
def test_invalid_instances_are_rejected(processing, due_dates, factories):
    with pytest.raises((TypeError, ValueError)):
        DPFSPInstance(processing, due_dates, factories)


def test_parser_reorders_machine_pairs_and_reads_factory_count():
    raw = """2 2
2
1 3 0 2
0 4 1 1
Duedate
4
10
"""
    instance = parse_dpfsp_instance_text(raw)
    assert (instance.jobs, instance.machines, instance.factories) == (2, 2, 2)
    assert instance.processing_times == ((2, 3), (4, 1))
    assert instance.due_dates == (4, 10)


def test_parser_rejects_bad_machine_ids():
    raw = """1 2
2
0 5 0 7
Duedate
10
"""
    with pytest.raises(ValueError, match="duplicate machine id"):
        parse_dpfsp_instance_text(raw)


def test_parser_rejects_missing_due_date():
    raw = """1 1
2
0 5
Duedate
"""
    with pytest.raises(ValueError, match="expected 1 due-date rows"):
        parse_dpfsp_instance_text(raw)
