"""Paired Week 5 Fuzzy-GWO evaluation against frozen Week 2/3 PFSP baselines."""
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
from scipy.stats import wilcoxon

from scripts.gwo_pfs_fuzzy import gwo_pfs_fuzzy
from scripts.pfs_taillard import load_taillard_instance


DEFAULT_INSTANCES = [
    Path("data/benchmarks/taillard/ta001.txt"),
    Path("data/benchmarks/taillard/ta011.txt"),
]
BUDGET = 15030


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def paired_summary(fuzzy: list[float], reference: list[float]) -> dict:
    f, r = np.asarray(fuzzy, dtype=float), np.asarray(reference, dtype=float)
    diff = f - r
    if f.size != r.size or f.size == 0:
        raise ValueError("paired samples must have equal non-zero length")
    if np.all(diff == 0):
        statistic, pvalue = 0.0, 1.0
    else:
        result = wilcoxon(f, r, zero_method="wilcox", alternative="two-sided")
        statistic, pvalue = float(result.statistic), float(result.pvalue)
    return {
        "n_pairs": int(diff.size),
        "mean_difference_fuzzy_minus_reference": float(diff.mean()),
        "median_difference": float(np.median(diff)),
        "fuzzy_better": int(np.sum(diff < 0)),
        "equal": int(np.sum(diff == 0)),
        "fuzzy_worse": int(np.sum(diff > 0)),
        "wilcoxon_statistic": statistic,
        "wilcoxon_pvalue": pvalue,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", nargs="+", type=Path, default=DEFAULT_INSTANCES)
    parser.add_argument("--baseline", type=Path, default=Path("results/week2_baseline_v1/runs.csv"))
    parser.add_argument("--tuned", type=Path, default=Path("results/week3_optuna_v1/final_runs.csv"))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(30)))
    parser.add_argument("--wolves", type=int, default=30)
    parser.add_argument("--budget", type=int, default=BUDGET)
    parser.add_argument("--stagnation-window", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("results/week5_fuzzy_v1"))
    args = parser.parse_args()
    if args.wolves < 3 or args.budget <= 0 or args.budget % args.wolves:
        parser.error("--budget must be positive and divisible by --wolves (>=3)")
    if args.stagnation_window < 1 or not args.seeds:
        parser.error("stagnation window and seeds must be positive")
    iterations = args.budget // args.wolves - 1
    baseline = read_rows(args.baseline)
    tuned = read_rows(args.tuned)
    args.output.mkdir(parents=True, exist_ok=True)

    run_rows: list[dict] = []
    convergence_rows: list[dict] = []
    trace_rows: list[dict] = []
    comparisons: dict[str, dict] = {}
    instance_meta = []

    for path in args.instances:
        instance = load_taillard_instance(path)
        instance_meta.append({
            "name": instance.name, "jobs": instance.n_jobs, "machines": instance.n_machines,
            "sha256": sha256(path), "published_upper_bound": instance.upper_bound,
            "path": str(path),
        })
        def index(rows: list[dict[str, str]]) -> dict[int, float]:
            return {
                int(row["seed"]): float(row["best_makespan"])
                for row in rows if row["instance"] == instance.name
            }
        baseline_by_seed, tuned_by_seed = index(baseline), index(tuned)
        for label, mapping in (("baseline", baseline_by_seed), ("tuned", tuned_by_seed)):
            missing = sorted(set(args.seeds) - set(mapping))
            if missing:
                parser.error(f"{label} results missing seeds for {instance.name}: {missing}")

        values, histories = [], []
        for seed in args.seeds:
            started = time.perf_counter()
            result = gwo_pfs_fuzzy(
                instance.processing_times, n_wolves=args.wolves, iterations=iterations,
                seed=seed, stagnation_window=args.stagnation_window,
            )
            elapsed = time.perf_counter() - started
            if result.evaluations != args.budget:
                raise RuntimeError(f"expected {args.budget} evaluations, got {result.evaluations}")
            values.append(float(result.best_fitness))
            histories.append(result.convergence)
            run_rows.append({
                "instance": instance.name, "seed": seed, "best_makespan": result.best_fitness,
                "published_upper_bound": instance.upper_bound, "evaluations": result.evaluations,
                "runtime_seconds": elapsed,
                "best_permutation": " ".join(map(str, result.best_permutation.tolist())),
            })
            for row in result.trace:
                trace_rows.append({"instance": instance.name, "seed": seed, **row})

        matrix = np.vstack(histories)
        means = matrix.mean(axis=0)
        stds = matrix.std(axis=0, ddof=1) if len(args.seeds) > 1 else np.zeros(matrix.shape[1])
        for generation, (mean, std) in enumerate(zip(means, stds)):
            convergence_rows.append({
                "instance": instance.name, "generation": generation,
                "mean_best_makespan": float(mean), "std_best_makespan": float(std),
                "n_runs": len(args.seeds),
            })
        comparisons[instance.name] = {
            "fuzzy_vs_baseline": paired_summary(values, [baseline_by_seed[s] for s in args.seeds]),
            "fuzzy_vs_tuned": paired_summary(values, [tuned_by_seed[s] for s in args.seeds]),
            "fuzzy_summary": {
                "n": len(values), "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std_sample": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                "best": float(np.min(values)), "worst": float(np.max(values)),
                "mean_runtime_seconds": float(np.mean([
                    float(row["runtime_seconds"]) for row in run_rows
                    if row["instance"] == instance.name
                ])),
            },
        }

    for filename, rows in (
        ("fuzzy_runs.csv", run_rows),
        ("fuzzy_convergence.csv", convergence_rows),
        ("fuzzy_trace.csv", trace_rows),
    ):
        with (args.output / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    metadata = {
        "protocol": "week5_taillard_pfsp_fuzzy_gwo_v1",
        "objective": "makespan",
        "controller": "Mamdani min-max centroid",
        "inputs": {
            "diversity": "mean pairwise absolute distance in random-key population",
            "stagnation": "consecutive generations without global-best improvement / window, clipped to [0,1]",
        },
        "output": "exploration multiplier in [0.5,1.5] applied to linear a schedule, then clipped to [0,2]",
        "rule_matrix_rows_diversity_low_medium_high_columns_stagnation_low_medium_high": [
            ["medium", "high", "high"],
            ["low", "medium", "high"],
            ["low", "medium", "high"],
        ],
        "n_wolves": args.wolves, "iterations": iterations,
        "evaluation_budget_per_run": args.budget, "stagnation_window": args.stagnation_window,
        "seeds": args.seeds, "comparisons": comparisons, "instances": instance_meta,
        "baseline_file": str(args.baseline), "tuned_file": str(args.tuned),
        "python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
    }
    (args.output / "summary.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(comparisons, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
