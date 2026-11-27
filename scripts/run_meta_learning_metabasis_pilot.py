"""Meta-base pilot: 36 Taillard instances × 4 variants × 3 seeds (paired)."""
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
from scripts.run_week4_surrogate import build_model, generate_dataset

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results/meta_learning_metabasis_pilot_v1"
DEFAULT_INSTANCES = [
    "ta001", "ta002", "ta003",
    "ta011", "ta012", "ta013",
    "ta021", "ta022", "ta023",
    "ta031", "ta032", "ta033",
    "ta041", "ta042", "ta043",
    "ta051", "ta052", "ta053",
    "ta061", "ta062", "ta063",
    "ta071", "ta072", "ta073",
    "ta081", "ta082", "ta083",
    "ta091", "ta092", "ta093",
    "ta101", "ta102", "ta103",
    "ta111", "ta112", "ta113",
]
RUN_FIELDS = [
    "variant", "instance", "jobs", "machines", "seed",
    "best_makespan", "upper_bound", "exact_evaluations",
    "surrogate_predictions", "runtime_seconds", "surrogate_prep_seconds",
    "instance_sha256", "model_sha256",
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
    inst_hash = sha256(instance_path)
    if model_path.is_file() and metrics_path.is_file():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        if (
            metrics.get("instance_sha256") == inst_hash
            and int(metrics.get("sample_count_requested", -1)) == samples
        ):
            return joblib.load(model_path), metrics, sha256(model_path)
    target.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    features, labels, unique, _ = generate_dataset(instance.processing_times, samples, seed)
    train_n = max(int(0.8 * len(labels)), 1)
    model = build_model(seed)
    model.fit(features[:train_n], labels[:train_n])
    train_s = time.perf_counter() - started
    joblib.dump(model, model_path)
    model_hash = sha256(model_path)
    metrics = {
        "protocol": "week4_taillard_pfsp_surrogate_v2_metabasis_pilot_v1",
        "instance": instance.name,
        "instance_sha256": inst_hash,
        "jobs": instance.n_jobs,
        "machines": instance.n_machines,
        "sample_count_requested": samples,
        "unique_permutations": int(unique),
        "train_samples": train_n,
        "training_seconds": train_s,
        "model_sha256": model_hash,
    }
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return model, metrics, model_hash


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", nargs="+", default=DEFAULT_INSTANCES)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--surrogate-samples", type=int, default=2000)
    parser.add_argument(
        "--optuna-config",
        type=Path,
        default=ROOT / "results/week3_optuna_v2/best_params.json",
    )
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds):
        raise SystemExit("seeds must be unique")

    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    runs_path = out / "runs.csv"
    done = set()
    if runs_path.exists() and runs_path.stat().st_size > 0:
        with runs_path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                done.add((row["variant"], row["instance"], int(row["seed"])))

    optuna = json.loads(args.optuna_config.read_text(encoding="utf-8"))
    params = optuna["best_params"]
    optuna_wolves = int(params["n_wolves"])
    budget = int(optuna["evaluation_budget_per_run"])
    optuna_iterations = budget // optuna_wolves - 1
    expected = len(args.instances) * len(args.seeds) * 4

    for name in args.instances:
        path = (ROOT / "data/benchmarks/taillard" / f"{name}.txt").resolve()
        instance = load_taillard_instance(path)
        inst_hash = sha256(path)
        model, metrics, model_hash = ensure_surrogate(
            path, out, args.surrogate_samples, 20261127
        )
        prep = float(metrics["training_seconds"])
        for seed in args.seeds:
            jobs = (
                ("baseline", lambda s=seed: gwo_pfs(
                    instance.processing_times, n_wolves=30, iterations=500, seed=s
                )),
                ("optuna", lambda s=seed: gwo_pfs(
                    instance.processing_times,
                    n_wolves=optuna_wolves,
                    iterations=optuna_iterations,
                    seed=s,
                    a_start=float(params["a_start"]),
                    a_end=float(params["a_end"]),
                    a_exponent=float(params["a_exponent"]),
                )),
                ("fuzzy", lambda s=seed: gwo_pfs_fuzzy(
                    instance.processing_times, n_wolves=30, iterations=500, seed=s
                )),
                ("surrogate", lambda s=seed: gwo_pfs_surrogate(
                    instance.processing_times, model, n_wolves=30, iterations=500,
                    seed=s, top_k=3,
                )),
            )
            for variant, runner in jobs:
                key = (variant, instance.name, seed)
                if key in done:
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
                    "seed": seed,
                    "best_makespan": best,
                    "upper_bound": instance.upper_bound if instance.upper_bound is not None else "",
                    "exact_evaluations": exact,
                    "surrogate_predictions": preds,
                    "runtime_seconds": elapsed,
                    "surrogate_prep_seconds": prep if variant == "surrogate" else 0.0,
                    "instance_sha256": inst_hash,
                    "model_sha256": model_hash if variant == "surrogate" else "",
                }
                new_file = not runs_path.exists() or runs_path.stat().st_size == 0
                with runs_path.open("a", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=RUN_FIELDS)
                    if new_file:
                        writer.writeheader()
                    writer.writerow(row)
                    stream.flush()
                done.add(key)
                print(
                    f"[{len(done)}/{expected}] {variant} {instance.name} seed={seed} "
                    f"best={best} t={elapsed:.1f}s",
                    flush=True,
                )

    metadata = {
        "protocol": "meta_learning_metabasis_pilot_v1",
        "instances": args.instances,
        "seeds": args.seeds,
        "variants": ["baseline", "optuna", "fuzzy", "surrogate"],
        "surrogate_samples": args.surrogate_samples,
        "optuna_config_sha256": sha256(args.optuna_config.resolve()),
        "n_runs_expected": expected,
        "n_runs_completed": len(done),
        "surrogate_freeze": "docs/decisions/2026-11-27-surrogate-variant-freeze.md",
        "feature_freeze": "docs/decisions/2026-11-27-meta-feature-extractor-freeze.md",
        "unit": "instance; seeds estimate noise only",
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"completed_runs={len(done)}/{expected} output={out}")


if __name__ == "__main__":
    main()
