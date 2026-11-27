"""Freeze metabasis_pilot_v1: features + targets + provenance hashes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from experiments.meta_learning.scripts.extract_instance_features import FEATURE_VERSION
from scripts.analyze_meta_learning_metabasis_pilot import (
    DEFAULT_MANIFEST,
    DEFAULT_RUNS,
    VARIANTS,
    validate_metabasis_pilot_runs,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FEATURES = ROOT / "experiments/meta_learning/data/instance_features.csv"
DEFAULT_TARGETS = (
    ROOT / "results/meta_learning_metabasis_pilot_v1/analysis/per_instance_targets.csv"
)
DEFAULT_OUT = ROOT / "experiments/meta_learning/data/metabasis_pilot_v1"
METADATA_FEATURE_COLS = ("instance", "sha256", "feature_version")
FORBIDDEN_PREDICTOR_TOKENS = (
    "makespan",
    "upper_bound",
    "lower_bound",
    "ub",
    "lb",
    "seed",
    "winner",
    "regret",
    "path",
    "model_sha",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(
            ["git", *cmd],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def validate_feature_target_alignment(
    feature_rows: list[dict[str, str]],
    target_rows: list[dict[str, str]],
    feature_cols: list[str],
) -> list[str]:
    predictors = [c for c in feature_cols if c not in METADATA_FEATURE_COLS]
    bad = [
        c for c in predictors
        if any(tok in c.lower() for tok in FORBIDDEN_PREDICTOR_TOKENS)
    ]
    if bad:
        raise ValueError(f"forbidden predictor columns: {bad}")
    feat_inst = {r["instance"] for r in feature_rows}
    targ_inst = {r["instance"] for r in target_rows}
    if feat_inst != targ_inst:
        raise ValueError(
            f"feature/target instance mismatch missing={sorted(targ_inst - feat_inst)} "
            f"extra={sorted(feat_inst - targ_inst)}"
        )
    versions = {r.get("feature_version") for r in feature_rows}
    if versions != {FEATURE_VERSION}:
        raise ValueError(f"unexpected feature_version set: {versions}")
    return predictors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    with args.runs.open(newline="", encoding="utf-8") as stream:
        runs = list(csv.DictReader(stream))
    with args.manifest.open(newline="", encoding="utf-8") as stream:
        manifest_rows = list(csv.DictReader(stream))
    audit = validate_metabasis_pilot_runs(runs, manifest_rows)

    feature_cols, feature_rows = _load_csv(args.features)
    target_cols, target_rows = _load_csv(args.targets)
    predictors = validate_feature_target_alignment(feature_rows, target_rows, feature_cols)

    out = args.output.resolve()
    if out.exists():
        raise SystemExit(f"refuse to overwrite existing freeze dir: {out}")
    out.mkdir(parents=True)

    shutil.copy2(args.features, out / "instance_features.csv")
    shutil.copy2(args.targets, out / "per_instance_targets.csv")
    shutil.copy2(args.manifest, out / "instance_manifest.csv")
    shutil.copy2(args.runs, out / "runs.csv")

    freeze = {
        "schema_version": "metabasis_pilot_v1",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_branch": _git(["branch", "--show-current"]),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "feature_version": FEATURE_VERSION,
        "variants": list(VARIANTS),
        "seeds": [0, 1, 2],
        "n_instances": audit["n_instances"],
        "n_runs": audit["n_runs"],
        "predictor_columns": predictors,
        "metadata_feature_columns": list(METADATA_FEATURE_COLS),
        "primary_selection_metric": "per_instance_regret_vs_oracle",
        "normalization": {
            "preferred": "upper_bound_when_available",
            "fallback": "rel_best_among_variant_means",
            "note": (
                "If any instance uses rel_best, do not interpret global mean_y "
                "as a homogeneous scale; prefer per-instance regret."
            ),
        },
        "hashes_sha256": {
            "instance_features.csv": sha256_file(out / "instance_features.csv"),
            "per_instance_targets.csv": sha256_file(out / "per_instance_targets.csv"),
            "instance_manifest.csv": sha256_file(out / "instance_manifest.csv"),
            "runs.csv": sha256_file(out / "runs.csv"),
        },
        "sources": {
            "features": str(args.features.as_posix()),
            "targets": str(args.targets.as_posix()),
            "manifest": str(args.manifest.as_posix()),
            "runs": str(args.runs.as_posix()),
        },
        "notes": [
            "Exploratory pilot freeze; not confirmatory Meta-Learning evidence.",
            "Operational baseline to beat: always Fuzzy (also computed inside each train fold).",
            "Surrogate budget remains unequal: 1530 exact + 15000 predictions vs 15030 exact.",
        ],
    }
    (out / "freeze_manifest.json").write_text(
        json.dumps(freeze, indent=2) + "\n", encoding="utf-8"
    )
    print("FROZE", out)
    print("N_INST", freeze["n_instances"])
    print("N_RUNS", freeze["n_runs"])
    print("PREDICTORS", len(predictors))
    print("HASHES", freeze["hashes_sha256"])


if __name__ == "__main__":
    main()
