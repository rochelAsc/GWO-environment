from scripts.run_week6_benchmark import holm_adjust


def test_holm_adjustment_is_monotonic_in_sorted_p_values():
    adjusted = holm_adjust([0.04, 0.01, 0.03, 0.20])
    assert adjusted == [0.09, 0.04, 0.09, 0.20]


def test_holm_adjustment_caps_values_at_one():
    assert holm_adjust([0.8, 0.9]) == [1.0, 1.0]
