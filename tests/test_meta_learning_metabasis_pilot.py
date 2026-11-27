"""Integrity tests for metabasis pilot aggregation."""
from __future__ import annotations

import copy

import pytest

from scripts.analyze_meta_learning_metabasis_pilot import (
    MetabasisPilotValidationError,
    VARIANTS,
    aggregate_metabasis_pilot,
    validate_metabasis_pilot_runs,
)


def _run(instance: str, variant: str, seed: int, **overrides) -> dict[str, str]:
    row = {
        "variant": variant,
        "instance": instance,
        "jobs": "20",
        "machines": "5",
        "seed": str(seed),
        "best_makespan": "1000",
        "upper_bound": "1000",
        "exact_evaluations": "15030",
        "surrogate_predictions": "0" if variant != "surrogate" else "15000",
        "runtime_seconds": "1.0",
        "surrogate_prep_seconds": "0.0",
        "instance_sha256": "abc",
        "model_sha256": "mdl" if variant == "surrogate" else "",
    }
    row.update({k: str(v) for k, v in overrides.items()})
    return row


def _complete(instances=("ta001", "ta002"), seeds=(0, 1, 2)) -> tuple[list[dict], list[dict]]:
    runs = [
        _run(inst, variant, seed)
        for inst in instances
        for variant in VARIANTS
        for seed in seeds
    ]
    manifest = [
        {"instance": inst, "upper_bound": "1000"} for inst in instances
    ]
    return runs, manifest


def test_validate_accepts_complete_grid():
    runs, manifest = _complete()
    audit = validate_metabasis_pilot_runs(runs, manifest)
    assert audit["ok"] is True
    assert audit["n_runs"] == 24
    assert audit["n_instances"] == 2
    assert audit["missing_keys"] == 0


def test_validate_rejects_missing_key():
    runs, manifest = _complete()
    runs = [r for r in runs if not (r["instance"] == "ta001" and r["variant"] == "fuzzy" and r["seed"] == "1")]
    with pytest.raises(MetabasisPilotValidationError, match="missing"):
        validate_metabasis_pilot_runs(runs, manifest)


def test_validate_rejects_duplicate_key():
    runs, manifest = _complete()
    runs.append(copy.deepcopy(runs[0]))
    with pytest.raises(MetabasisPilotValidationError, match="duplicate"):
        validate_metabasis_pilot_runs(runs, manifest)


def test_validate_rejects_invalid_variant():
    runs, manifest = _complete()
    runs[0]["variant"] = "neural"
    with pytest.raises(MetabasisPilotValidationError, match="unexpected variant"):
        validate_metabasis_pilot_runs(runs, manifest)


def test_validate_rejects_unexpected_seed():
    runs, manifest = _complete()
    runs[0]["seed"] = "9"
    with pytest.raises(MetabasisPilotValidationError, match="unexpected seed"):
        validate_metabasis_pilot_runs(runs, manifest)


def test_validate_rejects_non_finite_makespan():
    runs, manifest = _complete()
    runs[0]["best_makespan"] = "nan"
    with pytest.raises(MetabasisPilotValidationError, match="non-finite|non-numeric"):
        validate_metabasis_pilot_runs(runs, manifest)


def test_validate_rejects_empty_surrogate_model_hash():
    runs, manifest = _complete()
    for row in runs:
        if row["variant"] == "surrogate":
            row["model_sha256"] = ""
            break
    with pytest.raises(MetabasisPilotValidationError, match="model_sha256"):
        validate_metabasis_pilot_runs(runs, manifest)


def test_validate_rejects_incomplete_manifest_coverage():
    runs, manifest = _complete()
    manifest = [manifest[0]]  # drop ta002
    with pytest.raises(MetabasisPilotValidationError, match="extra|missing"):
        validate_metabasis_pilot_runs(runs, manifest)


def test_aggregate_marks_ub_normalization_and_winner():
    runs, manifest = _complete(instances=("ta001",), seeds=(0, 1, 2))
    for row in runs:
        if row["variant"] == "fuzzy":
            row["best_makespan"] = "900"
        elif row["variant"] == "baseline":
            row["best_makespan"] = "1000"
        else:
            row["best_makespan"] = "1100"
    validate_metabasis_pilot_runs(runs, manifest)
    rows, summary = aggregate_metabasis_pilot(runs, {m["instance"]: m for m in manifest})
    assert len(rows) == 1
    assert rows[0]["winner"] == "fuzzy"
    assert rows[0]["norm"] == "ub"
    assert summary["normalization_counts"] == {"ub": 1}
    assert summary["wins"]["fuzzy"] == 1


def test_aggregate_uses_rel_best_when_ub_missing():
    runs, manifest = _complete(instances=("ta001",), seeds=(0, 1, 2))
    manifest[0]["upper_bound"] = ""
    for row in runs:
        row["best_makespan"] = "1000" if row["variant"] == "optuna" else "1200"
    rows, summary = aggregate_metabasis_pilot(runs, {m["instance"]: m for m in manifest})
    assert rows[0]["norm"] == "rel_best"
    assert rows[0]["winner"] == "optuna"
    assert rows[0]["y_optuna"] == pytest.approx(1.0)
    assert summary["normalization_counts"] == {"rel_best": 1}
