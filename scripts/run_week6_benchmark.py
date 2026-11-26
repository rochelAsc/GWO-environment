"""Run the approved Week 6 four-variant PFSP/Taillard benchmark."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from pathlib import Path
from itertools import combinations

import joblib
import numpy as np
import scipy
from scipy.stats import friedmanchisquare, wilcoxon

from scripts.gwo_pfs import gwo_pfs
from scripts.gwo_pfs_fuzzy import gwo_pfs_fuzzy
from scripts.gwo_pfs_surrogate import gwo_pfs_surrogate
from scripts.pfs_taillard import load_taillard_instance


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INSTANCES = [
    ROOT / "data/benchmarks/taillard/ta001.txt",
    ROOT / "data/benchmarks/taillard/ta011.txt",
]
VARIANTS = ("baseline", "optuna", "surrogate", "fuzzy")
RUN_FIELDS = [
    "variant", "instance", "seed", "best_makespan", "published_upper_bound",
    "hit_upper_bound", "evaluations", "surrogate_predictions", "inference_batches",
    "exact_evaluation_seconds", "surrogate_seconds", "runtime_seconds",
    "best_permutation",
]
CONVERGENCE_FIELDS = ["variant", "instance", "seed", "generation", "best_makespan"]
SURROGATE_TRACE_FIELDS = [
    "instance", "seed", "iteration", "candidate_index", "predicted_rank",
    "predicted_makespan", "exact_makespan", "selected_duplicate_count_generation",
]
FUZZY_TRACE_FIELDS = [
    "instance", "seed", "iteration", "diversity", "stagnation",
    "fuzzy_scale", "a", "best_fitness", "improved",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def append_rows(path: Path, fields: list[str], rows: list[dict]) -> None:
    if not rows:
        return
    needs_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        if needs_header:
            writer.writeheader()
        writer.writerows(rows)
        stream.flush()



def deduplicate_csv(path: Path, key_fields: list[str]) -> None:
    rows = read_csv(path)
    if not rows:
        return
    latest = {}
    for row in rows:
        latest[tuple(row[field] for field in key_fields)] = row
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(latest.values())

def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, returned in original order."""
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    m = len(values)
    for rank, index in enumerate(order):
        candidate = min(1.0, (m - rank) * values[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted.tolist()


def describe(values: list[float]) -> dict:
    array = np.asarray(values, dtype=float)
    return {
        "n": int(array.size),
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "std_sample": float(array.std(ddof=1)) if array.size > 1 else 0.0,
        "minimum": float(array.min()),
        "maximum": float(array.max()),
        "upper_bound_hits": int(np.sum(array <= 0)),  # replaced by caller
    }


def paired_test(left: np.ndarray, right: np.ndarray) -> tuple[float, float]:
    differences = left - right
    if np.all(differences == 0):
        return 0.0, 1.0
    result = wilcoxon(left, right, alternative="two-sided", zero_method="wilcox")
    return float(result.statistic), float(result.pvalue)


def write_analysis(output: Path, run_rows: list[dict[str, str]], instances: list[dict]) -> dict:
    analysis: dict[str, dict] = {}
    pair_rows: list[dict] = []
    convergence = read_csv(output / "convergence.csv")
    summary_rows: list[dict] = []

    for instance in instances:
        name = instance["name"]
        per_variant = {}
        values_by_variant = {}
        for variant in VARIANTS:
            selected = [
                row for row in run_rows
                if row["instance"] == name and row["variant"] == variant
            ]
            selected.sort(key=lambda row: int(row["seed"]))
            values = np.asarray([float(row["best_makespan"]) for row in selected])
            values_by_variant[variant] = values
            upper = float(instance["upper_bound"])
            stats = describe(values.tolist())
            stats["upper_bound_hits"] = int(sum(float(row["best_makespan"]) <= upper for row in selected))
            stats["mean_runtime_seconds"] = float(np.mean([float(row["runtime_seconds"]) for row in selected]))
            stats["median_runtime_seconds"] = float(np.median([float(row["runtime_seconds"]) for row in selected]))
            stats["mean_exact_evaluation_seconds"] = float(np.mean([
                float(row["exact_evaluation_seconds"]) for row in selected
            ]))
            stats["mean_surrogate_seconds"] = float(np.mean([
                float(row["surrogate_seconds"]) for row in selected
            ]))
            stats["exact_evaluations_per_run"] = sorted({
                int(row["evaluations"]) for row in selected
            })
            stats["surrogate_predictions_per_run"] = sorted({
                int(row["surrogate_predictions"]) for row in selected
            })
            per_variant[variant] = stats
            summary_rows.append({"instance": name, "variant": variant, **stats})

        arrays = [values_by_variant[v] for v in VARIANTS]
        if len(arrays[0]) >= 3:
            try:
                friedman = friedmanchisquare(*arrays)
                friedman_result = {
                    "statistic": float(friedman.statistic),
                    "pvalue": float(friedman.pvalue),
                }
            except ValueError:
                friedman_result = {"statistic": None, "pvalue": None}
        else:
            friedman_result = {"statistic": None, "pvalue": None}

        comparisons = []
        raw_p = []
        for left_name, right_name in combinations(VARIANTS, 2):
            left = values_by_variant[left_name]
            right = values_by_variant[right_name]
            if len(left) != len(right) or len(left) == 0:
                raise RuntimeError(f"unpaired or missing seed values for {name}: {left_name}/{right_name}")
            statistic, pvalue = paired_test(left, right)
            diff = left - right
            item = {
                "left": left_name,
                "right": right_name,
                "n_pairs": int(len(diff)),
                "mean_difference_left_minus_right": float(diff.mean()),
                "median_difference_left_minus_right": float(np.median(diff)),
                "left_better": int(np.sum(diff < 0)),
                "equal": int(np.sum(diff == 0)),
                "left_worse": int(np.sum(diff > 0)),
                "wilcoxon_statistic": statistic,
                "pvalue_raw": pvalue,
            }
            comparisons.append(item)
            raw_p.append(pvalue)
        adjusted = holm_adjust(raw_p)
        for item, p_adjusted in zip(comparisons, adjusted):
            item["pvalue_holm"] = p_adjusted
            pair_rows.append({"instance": name, **item})

        analysis[name] = {
            "n_seeds": int(len(arrays[0])),
            "variants": per_variant,
            "friedman": friedman_result,
            "pairwise_wilcoxon_holm": comparisons,
        }

    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = list(summary_rows[0]) if summary_rows else []
        writer = csv.DictWriter(stream, fieldnames=fields)
        if fields:
            writer.writeheader()
            writer.writerows(summary_rows)
    with (output / "pairwise_statistics.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = list(pair_rows[0]) if pair_rows else []
        writer = csv.DictWriter(stream, fieldnames=fields)
        if fields:
            writer.writeheader()
            writer.writerows(pair_rows)

    # Aggregate the raw per-run convergence without discarding seed-level data.
    grouped: dict[tuple[str, str, int], list[float]] = {}
    for row in convergence:
        key = (row["variant"], row["instance"], int(row["generation"]))
        grouped.setdefault(key, []).append(float(row["best_makespan"]))
    aggregate_rows = []
    for (variant, instance, generation), values in sorted(grouped.items()):
        arr = np.asarray(values, dtype=float)
        aggregate_rows.append({
            "variant": variant, "instance": instance, "generation": generation,
            "n_runs": len(arr), "mean_best_makespan": float(arr.mean()),
            "std_best_makespan": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
        })
    with (output / "convergence_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["variant", "instance", "generation", "n_runs",
                  "mean_best_makespan", "std_best_makespan"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(aggregate_rows)

    return analysis


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", nargs="+", type=Path, default=DEFAULT_INSTANCES)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(30)))
    parser.add_argument("--optuna-config", type=Path, default=ROOT / "results/week3_optuna_v2/best_params.json")
    parser.add_argument("--surrogate-dir", type=Path, default=ROOT / "results/week4_surrogate_v2")
    parser.add_argument("--output", type=Path, default=ROOT / "results/week6_benchmark_v1")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    if not args.seeds or len(set(args.seeds)) != len(args.seeds):
        parser.error("seeds must be non-empty and unique")
    if args.top_k < 1 or args.top_k > 30:
        parser.error("--top-k must be in [1,30]")

    args.optuna_config = args.optuna_config.resolve()
    args.surrogate_dir = args.surrogate_dir.resolve()
    args.output = args.output.resolve()
    args.instances = [path.resolve() for path in args.instances]
    config = json.loads(args.optuna_config.read_text(encoding="utf-8"))
    params = config["best_params"]
    wolves_optuna = int(params["n_wolves"])
    budget = int(config["evaluation_budget_per_run"])
    optuna_iterations = budget // wolves_optuna - 1
    if wolves_optuna * (optuna_iterations + 1) != budget:
        parser.error("Optuna parameters do not preserve the approved exact-evaluation budget")

    args.output.mkdir(parents=True, exist_ok=True)
    runs_path = args.output / "runs.csv"
    convergence_path = args.output / "convergence.csv"
    surrogate_trace_path = args.output / "surrogate_trace.csv"
    fuzzy_trace_path = args.output / "fuzzy_trace.csv"
    existing_rows = read_csv(runs_path)
    completed = {
        (row["variant"], row["instance"], int(row["seed"])) for row in existing_rows
    }

    instance_metadata = []
    model_metadata = {}
    model_cache = {}
    loaded_instances = []
    for path in args.instances:
        instance = load_taillard_instance(path)
        if instance.name not in {"ta001", "ta011"}:
            raise ValueError(f"unexpected instance outside approved protocol: {instance.name}")
        model_path = args.surrogate_dir / instance.name / "surrogate.joblib"
        metrics_path = args.surrogate_dir / instance.name / "metrics.json"
        if not model_path.is_file() or not metrics_path.is_file():
            raise FileNotFoundError(f"missing Week 4 surrogate artifacts for {instance.name}")
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        if metrics["instance_sha256"] != sha256(path):
            raise ValueError(f"Week 4 model instance hash mismatch for {instance.name}")
        model_cache[instance.name] = joblib.load(model_path)
        model_metadata[instance.name] = {
            "path": str(model_path.relative_to(ROOT)),
            "sha256": sha256(model_path),
            "metrics_path": str(metrics_path.relative_to(ROOT)),
            "dataset_generation_and_exact_labels_seconds": metrics["timing"]["dataset_generation_and_exact_labels_seconds"],
            "training_seconds": metrics["timing"]["training_seconds"],
            "exact_training_labels": int(metrics["unique_permutations"]),
            "test_metrics": metrics["metrics"]["test"],
        }
        instance_metadata.append({
            "name": instance.name, "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path), "jobs": instance.n_jobs,
            "machines": instance.n_machines, "upper_bound": instance.upper_bound,
        })
        loaded_instances.append((instance, path))

    for instance, path in loaded_instances:
        name = instance.name
        for seed in args.seeds:
            for variant in VARIANTS:
                key = (variant, name, seed)
                if key in completed:
                    continue
                started = time.perf_counter()
                exact_seconds = 0.0
                surrogate_seconds = 0.0
                predictions = 0
                batches = 0
                fuzzy_rows = []
                surrogate_rows = []

                if variant == "baseline":
                    result = gwo_pfs(
                        instance.processing_times, n_wolves=30, iterations=500, seed=seed,
                    )
                    best, permutation, convergence = result.best_fitness, result.best_permutation, result.convergence
                    evaluations, exact_seconds = result.evaluations, result.exact_evaluation_seconds
                elif variant == "optuna":
                    result = gwo_pfs(
                        instance.processing_times, n_wolves=wolves_optuna,
                        iterations=optuna_iterations, seed=seed,
                        a_start=float(params["a_start"]), a_end=float(params["a_end"]),
                        a_exponent=float(params["a_exponent"]),
                    )
                    best, permutation, convergence = result.best_fitness, result.best_permutation, result.convergence
                    evaluations, exact_seconds = result.evaluations, result.exact_evaluation_seconds
                elif variant == "fuzzy":
                    result = gwo_pfs_fuzzy(
                        instance.processing_times, n_wolves=30, iterations=500, seed=seed,
                    )
                    best, permutation, convergence = result.best_fitness, result.best_permutation, result.convergence
                    evaluations, exact_seconds = result.evaluations, result.exact_evaluation_seconds
                    fuzzy_rows = [
                        {"instance": name, "seed": seed, **row} for row in result.trace
                    ]
                else:
                    result = gwo_pfs_surrogate(
                        instance.processing_times, model_cache[name],
                        n_wolves=30, iterations=500, seed=seed, top_k=args.top_k,
                    )
                    best, permutation, convergence = result.best_fitness, result.best_permutation, result.convergence
                    evaluations = result.exact_evaluations
                    exact_seconds = result.exact_evaluation_seconds
                    surrogate_seconds = result.surrogate_seconds
                    predictions = result.surrogate_predictions
                    batches = result.inference_batches
                    surrogate_rows = [
                        {"instance": name, "seed": seed, **row} for row in result.trace
                    ]

                wall_seconds = time.perf_counter() - started
                expected_evaluations = (
                    1530 if variant == "surrogate"
                    else (wolves_optuna * (optuna_iterations + 1) if variant == "optuna" else 15030)
                )
                expected_predictions = 15000 if variant == "surrogate" else 0
                if evaluations != expected_evaluations or predictions != expected_predictions:
                    raise RuntimeError(
                        f"{variant}/{name}/seed={seed}: budget mismatch "
                        f"exact={evaluations}, predictions={predictions}"
                    )
                run = {
                    "variant": variant, "instance": name, "seed": seed,
                    "best_makespan": int(best), "published_upper_bound": instance.upper_bound,
                    "hit_upper_bound": int(best <= instance.upper_bound),
                    "evaluations": int(evaluations), "surrogate_predictions": int(predictions),
                    "inference_batches": int(batches),
                    "exact_evaluation_seconds": exact_seconds,
                    "surrogate_seconds": surrogate_seconds,
                    "runtime_seconds": wall_seconds,
                    "best_permutation": " ".join(map(str, np.asarray(permutation).tolist())),
                }
                convergence_rows = [
                    {
                        "variant": variant, "instance": name, "seed": seed,
                        "generation": generation, "best_makespan": int(value),
                    }
                    for generation, value in enumerate(convergence)
                ]
                append_rows(convergence_path, CONVERGENCE_FIELDS, convergence_rows)
                append_rows(surrogate_trace_path, SURROGATE_TRACE_FIELDS, surrogate_rows)
                append_rows(fuzzy_trace_path, FUZZY_TRACE_FIELDS, fuzzy_rows)
                # The run row is the completion marker and is written last.
                append_rows(runs_path, RUN_FIELDS, [run])
                completed.add(key)
                print(f"completed {variant} {name} seed={seed}: best={best}, exact={evaluations}")

    expected = {
        (variant, instance.name, seed)
        for instance, _ in loaded_instances
        for seed in args.seeds
        for variant in VARIANTS
    }
    final_rows = read_csv(runs_path)
    final_keys = {(r["variant"], r["instance"], int(r["seed"])) for r in final_rows}
    if final_keys != expected or len(final_rows) != len(expected):
        missing, extra = sorted(expected - final_keys), sorted(final_keys - expected)
        raise RuntimeError(
            f"benchmark incomplete or duplicated; rows={len(final_rows)}, "
            f"expected={len(expected)}, missing={missing[:10]}, extra={extra[:10]}"
        )

    # Remove orphaned/duplicated per-generation rows left by an interrupted append.
    deduplicate_csv(convergence_path, ["variant", "instance", "seed", "generation"])
    deduplicate_csv(surrogate_trace_path, ["instance", "seed", "iteration", "candidate_index"])
    deduplicate_csv(fuzzy_trace_path, ["instance", "seed", "iteration"])
    analysis = write_analysis(args.output, final_rows, instance_metadata)
    metadata = {
        "protocol": "week6_taillard_four_variant_benchmark_v1",
        "decision": "docs/decisions/2026-11-25-week6-surrogate-assisted-evaluation.md",
        "protocol_document": "docs/reports/week6_benchmark_protocol.md",
        "objective": "minimize PFSP makespan",
        "variants": list(VARIANTS),
        "seeds": args.seeds,
        "optuna": {
            "config_path": str(args.optuna_config.relative_to(ROOT)),
            "config_sha256": sha256(args.optuna_config),
            "parameters": params,
            "iterations": optuna_iterations,
            "evaluations_per_run": budget,
        },
        "surrogate": {
            "top_k": args.top_k, "wolves": 30, "iterations": 500,
            "exact_evaluations_per_run": 30 + args.top_k * 500,
            "predictions_per_run": 30 * 500,
            "models": model_metadata,
            "preparation_exact_labels_total": sum(
                item["exact_training_labels"] for item in model_metadata.values()
            ),
            "preparation_seconds_total": sum(
                item["dataset_generation_and_exact_labels_seconds"] + item["training_seconds"]
                for item in model_metadata.values()
            ),
        },
        "instances": instance_metadata,
        "expected_runs": len(expected),
        "actual_runs": len(final_rows),
        "search_exact_evaluations_total": sum(int(row["evaluations"]) for row in final_rows),
        "search_surrogate_predictions_total": sum(int(row["surrogate_predictions"]) for row in final_rows),
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "analysis": analysis,
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output), "runs": len(final_rows),
        "search_exact_evaluations_total": metadata["search_exact_evaluations_total"],
        "search_surrogate_predictions_total": metadata["search_surrogate_predictions_total"],
    }, indent=2))


if __name__ == "__main__":
    main()
