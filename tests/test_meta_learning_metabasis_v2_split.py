"""Deterministic split tests for metabasis_v2 pre-registration."""
from __future__ import annotations

from scripts.build_meta_learning_metabasis_v2_inventory_split import (
    SPLIT_SEED,
    build_split,
)


def _fake_inventory() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    # Two groups, 10 instances each, first 3 are pilot.
    for jobs, machines, start in ((20, 5, 1), (20, 10, 11)):
        group = f"{jobs}x{machines}"
        for offset in range(10):
            idx = start + offset
            rows.append({
                "instance": f"ta{idx:03d}",
                "path": f"data/benchmarks/taillard/ta{idx:03d}.txt",
                "jobs": jobs,
                "machines": machines,
                "group": group,
                "upper_bound": 1000 + idx,
                "lower_bound": 900 + idx,
                "sha256": f"hash{idx:03d}",
                "source_mirror": "test",
            })
    return rows


def test_split_is_deterministic_and_covers_stages():
    inventory = _fake_inventory()
    pilot = {f"ta{i:03d}" for i in (1, 2, 3, 11, 12, 13)}
    first = build_split(inventory, pilot, split_seed=SPLIT_SEED)
    second = build_split(inventory, pilot, split_seed=SPLIT_SEED)
    assert first == second
    assert len(first) == 20
    holdout = {r["instance"] for r in first if r["partition"] == "holdout"}
    assert holdout.isdisjoint(pilot)
    for group in ("20x5", "20x10"):
        members = [r for r in first if r["group"] == group]
        assert sum(r["stage"] == "pilot_v1" for r in members) == 3
        assert sum(r["partition"] == "development" and r["stage"] == 60 for r in members) == 1
        assert sum(r["partition"] == "development" and r["stage"] == 120 for r in members) == 4
        assert sum(r["partition"] == "holdout" and r["stage"] == 60 for r in members) == 1
        assert sum(r["partition"] == "holdout" and r["stage"] == 120 for r in members) == 1


def test_different_seed_changes_assignment():
    inventory = _fake_inventory()
    pilot = {f"ta{i:03d}" for i in (1, 2, 3, 11, 12, 13)}
    a = build_split(inventory, pilot, split_seed=SPLIT_SEED)
    b = build_split(inventory, pilot, split_seed=SPLIT_SEED + 1)
    a_hold = sorted(r["instance"] for r in a if r["partition"] == "holdout")
    b_hold = sorted(r["instance"] for r in b if r["partition"] == "holdout")
    assert a_hold != b_hold
