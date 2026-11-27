"""Freeze metabasis_v2 artifacts into a new versioned directory (no overwrite)."""
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

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "experiments/meta_learning/data/metabasis_v2_freeze"
DEFAULT_SPLIT = ROOT / "experiments/meta_learning/data/metabasis_v2/split_manifest.csv"
METADATA_FEATURE_COLS = ("instance", "sha256", "feature_version")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *cmd], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--split", type=Path, default=DEFAULT_SPLIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--schema-version", default="metabasis_v2")
    args = parser.parse_args()

    out = args.output.resolve()
    if out.exists():
        raise SystemExit(f"refuse to overwrite existing freeze dir: {out}")
    if "metabasis_pilot_v1" in str(out).replace("\\", "/"):
        raise SystemExit("refuse to write v2 freeze into pilot_v1 path")

    required = {
        "features": args.features,
        "targets": args.targets,
        "manifest": args.manifest,
        "runs": args.runs,
        "split": args.split,
    }
    for label, path in required.items():
        if not path.is_file():
            raise SystemExit(f"missing {label}: {path}")

    with args.features.open(newline="", encoding="utf-8") as stream:
        feature_reader = csv.DictReader(stream)
        feature_cols = list(feature_reader.fieldnames or [])
        feature_rows = list(feature_reader)
    predictors = [c for c in feature_cols if c not in METADATA_FEATURE_COLS]
    if any(tok in c.lower() for c in predictors for tok in ("makespan", "winner", "seed", "ub", "lb")):
        raise SystemExit("forbidden tokens detected in predictor columns")

    out.mkdir(parents=True)
    mapping = {
        "instance_features.csv": args.features,
        "per_instance_targets.csv": args.targets,
        "instance_manifest.csv": args.manifest,
        "runs.csv": args.runs,
        "split_manifest.csv": args.split,
    }
    hashes = {}
    for name, src in mapping.items():
        dest = out / name
        shutil.copy2(src, dest)
        hashes[name] = sha256_file(dest)

    freeze = {
        "schema_version": args.schema_version,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_branch": _git(["branch", "--show-current"]),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "feature_version": FEATURE_VERSION,
        "n_feature_rows": len(feature_rows),
        "predictor_columns": predictors,
        "hashes_sha256": hashes,
        "notes": [
            "metabasis_v2 freeze; do not overwrite.",
            "Holdout targets remain sealed until confirmatory evaluation protocol is frozen.",
        ],
    }
    (out / "freeze_manifest.json").write_text(
        json.dumps(freeze, indent=2) + "\n", encoding="utf-8"
    )
    print("FROZE", out)
    print("SCHEMA", args.schema_version)
    print("HASHES", hashes)


if __name__ == "__main__":
    main()
