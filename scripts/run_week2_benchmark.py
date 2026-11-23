"""Reproducible 30-seed Week 2 Taillard PFSP benchmark."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

from scripts.gwo_pfs import gwo_pfs
from scripts.pfs_taillard import load_taillard_instance


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(instances: list[Path], output: Path, seeds: int, wolves: int, iterations: int):
    output.mkdir(parents=True, exist_ok=True)
    run_rows = []
    convergence_rows = []
    metadata = {
        "protocol": "week2_taillard_pfsp_gwo_v1",
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "n_wolves": wolves,
        "iterations": iterations,
        "seeds": list(range(seeds)),
        "evaluations_per_run_expected": wolves * (iterations + 1),
        "update_semantics": "synchronous_frozen_alpha_beta_delta",
        "encoding": "random_keys_[0,1]_stable_argsort",
        "a_schedule": "linear_2_to_0",
        "objective": "makespan",
        "instances": [],
    }

    for instance_path in instances:
        instance = load_taillard_instance(instance_path)
        metadata["instances"].append({
            "name": instance.name,
            "jobs": instance.n_jobs,
            "machines": instance.n_machines,
            "published_seed": instance.published_seed,
            "published_upper_bound": instance.upper_bound,
            "published_lower_bound": instance.lower_bound,
            "sha256": sha256(instance_path),
            "path": str(instance_path),
        })
        per_seed_histories = []
        for seed in range(seeds):
            start = time.perf_counter()
            result = gwo_pfs(
                instance.processing_times,
                n_wolves=wolves,
                iterations=iterations,
                seed=seed,
            )
            elapsed = time.perf_counter() - start
            if result.evaluations != wolves * (iterations + 1):
                raise RuntimeError("unexpected objective evaluation count")
            per_seed_histories.append(result.convergence)
            run_rows.append({
                "instance": instance.name,
                "jobs": instance.n_jobs,
                "machines": instance.n_machines,
                "seed": seed,
                "best_makespan": result.best_fitness,
                "published_upper_bound": instance.upper_bound,
                "gap_to_published_ub_pct": (
                    100.0 * (result.best_fitness - instance.upper_bound)
                    / instance.upper_bound if instance.upper_bound else None
                ),
                "evaluations": result.evaluations,
                "runtime_seconds": elapsed,
                "best_permutation": " ".join(map(str, result.best_permutation.tolist())),
            })

        matrix = np.vstack(per_seed_histories)
        means = matrix.mean(axis=0)
        stds = matrix.std(axis=0, ddof=1) if seeds > 1 else np.zeros(matrix.shape[1])
        for generation, (mean, std) in enumerate(zip(means, stds)):
            convergence_rows.append({
                "instance": instance.name,
                "generation": generation,
                "mean_best_makespan": float(mean),
                "std_best_makespan": float(std),
                "n_runs": seeds,
            })

    with (output / "runs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(run_rows[0]))
        writer.writeheader()
        writer.writerows(run_rows)
    with (output / "convergence.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(convergence_rows[0]))
        writer.writeheader()
        writer.writerows(convergence_rows)

    summaries = []
    for name in sorted({row["instance"] for row in run_rows}):
        values = np.asarray([r["best_makespan"] for r in run_rows if r["instance"] == name])
        summaries.append({
            "instance": name,
            "n_runs": int(values.size),
            "mean": float(values.mean()),
            "median": float(np.median(values)),
            "std_sample": float(values.std(ddof=1)) if values.size > 1 else 0.0,
            "best": int(values.min()),
            "worst": int(values.max()),
        })
    metadata["summary"] = summaries
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summaries, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", nargs="+", type=Path, default=[
        Path("data/benchmarks/taillard/ta001.txt"),
        Path("data/benchmarks/taillard/ta011.txt"),
    ])
    parser.add_argument("--output", type=Path, default=Path("results/week2_baseline_v1"))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--wolves", type=int, default=30)
    parser.add_argument("--iterations", type=int, default=500)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be >= 1")
    run(args.instances, args.output, args.seeds, args.wolves, args.iterations)


if __name__ == "__main__":
    main()
