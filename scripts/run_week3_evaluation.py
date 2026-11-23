"""Evaluate frozen Week 3 Optuna parameters on held-out seeds and compare paired."""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, sys, time
from pathlib import Path
import numpy as np
from scripts.gwo_pfs import gwo_pfs
from scripts.pfs_taillard import load_taillard_instance

BUDGET = 15030
DEFAULT_INSTANCES = [Path("data/benchmarks/taillard/ta001.txt"), Path("data/benchmarks/taillard/ta011.txt")]

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def describe(values):
    a = np.asarray(values, dtype=float)
    return {"n": int(a.size), "mean": float(a.mean()), "median": float(np.median(a)),
            "std_sample": float(a.std(ddof=1)) if a.size > 1 else 0.0,
            "best": float(a.min()), "worst": float(a.max())}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("results/week3_optuna_v2/best_params.json"))
    parser.add_argument("--baseline", type=Path, default=Path("results/week2_baseline_v2/runs.csv"))
    parser.add_argument("--instances", nargs="+", type=Path, default=DEFAULT_INSTANCES)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(30)))
    parser.add_argument("--output", type=Path, default=Path("results/week3_optuna_v2"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    params = config["best_params"]
    wolves = int(params["n_wolves"])
    iterations = BUDGET // wolves - 1
    if wolves * (iterations + 1) != BUDGET:
        parser.error("best configuration does not preserve the evaluation budget")
    baseline_rows = read_csv(args.baseline)
    args.output.mkdir(parents=True, exist_ok=True)
    run_rows, convergence_rows, comparisons = [], [], []

    for path in args.instances:
        instance = load_taillard_instance(path)
        base = {int(r["seed"]): float(r["best_makespan"]) for r in baseline_rows if r["instance"] == instance.name}
        missing = sorted(set(args.seeds) - set(base))
        if missing:
            parser.error(f"baseline missing seeds for {instance.name}: {missing}")
        histories, tuned_values, diffs = [], [], []
        for seed in args.seeds:
            start = time.perf_counter()
            result = gwo_pfs(
                instance.processing_times, n_wolves=wolves, iterations=iterations, seed=seed,
                a_start=float(params["a_start"]), a_end=float(params["a_end"]),
                a_exponent=float(params["a_exponent"]),
            )
            elapsed = time.perf_counter() - start
            if result.evaluations != BUDGET:
                raise RuntimeError("unexpected evaluation count")
            histories.append(result.convergence)
            tuned_values.append(float(result.best_fitness))
            diff = float(result.best_fitness) - base[seed]
            diffs.append(diff)
            run_rows.append({
                "instance": instance.name, "jobs": instance.n_jobs, "machines": instance.n_machines,
                "seed": seed, "best_makespan": result.best_fitness,
                "baseline_makespan_same_seed": base[seed],
                "paired_difference_tuned_minus_baseline": diff,
                "published_upper_bound": instance.upper_bound,
                "gap_to_published_ub_pct": 100.0 * (result.best_fitness - instance.upper_bound) / instance.upper_bound,
                "evaluations": result.evaluations, "runtime_seconds": elapsed,
                "best_permutation": " ".join(map(str, result.best_permutation.tolist())),
            })
        matrix = np.vstack(histories)
        means = matrix.mean(axis=0)
        stds = matrix.std(axis=0, ddof=1) if len(args.seeds) > 1 else np.zeros(matrix.shape[1])
        for generation, (mean, std) in enumerate(zip(means, stds)):
            convergence_rows.append({"instance": instance.name, "generation": generation,
                "mean_best_makespan": float(mean), "std_best_makespan": float(std), "n_runs": len(args.seeds)})
        d = np.asarray(diffs)
        comparisons.append({
            "instance": instance.name, "baseline": describe([base[s] for s in args.seeds]),
            "tuned": describe(tuned_values),
            "paired_difference_tuned_minus_baseline": {
                "mean": float(d.mean()), "median": float(np.median(d)),
                "tuned_better": int(np.sum(d < 0)), "equal": int(np.sum(d == 0)),
                "tuned_worse": int(np.sum(d > 0)),
            },
        })

    for filename, rows in [("final_runs.csv", run_rows), ("final_convergence.csv", convergence_rows)]:
        with (args.output / filename).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    metadata = {
        "protocol": "week3_pfsp_optuna_evaluation_v2", "objective": "makespan",
        "frozen_best_params": params, "solver_version": "gwo_pfs_population_replacement_v2", "iterations_derived": iterations,
        "evaluation_budget_per_run": BUDGET, "seeds": args.seeds,
        "baseline_file": str(args.baseline), "comparison": comparisons,
        "python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
        "instances": [{"name": load_taillard_instance(p).name, "sha256": sha256(p), "path": str(p)} for p in args.instances],
    }
    (args.output / "evaluation_summary.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
