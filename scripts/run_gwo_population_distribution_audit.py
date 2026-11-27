"""Collect full GWO populations without changing optimizer decisions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import scipy
import sklearn

from scripts.gwo_pfs import gwo_pfs, decode_random_keys
from scripts.gwo_pfs_fuzzy import gwo_pfs_fuzzy
from scripts.gwo_pfs_surrogate import gwo_pfs_surrogate
from scripts.pfs_taillard import load_taillard_instance, makespan

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INSTANCE = ROOT / "data/benchmarks/taillard/ta111.txt"
DEFAULT_OUTPUT = ROOT / "results/gwo_population_distribution_audit_v1"
POPULATION_FIELDS = [
    "variant", "instance", "seed", "generation", "wolf_index",
    "permutation", "makespan", "is_generation_best", "generation_unique_permutations",
]
RUN_FIELDS = [
    "variant", "instance", "seed", "best_makespan", "exact_evaluations",
    "diagnostic_exact_labels", "surrogate_predictions", "runtime_seconds",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def append_rows(path: Path, fields: list[str], rows: list[dict]) -> None:
    if not rows:
        return
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)
        stream.flush()


def deduplicate(path: Path, keys: list[str]) -> None:
    rows = read_rows(path)
    if not rows:
        return
    unique = {}
    for row in rows:
        unique[tuple(row[key] for key in keys)] = row
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(unique.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=Path, default=DEFAULT_INSTANCE)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(5)))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--surrogate-dir", type=Path, default=ROOT / "results/week4_surrogate_v2")
    parser.add_argument("--optuna-config", type=Path, default=ROOT / "results/week3_optuna_v2/best_params.json")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    if not args.seeds or len(set(args.seeds)) != len(args.seeds):
        parser.error("seeds must be non-empty and unique")
    args.instance = args.instance.resolve()
    args.output = args.output.resolve()
    args.surrogate_dir = args.surrogate_dir.resolve()
    args.optuna_config = args.optuna_config.resolve()
    if args.top_k < 1 or args.top_k > 30:
        parser.error("--top-k must be in [1,30]")

    instance = load_taillard_instance(args.instance)
    if instance.name != "ta111":
        raise ValueError("the initial distribution audit is restricted to ta111")
    model_path = args.surrogate_dir / instance.name / "surrogate.joblib"
    metrics_path = args.surrogate_dir / instance.name / "metrics.json"
    if not model_path.is_file() or not metrics_path.is_file():
        raise FileNotFoundError(f"missing Week 4 surrogate artifacts for {instance.name}")
    model_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    if model_metrics["instance_sha256"] != sha256(args.instance):
        raise ValueError("Week 4 surrogate instance hash mismatch")
    model = joblib.load(model_path)

    config = json.loads(args.optuna_config.read_text(encoding="utf-8"))
    params = config["best_params"]
    optuna_wolves = int(params["n_wolves"])
    budget = int(config["evaluation_budget_per_run"])
    optuna_iterations = budget // optuna_wolves - 1
    if optuna_wolves * (optuna_iterations + 1) != budget:
        raise ValueError("Optuna parameters do not preserve the approved evaluation budget")

    args.output.mkdir(parents=True, exist_ok=True)
    populations_path = args.output / "populations.csv"
    runs_path = args.output / "runs.csv"
    completed = {
        (row["variant"], row["instance"], int(row["seed"]))
        for row in read_rows(runs_path)
    }
    variants = ("baseline", "optuna", "fuzzy", "surrogate")
    diagnostic_labels = 0
    for seed in args.seeds:
        for variant in variants:
            key = (variant, instance.name, seed)
            if key in completed:
                continue
            run_diagnostic_count = 0

            def observe(generation: int, positions: np.ndarray) -> None:
                nonlocal run_diagnostic_count
                permutations = [decode_random_keys(row) for row in positions]
                labels = [int(makespan(instance.processing_times, perm)) for perm in permutations]
                run_diagnostic_count += len(labels)
                unique_count = len({tuple(int(x) for x in perm) for perm in permutations})
                best = min(labels)
                rows = []
                for wolf_index, (permutation, label) in enumerate(zip(permutations, labels)):
                    rows.append({
                        "variant": variant, "instance": instance.name, "seed": seed,
                        "generation": generation, "wolf_index": wolf_index,
                        "permutation": " ".join(str(int(x)) for x in permutation),
                        "makespan": label, "is_generation_best": int(label == best),
                        "generation_unique_permutations": unique_count,
                    })
                append_rows(populations_path, POPULATION_FIELDS, rows)

            started = time.perf_counter()
            if variant in {"baseline", "optuna"}:
                kwargs = {"n_wolves": 30, "iterations": 500, "seed": seed}
                if variant == "optuna":
                    kwargs.update({
                        "n_wolves": optuna_wolves, "iterations": optuna_iterations,
                        "a_start": float(params["a_start"]),
                        "a_end": float(params["a_end"]),
                        "a_exponent": float(params["a_exponent"]),
                    })
                result = gwo_pfs(instance.processing_times, population_observer=observe, **kwargs)
                exact_evaluations = result.evaluations
                predictions = 0
            elif variant == "fuzzy":
                result = gwo_pfs_fuzzy(
                    instance.processing_times, n_wolves=30, iterations=500,
                    seed=seed, population_observer=observe,
                )
                exact_evaluations = result.evaluations
                predictions = 0
            else:
                result = gwo_pfs_surrogate(
                    instance.processing_times, model, n_wolves=30, iterations=500,
                    seed=seed, top_k=args.top_k, population_observer=observe,
                )
                exact_evaluations = result.exact_evaluations
                predictions = result.surrogate_predictions
            elapsed = time.perf_counter() - started
            append_rows(runs_path, RUN_FIELDS, [{
                "variant": variant, "instance": instance.name, "seed": seed,
                "best_makespan": int(result.best_fitness),
                "exact_evaluations": int(exact_evaluations),
                "diagnostic_exact_labels": run_diagnostic_count,
                "surrogate_predictions": int(predictions),
                "runtime_seconds": elapsed,
            }])
            diagnostic_labels += run_diagnostic_count
            completed.add(key)
            print(f"completed {variant} {instance.name} seed={seed}: "
                  f"best={result.best_fitness}, diagnostic_labels={run_diagnostic_count}")

    expected = {(v, instance.name, seed) for v in variants for seed in args.seeds}
    actual = {(r["variant"], r["instance"], int(r["seed"])) for r in read_rows(runs_path)}
    if actual != expected or len(read_rows(runs_path)) != len(expected):
        raise RuntimeError(f"incomplete or duplicated runs: missing={sorted(expected-actual)}")
    deduplicate(populations_path, ["variant", "instance", "seed", "generation", "wolf_index"])
    metadata = {
        "protocol": "gwo_population_distribution_audit_v1",
        "instance": {"name": instance.name, "path": str(args.instance.relative_to(ROOT)),
                     "sha256": sha256(args.instance), "jobs": instance.n_jobs,
                     "machines": instance.n_machines},
        "seeds": args.seeds, "variants": list(variants),
        "population_generations": "initial=-1; subsequent=0..iterations-1",
        "observer_contract": "receives a defensive copy; does not influence optimizer decisions",
        "diagnostic_labels_are_not_used_by_search": True,
        "diagnostic_exact_labels_total": sum(int(r["diagnostic_exact_labels"]) for r in read_rows(runs_path)),
        "surrogate_model_sha256": sha256(model_path),
        "optuna_config_sha256": sha256(args.optuna_config),
        "environment": {"python": platform.python_version(), "numpy": np.__version__,
                        "scipy": scipy.__version__, "sklearn": sklearn.__version__},
        "artifacts": {"populations": "populations.csv", "runs": "runs.csv"},
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"population rows: {len(read_rows(populations_path))}")
    print(f"diagnostic exact labels: {metadata['diagnostic_exact_labels_total']}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
