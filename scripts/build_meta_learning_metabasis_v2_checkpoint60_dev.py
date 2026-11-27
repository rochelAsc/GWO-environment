"""Merge pilot_v1 reused runs with stage-60 new runs; aggregate development targets.

Does not open holdout. Does not modify metabasis_pilot_v1 files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from scripts.analyze_meta_learning_metabasis_pilot import (
    VARIANTS,
    aggregate_metabasis_pilot,
    validate_metabasis_pilot_runs,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PILOT_RUNS = ROOT / "results/meta_learning_metabasis_pilot_v1/runs.csv"
DEFAULT_V2_RUNS = ROOT / "results/meta_learning_metabasis_v2/runs.csv"
DEFAULT_SPLIT = ROOT / "experiments/meta_learning/data/metabasis_v2/split_manifest.csv"
DEFAULT_OUT = ROOT / "results/meta_learning_metabasis_v2/checkpoint60_dev"
RUN_FIELDS = [
    "variant", "instance", "jobs", "machines", "seed",
    "best_makespan", "upper_bound", "exact_evaluations",
    "surrogate_predictions", "runtime_seconds", "surrogate_prep_seconds",
    "instance_sha256", "model_sha256", "source", "partition", "stage",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-runs", type=Path, default=DEFAULT_PILOT_RUNS)
    parser.add_argument("--v2-runs", type=Path, default=DEFAULT_V2_RUNS)
    parser.add_argument("--split", type=Path, default=DEFAULT_SPLIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    split = _load_csv(args.split)
    pilot_split = {
        r["instance"]: r for r in split
        if r["partition"] == "development" and str(r["stage"]) == "pilot_v1"
    }
    stage60_dev = {
        r["instance"]: r for r in split
        if r["partition"] == "development" and str(r["stage"]) == "60"
    }
    if len(pilot_split) != 36 or len(stage60_dev) != 12:
        raise SystemExit(
            f"expected 36 pilot + 12 stage60 development; got {len(pilot_split)}+{len(stage60_dev)}"
        )

    holdout_ids = {r["instance"] for r in split if r["partition"] == "holdout"}
    pilot_runs = _load_csv(args.pilot_runs)
    v2_runs = _load_csv(args.v2_runs)

    # Compatibility: instance hashes must match the frozen split inventory.
    merged: list[dict[str, object]] = []
    for row in pilot_runs:
        inst = row["instance"]
        if inst not in pilot_split:
            raise SystemExit(f"pilot run instance not in pilot_v1 split rows: {inst}")
        expected_hash = pilot_split[inst]["sha256"]
        if row["instance_sha256"] != expected_hash:
            raise SystemExit(
                f"pilot hash mismatch {inst}: run={row['instance_sha256']} split={expected_hash}"
            )
        if inst in holdout_ids:
            raise SystemExit(f"pilot instance incorrectly marked holdout: {inst}")
        merged.append({
            **{k: row.get(k, "") for k in RUN_FIELDS if k in row or k in (
                "source", "partition", "stage"
            )},
            "source": "pilot_v1_reused",
            "partition": "development",
            "stage": "pilot_v1",
            "variant": row["variant"],
            "instance": inst,
            "jobs": row["jobs"],
            "machines": row["machines"],
            "seed": row["seed"],
            "best_makespan": row["best_makespan"],
            "upper_bound": row.get("upper_bound", ""),
            "exact_evaluations": row["exact_evaluations"],
            "surrogate_predictions": row["surrogate_predictions"],
            "runtime_seconds": row["runtime_seconds"],
            "surrogate_prep_seconds": row.get("surrogate_prep_seconds", "0"),
            "instance_sha256": row["instance_sha256"],
            "model_sha256": row.get("model_sha256", ""),
        })

    for row in v2_runs:
        inst = row["instance"]
        if inst in holdout_ids:
            raise SystemExit(f"holdout instance found in v2 runs: {inst}")
        if inst not in stage60_dev:
            raise SystemExit(f"v2 run instance not in stage60 development: {inst}")
        if row["instance_sha256"] != stage60_dev[inst]["sha256"]:
            raise SystemExit(f"v2 hash mismatch for {inst}")
        if row.get("source") != "metabasis_v2_new":
            raise SystemExit(f"unexpected source for {inst}: {row.get('source')}")
        merged.append({k: row.get(k, "") for k in RUN_FIELDS})

    if len(merged) != 576:
        raise SystemExit(f"expected 576 development runs; got {len(merged)}")

    # Manifest for the 48 development instances only (for aggregation/UB).
    manifest_rows = []
    for inst, meta in sorted({**pilot_split, **stage60_dev}.items()):
        manifest_rows.append({
            "instance": inst,
            "path": meta["path"],
            "jobs": meta["jobs"],
            "machines": meta["machines"],
            "upper_bound": meta.get("upper_bound", ""),
            "lower_bound": meta.get("lower_bound", ""),
            "sha256": meta["sha256"],
            "partition": meta["partition"],
            "stage": meta["stage"],
        })

    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    runs_path = out / "development_runs.csv"
    manifest_path = out / "development_manifest.csv"
    _write_csv(runs_path, merged, RUN_FIELDS)
    _write_csv(manifest_path, manifest_rows, list(manifest_rows[0].keys()))

    # Validate + aggregate using existing pilot aggregator contracts.
    validate_metabasis_pilot_runs(
        [{k: str(v) for k, v in row.items()} for row in merged],
        [{k: str(v) for k, v in row.items()} for row in manifest_rows],
    )
    rows, summary = aggregate_metabasis_pilot(
        [{k: str(v) for k, v in row.items()} for row in merged],
        {r["instance"]: r for r in manifest_rows},
    )
    if len(rows) != 48:
        raise SystemExit(f"expected 48 aggregated instances; got {len(rows)}")

    analysis_dir = out / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    targets_path = analysis_dir / "per_instance_targets.csv"
    _write_csv(targets_path, rows, list(rows[0].keys()))
    summary["protocol"] = "meta_learning_metabasis_v2_checkpoint60_dev"
    summary["n_runs_development"] = 576
    summary["n_instances_development"] = 48
    summary["holdout_sealed"] = True
    summary["sources"] = {
        "pilot_v1_reused": 432,
        "metabasis_v2_new": 144,
    }
    summary["hashes_sha256"] = {
        "development_runs.csv": sha256_file(runs_path),
        "development_manifest.csv": sha256_file(manifest_path),
        "per_instance_targets.csv": sha256_file(targets_path),
        "split_manifest.csv": sha256_file(args.split.resolve()),
    }
    summary["notes"] = list(summary.get("notes", [])) + [
        "Checkpoint 60 development only; holdout targets sealed.",
        "Pilot rows marked source=pilot_v1_reused after hash compatibility check.",
    ]
    (analysis_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print("N_RUNS", len(merged))
    print("N_INST", len(rows))
    print("WINS", summary["wins"])
    print("LOW_CONF", summary["low_confidence_labels_margin_lt_0.5pct"])
    print("REGRET", {v: round(summary["mean_regret_vs_oracle_if_always"][v], 6) for v in VARIANTS})
    print("HASHES", summary["hashes_sha256"])
    print("WROTE", out)


if __name__ == "__main__":
    main()
