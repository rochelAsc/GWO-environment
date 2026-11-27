"""Smoke tests for metabasis_v2 runner helpers and freeze overwrite guard."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.freeze_meta_learning_metabasis_v2 import main as freeze_main
from scripts.run_meta_learning_metabasis_v2 import load_split_instances


def test_load_split_stage60_development_has_twelve(tmp_path: Path):
    split = Path("experiments/meta_learning/data/metabasis_v2/split_manifest.csv")
    rows = load_split_instances(split, partitions={"development"}, stages={"60"})
    # includes only stage 60 development (pilot_v1 filtered later by runner)
    assert len(rows) == 12
    assert all(r["partition"] == "development" for r in rows)
    assert all(str(r["stage"]) == "60" for r in rows)
    pilot = {
        "ta001", "ta002", "ta003", "ta011", "ta012", "ta013",
        "ta021", "ta022", "ta023", "ta031", "ta032", "ta033",
        "ta041", "ta042", "ta043", "ta051", "ta052", "ta053",
        "ta061", "ta062", "ta063", "ta071", "ta072", "ta073",
        "ta081", "ta082", "ta083", "ta091", "ta092", "ta093",
        "ta101", "ta102", "ta103", "ta111", "ta112", "ta113",
    }
    assert set(r["instance"] for r in rows).isdisjoint(pilot)


def test_freeze_refuses_overwrite(tmp_path: Path, monkeypatch):
    features = tmp_path / "features.csv"
    targets = tmp_path / "targets.csv"
    manifest = tmp_path / "manifest.csv"
    runs = tmp_path / "runs.csv"
    split = tmp_path / "split.csv"
    for path, header in (
        (features, ["instance", "sha256", "feature_version", "n_jobs"]),
        (targets, ["instance", "winner"]),
        (manifest, ["instance", "upper_bound"]),
        (runs, ["instance", "variant", "seed"]),
        (split, ["instance", "partition", "stage"]),
    ):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=header)
            writer.writeheader()
            writer.writerow({k: ("ta999" if k == "instance" else "x") for k in header})

    out = tmp_path / "freeze"
    out.mkdir()
    monkeypatch.setattr(
        "sys.argv",
        [
            "freeze",
            "--features", str(features),
            "--targets", str(targets),
            "--manifest", str(manifest),
            "--runs", str(runs),
            "--split", str(split),
            "--output", str(out),
        ],
    )
    with pytest.raises(SystemExit, match="refuse to overwrite"):
        freeze_main()
