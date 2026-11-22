#!/usr/bin/env python3
"""Run a reproducible, reduced-budget pilot for random-key GWO on DPFSP-DD.

The script selects one Small, one intermediate (Large-family) and one
largest instance from the ZIP, then runs the four population/schedule
combinations with matched seeds and complete population batches.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import statistics
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np

from scripts.discrete_gwo_dpfsp import RandomKeyGWO
from scripts.dpfsp_dd import parse_dpfsp_instance_text


CONFIGURATIONS = (
    ("GWO-30-L", 30, "linear"),
    ("GWO-30-Q", 30, "quadratic"),
    ("GWO-55-L", 55, "linear"),
    ("GWO-55-Q", 55, "quadratic"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def select_instances(archive: zipfile.ZipFile):
    candidates = []
    for info in archive.infolist():
        if info.is_dir() or PurePosixPath(info.filename).suffix.lower() not in {".txt", ".dat", ".ins"}:
            continue
        parts = PurePosixPath(info.filename).parts
        family = "Small" if "Small" in parts else ("Large" if "Large" in parts else None)
        if family is None:
            continue
        raw = archive.read(info)
        instance = parse_dpfsp_instance_text(raw.decode("utf-8-sig"), source=info.filename)
        candidates.append((info.filename, raw, instance, family))

    selections = []
    targets = (
        ("Small", "small", 4, 2),
        ("Large", "intermediate", 50, 10),
        ("Large", "large", 500, 20),
    )
    for family, label, target_jobs, target_machines in targets:
        pool = [item for item in candidates if item[3] == family]
        if not pool:
            raise ValueError(f"No valid {family} instances found in archive")
        chosen = min(
            pool,
            key=lambda item: (
                abs(item[2].jobs - target_jobs),
                abs(item[2].machines - target_machines),
                item[2].factories,
                item[0],
            ),
        )
        name, raw, instance, _ = chosen
        selections.append({
            "label": label,
            "path": name,
            "sha256": sha256(raw),
            "jobs": instance.jobs,
            "machines": instance.machines,
            "factories": instance.factories,
            "instance": instance,
        })
    return selections


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", help="Path to data/instances/DPFSP_DD.zip")
    parser.add_argument("--output-dir", default="results/gwo_pilot")
    parser.add_argument("--budget", type=int, default=990,
                        help="Real objective evaluations per run; must be divisible by 30 and 55")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    args = parser.parse_args()

    if args.budget < 55 or args.budget % 30 or args.budget % 55:
        raise SystemExit("--budget must be >= 55 and divisible by both 30 and 55")
    if not args.seeds or any(seed < 0 for seed in args.seeds):
        raise SystemExit("--seeds must contain non-negative integers")

    zip_path = Path(args.zip_path)
    if not zip_path.is_file():
        raise SystemExit(f"ZIP file not found: {zip_path}")
    archive_bytes = zip_path.read_bytes()
    archive_hash = sha256(archive_bytes)

    with zipfile.ZipFile(zip_path) as archive:
        selections = select_instances(archive)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for selected in selections:
        instance = selected.pop("instance")
        for config, wolves, decay in CONFIGURATIONS:
            for seed in args.seeds:
                optimizer = RandomKeyGWO(
                    instance,
                    n_wolves=wolves,
                    max_evaluations=args.budget,
                    seed=seed,
                    a_decay=decay,
                )
                started = time.perf_counter()
                result = optimizer.optimize()
                elapsed = time.perf_counter() - started

                rows.append({
                    "instance_label": selected["label"],
                    "instance_path": selected["path"],
                    "instance_sha256": selected["sha256"],
                    "jobs": selected["jobs"],
                    "machines": selected["machines"],
                    "factories": selected["factories"],
                    "configuration": config,
                    "wolves": wolves,
                    "a_decay": decay,
                    "seed": seed,
                    "budget_requested": args.budget,
                    "evaluations": result.evaluations,
                    "generations": result.generations,
                    "best_total_tardiness": result.best_fitness,
                    "unique_decoded_solutions": result.unique_decoded_solutions,
                    "coordinate_saturation_fraction": result.coordinate_saturation_fraction,
                    "elapsed_seconds": round(elapsed, 6),
                    "history": json.dumps(result.history),
                })
                print(
                    f"{selected['label']} | {config} | seed={seed} | "
                    f"TT={result.best_fitness} | evals={result.evaluations} | "
                    f"unique={result.unique_decoded_solutions} | {elapsed:.2f}s",
                    flush=True,
                )

    csv_path = output_dir / "pilot_runs.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    grouped = {}
    for row in rows:
        key = (row["instance_label"], row["configuration"])
        grouped.setdefault(key, []).append(row)

    summary = []
    for (label, config), group in sorted(grouped.items()):
        values = [int(row["best_total_tardiness"]) for row in group]
        times = [float(row["elapsed_seconds"]) for row in group]
        summary.append({
            "instance_label": label,
            "configuration": config,
            "runs": len(group),
            "mean_total_tardiness": statistics.mean(values),
            "median_total_tardiness": statistics.median(values),
            "stdev_total_tardiness": statistics.stdev(values) if len(values) > 1 else 0.0,
            "mean_elapsed_seconds": statistics.mean(times),
            "mean_unique_decoded_solutions": statistics.mean(
                int(row["unique_decoded_solutions"]) for row in group
            ),
            "mean_coordinate_saturation_fraction": statistics.mean(
                float(row["coordinate_saturation_fraction"]) for row in group
            ),
        })

    metadata = {
        "archive_path": str(zip_path),
        "archive_sha256": archive_hash,
        "budget_per_run": args.budget,
        "seeds": args.seeds,
        "configurations": [
            {"id": name, "wolves": wolves, "a_decay": decay}
            for name, wolves, decay in CONFIGURATIONS
        ],
        "instances": [
            {key: value for key, value in item.items() if key != "instance"}
            for item in selections
        ],
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
        },
        "total_runs": len(rows),
        "summary": summary,
        "notes": [
            "Reduced-budget technical pilot; not part of the confirmatory benchmark.",
            "Only the four GWO population/schedule combinations are included.",
            "Fuzzy and Surrogate are excluded until their DPFSP-DD adaptations are implemented.",
            "No partial population batches are run.",
        ],
    }
    json_path = output_dir / "pilot_summary.json"
    json_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nCSV: {csv_path}")
    print(f"Summary: {json_path}")
    print(f"Completed runs: {len(rows)}")


if __name__ == "__main__":
    main()
