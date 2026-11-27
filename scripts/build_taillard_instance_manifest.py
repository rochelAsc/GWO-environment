"""Build SHA-256 inventory for Taillard instances used by Meta-Learning."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from scripts.pfs_taillard import load_taillard_instance

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "data/benchmarks/taillard"
DEFAULT_OUT = ROOT / "experiments/meta_learning/data/instance_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    rows = []
    for path in sorted(args.input_dir.glob("ta*.txt")):
        inst = load_taillard_instance(path)
        rows.append({
            "instance": inst.name,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "jobs": inst.n_jobs,
            "machines": inst.n_machines,
            "upper_bound": inst.upper_bound,
            "lower_bound": inst.lower_bound,
            "sha256": sha256(path),
        })
    groups = {}
    for row in rows:
        key = f"{row['jobs']}x{row['machines']}"
        groups.setdefault(key, []).append(row["instance"])
    payload = {
        "protocol": "taillard_meta_learning_inventory_v1",
        "source_mirror": "https://github.com/arnaud-m/pisco/tree/master/pisco-shop/src/main/benchmarks/instances/flow-shop/taillard",
        "n_instances": len(rows),
        "groups": {k: sorted(v) for k, v in sorted(groups.items())},
        "instances": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    csv_path = args.output.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"instances={len(rows)} wrote {args.output} and {csv_path}")


if __name__ == "__main__":
    main()
