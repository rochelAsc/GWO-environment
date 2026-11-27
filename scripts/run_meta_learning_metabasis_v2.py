"""Meta-base v2 runner: development instances from the frozen split manifesto.

Protocol: meta_learning_metabasis_v2. Does not overwrite metabasis_pilot_v1.
Default scope: development + stage=60 (12 new instances). Pilot reuse is separate.
"""
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
DEFAULT_OUT = ROOT / "results/meta_learning_metabasis_v2"
DEFAULT_SPLIT = ROOT / "experiments/meta_learning/data/metabasis_v2/split_manifest.csv"
PROTOCOL = "meta_learning_metabasis_v2"
RUN_FIELDS = [
    "variant", "instance", "jobs", "machines", "seed",
    "best_makespan", "upper_bound", "exact_evaluations",
    "surrogate_predictions", "runtime_seconds", "surrogate_prep_seconds",
    "instance_sha256", "model_sha256", "source", "partition", "stage",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_split_instances(
    split_path: Path,
    *,
    partitions: set[str],
    stages: set[str],
) -> list[dict[str, str]]:
    with split_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    selected = [
        row for row in rows
        if row["partition"] in partitions and str(row["stage"]) in stages
    ]
    if not selected:
        raise SystemExit("no instances matched partition/stage filters")
    return selected


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
            and metrics.get("protocol", "").endswith("metabasis_v2")
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
        "protocol": "week4_taillard_pfsp_surrogate_v2_metabasis_v2",
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
    parser.add_argument("--split", type=Path, default=DEFAULT_SPLIT)
    parser.add_argument(
        "--partitions",
        nargs="+",
        default=["development"],
        help="Split partitions to run (default: development only).",
    )
    parser.add_argument(
        "--stages",
        nargs="+",
        default=["60"],
        help="Stages to run (default: 60). Use 60 120 for full expansion.",
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--surrogate-samples", type=int, default=2000)
    parser.add_argument(
        "--optuna-config",
        type=Path,
        default=ROOT / "results/week3_optuna_v2/best_params.json",
    )
    parser.add_argument(
        "--allow-holdout",
        action="store_true",
        help="Required if partitions include holdout. Keep sealed until confirmatory eval.",
    )
    args = parser.parse_args()

    if len(set(args.seeds)) != len(args.seeds):
        raise SystemExit("seeds must be unique")
    out = args.output.resolve()
    if "metabasis_pilot_v1" in str(out).replace("\\", "/"):
        raise SystemExit("refuse to write v2 runs into metabasis_pilot_v1 paths")
    if "holdout" in args.partitions and not args.allow_holdout:
        raise SystemExit("holdout partition requires --allow-holdout")

    selected = load_split_instances(
        args.split,
        partitions=set(args.partitions),
        stages={str(s) for s in args.stages},
    )
    # Exclude pilot_v1 stage from default new runs unless explicitly requested.
    selected = [r for r in selected if str(r["stage"]) != "pilot_v1"]
    if not selected:
        raise SystemExit("after excluding pilot_v1, no instances remain to run")

    out.mkdir(parents=True, exist_ok=True)
    runs_path = out / "runs.csv"
    done: set[tuple[str, str, int]] = set()
    if runs_path.exists() and runs_path.stat().st_size > 0:
        with runs_path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                done.add((row["variant"], row["instance"], int(row["seed"])))

    optuna = json.loads(args.optuna_config.read_text(encoding="utf-8"))
    params = optuna["best_params"]
    optuna_wolves = int(params["n_wolves"])
    budget = int(optuna["evaluation_budget_per_run"])
    optuna_iterations = budget // optuna_wolves - 1
    expected = len(selected) * len(args.seeds) * 4

    for meta in selected:
        name = meta["instance"]
        path = (ROOT / meta["path"]).resolve()
        if not path.is_file():
            raise SystemExit(f"missing instance file: {path}")
        inst_hash = sha256(path)
        if inst_hash != meta["sha256"]:
            raise SystemExit(
                f"instance hash mismatch for {name}: split={meta['sha256']} file={inst_hash}"
            )
        instance = load_taillard_instance(path)
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
                    "source": "metabasis_v2_new",
                    "partition": meta["partition"],
                    "stage": meta["stage"],
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
        "protocol": PROTOCOL,
        "split_manifest": str(args.split.as_posix()),
        "split_sha256": sha256(args.split.resolve()),
        "partitions": args.partitions,
        "stages": [str(s) for s in args.stages],
        "instances": [r["instance"] for r in selected],
        "seeds": args.seeds,
        "variants": ["baseline", "optuna", "fuzzy", "surrogate"],
        "surrogate_samples": args.surrogate_samples,
        "optuna_config_sha256": sha256(args.optuna_config.resolve()),
        "n_runs_expected": expected,
        "n_runs_completed": len(done),
        "surrogate_freeze": "docs/decisions/2026-11-27-surrogate-variant-freeze.md",
        "feature_freeze": "docs/decisions/2026-11-27-meta-feature-extractor-freeze.md",
        "expansion_decision": "docs/decisions/2026-11-27-meta-learning-expansion-v2.md",
        "unit": "instance; seeds estimate noise only",
        "numpy_version": np.__version__,
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"completed_runs={len(done)}/{expected} output={out}")


if __name__ == "__main__":
    main()
