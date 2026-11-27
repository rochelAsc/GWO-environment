"""Build Taillard-120 inventory and pre-registered metabasis_v2 split.

split_seed=20261127; numpy.random.default_rng(20261127); groups in lexicographic
order of jobsxmáchines; within each group, sort the 7 non-pilot IDs and permute.
First 5 = development, last 2 = holdout. First of each partition = stage 60;
remaining = stage 120. Pilot 36 stay development (stage=pilot_v1).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from scripts.pfs_taillard import load_taillard_instance

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "data/benchmarks/taillard"
DEFAULT_PILOT_MANIFEST = ROOT / "experiments/meta_learning/data/instance_manifest.csv"
DEFAULT_OUT = ROOT / "results/meta_learning_metabasis_v2"
SPLIT_SEED = 20261127
SOURCE_MIRROR = (
    "https://github.com/arnaud-m/pisco/tree/master/"
    "pisco-shop/src/main/benchmarks/instances/flow-shop/taillard"
)


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


def _load_pilot_hashes(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as stream:
        return {row["instance"]: row["sha256"] for row in csv.DictReader(stream)}


def inventory_instances(input_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(input_dir.glob("ta*.txt")):
        inst = load_taillard_instance(path)
        rows.append({
            "instance": inst.name,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "jobs": int(inst.n_jobs),
            "machines": int(inst.n_machines),
            "group": f"{inst.n_jobs}x{inst.n_machines}",
            "upper_bound": inst.upper_bound if inst.upper_bound is not None else "",
            "lower_bound": inst.lower_bound if inst.lower_bound is not None else "",
            "sha256": sha256_file(path),
            "source_mirror": SOURCE_MIRROR,
        })
    return rows


def build_split(
    inventory: list[dict[str, object]],
    pilot_ids: set[str],
    *,
    split_seed: int = SPLIT_SEED,
) -> list[dict[str, object]]:
    by_group: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in inventory:
        by_group[str(row["group"])].append(row)

    rng = np.random.default_rng(split_seed)
    split_rows: list[dict[str, object]] = []

    for group in sorted(by_group):
        members = sorted(by_group[group], key=lambda r: str(r["instance"]))
        if len(members) != 10:
            raise ValueError(f"group {group} has {len(members)} instances; expected 10")
        pilot = [r for r in members if r["instance"] in pilot_ids]
        rest = [r for r in members if r["instance"] not in pilot_ids]
        if len(pilot) != 3 or len(rest) != 7:
            raise ValueError(
                f"group {group}: expected 3 pilot + 7 rest; got {len(pilot)}+{len(rest)}"
            )
        for row in pilot:
            split_rows.append({
                **row,
                "partition": "development",
                "stage": "pilot_v1",
                "eligible_for_holdout": 0,
                "split_seed": split_seed,
            })
        rest_ids = [str(r["instance"]) for r in rest]
        order = list(rng.permutation(rest_ids))
        development_ids = order[:5]
        holdout_ids = order[5:]
        for idx, instance_id in enumerate(development_ids):
            row = next(r for r in rest if r["instance"] == instance_id)
            split_rows.append({
                **row,
                "partition": "development",
                "stage": 60 if idx == 0 else 120,
                "eligible_for_holdout": 0,
                "split_seed": split_seed,
            })
        for idx, instance_id in enumerate(holdout_ids):
            row = next(r for r in rest if r["instance"] == instance_id)
            split_rows.append({
                **row,
                "partition": "holdout",
                "stage": 60 if idx == 0 else 120,
                "eligible_for_holdout": 1,
                "split_seed": split_seed,
            })

    split_rows.sort(key=lambda r: (str(r["group"]), str(r["instance"])))
    return split_rows


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--pilot-manifest", type=Path, default=DEFAULT_PILOT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--split-seed", type=int, default=SPLIT_SEED)
    args = parser.parse_args()

    pilot_hashes = _load_pilot_hashes(args.pilot_manifest)
    if len(pilot_hashes) != 36:
        raise SystemExit(f"pilot manifest must have 36 rows; got {len(pilot_hashes)}")

    inventory = inventory_instances(args.input_dir)
    if len(inventory) != 120:
        raise SystemExit(f"expected 120 instances; got {len(inventory)}")

    by_id = {str(r["instance"]): r for r in inventory}
    hash_mismatches = []
    for instance, expected in sorted(pilot_hashes.items()):
        actual = str(by_id[instance]["sha256"])
        if actual != expected:
            hash_mismatches.append((instance, expected, actual))
    if hash_mismatches:
        raise SystemExit(f"pilot hash mismatches: {hash_mismatches[:5]}")

    split_rows = build_split(inventory, set(pilot_hashes), split_seed=args.split_seed)

    # Coverage checks
    groups = sorted({str(r["group"]) for r in inventory})
    if len(groups) != 12:
        raise SystemExit(f"expected 12 groups; got {len(groups)}")
    for group in groups:
        members = [r for r in split_rows if r["group"] == group]
        assert len(members) == 10
        assert sum(1 for r in members if r["partition"] == "development" and r["stage"] == "pilot_v1") == 3
        assert sum(1 for r in members if r["partition"] == "development" and r["stage"] == 60) == 1
        assert sum(1 for r in members if r["partition"] == "development" and r["stage"] == 120) == 4
        assert sum(1 for r in members if r["partition"] == "holdout" and r["stage"] == 60) == 1
        assert sum(1 for r in members if r["partition"] == "holdout" and r["stage"] == 120) == 1

    holdout_ids = {str(r["instance"]) for r in split_rows if r["partition"] == "holdout"}
    if holdout_ids & set(pilot_hashes):
        raise SystemExit("holdout overlaps pilot instances")

    out = args.output.resolve()
    inv_dir = out / "inventory"
    split_dir = out / "split"
    inv_dir.mkdir(parents=True, exist_ok=True)
    split_dir.mkdir(parents=True, exist_ok=True)

    inv_csv = inv_dir / "instance_manifest_120.csv"
    _write_csv(inv_csv, inventory)
    inv_hash = sha256_file(inv_csv)

    split_csv = split_dir / "split_manifest.csv"
    _write_csv(split_csv, split_rows)
    split_hash = sha256_file(split_csv)

    # Also place the pre-registered split under experiments freeze path (split only).
    freeze_split_dir = ROOT / "experiments/meta_learning/data/metabasis_v2"
    freeze_split_dir.mkdir(parents=True, exist_ok=True)
    freeze_split = freeze_split_dir / "split_manifest.csv"
    if freeze_split.exists():
        raise SystemExit(f"refuse to overwrite existing split: {freeze_split}")
    _write_csv(freeze_split, split_rows)
    freeze_split_hash = sha256_file(freeze_split)
    if freeze_split_hash != split_hash:
        raise SystemExit("split hash mismatch between results and experiments copies")

    summary = {
        "protocol": "meta_learning_metabasis_v2_inventory_split",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_branch": _git(["branch", "--show-current"]),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "numpy_version": np.__version__,
        "split_seed": args.split_seed,
        "rng": "numpy.random.default_rng(split_seed); sequential per lexicographic group",
        "n_instances": 120,
        "n_groups": 12,
        "pilot_instances": 36,
        "pilot_hashes_verified": True,
        "checkpoint_60": {
            "development": 48,
            "holdout_sealed": 12,
            "new_development_to_run": 12,
        },
        "target_120": {
            "development": 96,
            "holdout_sealed": 24,
        },
        "hashes_sha256": {
            "instance_manifest_120.csv": inv_hash,
            "split_manifest.csv": split_hash,
        },
        "paths": {
            "inventory_csv": str(inv_csv.as_posix()),
            "split_csv": str(split_csv.as_posix()),
            "freeze_split_csv": str(freeze_split.as_posix()),
        },
        "ub_missing": [r["instance"] for r in inventory if r["upper_bound"] in ("", None)],
        "lb_missing": [r["instance"] for r in inventory if r["lower_bound"] in ("", None)],
        "notes": [
            "Holdout targets must remain sealed until confirmatory evaluation.",
            "Do not alter split_seed or regenerate after inspecting algorithm outcomes.",
        ],
    }
    summary_path = split_dir / "split_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    # Compact stage lists for operator review
    stage60_dev = sorted(
        str(r["instance"]) for r in split_rows
        if r["partition"] == "development" and r["stage"] == 60
    )
    stage60_hold = sorted(
        str(r["instance"]) for r in split_rows
        if r["partition"] == "holdout" and r["stage"] == 60
    )
    print("N_INST", 120)
    print("GROUPS", len(groups))
    print("PILOT_HASHES", "OK")
    print("SPLIT_SEED", args.split_seed)
    print("STAGE60_DEV", stage60_dev)
    print("STAGE60_HOLDOUT", stage60_hold)
    print("UB_MISSING", summary["ub_missing"])
    print("INV_SHA", inv_hash)
    print("SPLIT_SHA", split_hash)
    print("WROTE", out)
    print("WROTE_FREEZE_SPLIT", freeze_split)


if __name__ == "__main__":
    main()
