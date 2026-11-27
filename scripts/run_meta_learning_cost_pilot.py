"""Short multi-size cost pilot for Meta-Learning expansion (1 seed, frozen configs)."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np

from scripts.gwo_pfs import gwo_pfs
from scripts.gwo_pfs_fuzzy import gwo_pfs_fuzzy
from scripts.gwo_pfs_surrogate import gwo_pfs_surrogate
from scripts.pfs_taillard import load_taillard_instance
from scripts.run_week4_surrogate import generate_dataset, build_model

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results/meta_learning_cost_pilot_v3"
# One instance per size group already in the 36-set.
DEFAULT_INSTANCES = [
    "ta001", "ta011", "ta021", "ta031", "ta041", "ta051",
    "ta061", "ta071", "ta081", "ta091", "ta101", "ta111",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_surrogate(instance_path: Path, out_dir: Path, samples: int, seed: int):
    instance = load_taillard_instance(instance_path)
    target = out_dir / "surrogates" / instance.name
    model_path = target / "surrogate.joblib"
    metrics_path = target / "metrics.json"
    if model_path.is_file() and metrics_path.is_file():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        if metrics.get("instance_sha256") == sha256(instance_path):
            return joblib.load(model_path), metrics
    target.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    features, labels, unique, _ = generate_dataset(instance.processing_times, samples, seed)
    train_n = max(int(0.8 * len(labels)), 1)
    model = build_model(seed)
    model.fit(features[:train_n], labels[:train_n])
    train_s = time.perf_counter() - started
    metrics = {
        "instance": instance.name,
        "instance_sha256": sha256(instance_path),
        "jobs": instance.n_jobs,
        "machines": instance.n_machines,
        "samples": int(len(labels)),
        "unique_permutations": int(unique),
        "train_samples": train_n,
        "training_seconds": train_s,
        "protocol": "week4_taillard_pfsp_surrogate_v2_cost_pilot_v3",
        "model_sha256_after_save": None,
    }
    joblib.dump(model, model_path)
    metrics["model_sha256_after_save"] = sha256(model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return model, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", nargs="+", default=DEFAULT_INSTANCES)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--surrogate-samples", type=int, default=500)
    parser.add_argument(
        "--optuna-config",
        type=Path,
        default=ROOT / "results/week3_optuna_v2/best_params.json",
    )
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    runs_path = out / "runs.csv"
    fields = [
        "variant", "instance", "jobs", "machines", "seed",
        "best_makespan", "exact_evaluations", "surrogate_predictions",
        "runtime_seconds", "surrogate_prep_seconds",
    ]
    done = set()
    if runs_path.exists():
        with runs_path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                done.add((row["variant"], row["instance"], int(row["seed"])))

    optuna = json.loads(args.optuna_config.read_text(encoding="utf-8"))
    params = optuna["best_params"]
    optuna_wolves = int(params["n_wolves"])
    budget = int(optuna["evaluation_budget_per_run"])
    optuna_iterations = budget // optuna_wolves - 1

    for name in args.instances:
        path = ROOT / "data/benchmarks/taillard" / f"{name}.txt"
        instance = load_taillard_instance(path)
        model, metrics = ensure_surrogate(path, out, args.surrogate_samples, 20261127)
        prep = float(metrics["training_seconds"])
        variants = (
            ("baseline", lambda: gwo_pfs(instance.processing_times, n_wolves=30, iterations=500, seed=args.seed)),
            ("optuna", lambda: gwo_pfs(
                instance.processing_times,
                n_wolves=optuna_wolves,
                iterations=optuna_iterations,
                seed=args.seed,
                a_start=float(params["a_start"]),
                a_end=float(params["a_end"]),
                a_exponent=float(params["a_exponent"]),
            )),
            ("fuzzy", lambda: gwo_pfs_fuzzy(instance.processing_times, n_wolves=30, iterations=500, seed=args.seed)),
            ("surrogate", lambda: gwo_pfs_surrogate(
                instance.processing_times, model, n_wolves=30, iterations=500, seed=args.seed, top_k=3,
            )),
        )
        for variant, runner in variants:
            key = (variant, instance.name, args.seed)
            if key in done:
                print(f"skip {key}")
                continue
            started = time.perf_counter()
            result = runner()
            elapsed = time.perf_counter() - started
            if variant == "surrogate":
                exact = int(result.exact_evaluations)
                preds = int(result.surrogate_predictions)
                best = int(result.best_fitness)
            else:
                exact = int(result.evaluations)
                preds = 0
                best = int(result.best_fitness)
            row = {
                "variant": variant,
                "instance": instance.name,
                "jobs": instance.n_jobs,
                "machines": instance.n_machines,
                "seed": args.seed,
                "best_makespan": best,
                "exact_evaluations": exact,
                "surrogate_predictions": preds,
                "runtime_seconds": elapsed,
                "surrogate_prep_seconds": prep if variant == "surrogate" else 0.0,
            }
            new_file = not runs_path.exists() or runs_path.stat().st_size == 0
            with runs_path.open("a", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                if new_file:
                    writer.writeheader()
                writer.writerow(row)
            print(
                f"done {variant} {instance.name}: best={best} "
                f"t={elapsed:.2f}s prep={row['surrogate_prep_seconds']:.2f}s"
            )

    # Cost projection
    with runs_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    by_size = {}
    for row in rows:
        key = (int(row["jobs"]), int(row["machines"]))
        by_size.setdefault(key, []).append(row)
    projection = []
    for (jobs, machines), group in sorted(by_size.items()):
        mean_per_variant = {
            v: float(np.mean([float(r["runtime_seconds"]) for r in group if r["variant"] == v]))
            for v in ("baseline", "optuna", "fuzzy", "surrogate")
        }
        prep = float(np.mean([
            float(r["surrogate_prep_seconds"]) for r in group if r["variant"] == "surrogate"
        ]))
        four = sum(mean_per_variant.values())
        projection.append({
            "jobs": jobs,
            "machines": machines,
            "seconds_four_variants_one_seed": four,
            "surrogate_prep_seconds": prep,
            "estimate_3_instances_x_3_seeds_seconds": 3 * 3 * four,
            "estimate_3_instances_x_3_seeds_hours": 3 * 3 * four / 3600.0,
            **{f"mean_seconds_{k}": v for k, v in mean_per_variant.items()},
        })
    total_36_3seeds = sum(p["estimate_3_instances_x_3_seeds_seconds"] for p in projection)
    summary = {
        "protocol": "meta_learning_cost_pilot_v3",
        "seed": args.seed,
        "surrogate_samples": args.surrogate_samples,
        "instances_measured": args.instances,
        "projection_by_size_group": projection,
        "estimate_36_instances_3_seeds_four_variants_hours": total_36_3seeds / 3600.0,
        "estimate_36_instances_10_seeds_four_variants_hours": total_36_3seeds / 3600.0 * (10 / 3),
        "notes": [
            "Surrogate models here use 500 LHS samples for cost only; confirmatory meta-base should use Week4 sample policy.",
            "Estimates assume three instances per size group scale like the measured representative.",
        ],
    }
    (out / "cost_projection.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "hours_36x3seeds": summary["estimate_36_instances_3_seeds_four_variants_hours"],
        "hours_36x10seeds": summary["estimate_36_instances_10_seeds_four_variants_hours"],
    }, indent=2))


if __name__ == "__main__":
    main()
