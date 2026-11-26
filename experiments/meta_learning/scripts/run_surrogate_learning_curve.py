"""Learning-curve experiment for per-instance PFSP makespan surrogates.

The experiment compares LHS-on-random-keys with direct uniform permutations.
All training sizes share one fixed, independently generated test set per instance.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import kendalltau, qmc, spearmanr

from scripts.pfs_taillard import load_taillard_instance, makespan
from scripts.run_week4_surrogate import build_model, permutation_features, sha256


def geometric_sample_sizes(minimum: int = 300, maximum: int = 4000, points: int = 5) -> list[int]:
    """Return log-spaced integer sample sizes, including both endpoints."""
    if minimum < 2 or maximum < minimum or points < 2:
        raise ValueError("require 2 <= minimum <= maximum and points >= 2")
    ratio = (maximum / minimum) ** (1.0 / (points - 1))
    values = [int(round(minimum * ratio**i)) for i in range(points)]
    values[0] = minimum
    values[-1] = maximum
    # Rounding can theoretically collapse adjacent values for narrow ranges.
    if len(set(values)) != points:
        raise ValueError("sample-size range is too narrow for the requested number of points")
    return values


def generate_uniform_permutations(
    processing_times: np.ndarray, count: int, seed: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate a nested prefix of unique, uniformly sampled permutations."""
    rng = np.random.default_rng(seed)
    n_jobs = processing_times.shape[0]
    seen: set[tuple[int, ...]] = set()
    features: list[np.ndarray] = []
    targets: list[float] = []
    permutations: list[np.ndarray] = []
    while len(permutations) < count:
        permutation = rng.permutation(n_jobs)
        key = tuple(int(value) for value in permutation)
        if key in seen:
            continue
        seen.add(key)
        permutations.append(permutation)
        features.append(permutation_features(permutation))
        targets.append(float(makespan(processing_times, permutation)))
    return (
        np.vstack(features),
        np.asarray(targets, dtype=np.float64),
        np.vstack(permutations),
    )


def generate_lhs_dataset(
    processing_times: np.ndarray, count: int, seed: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate LHS random keys, decode with stable argsort, and label exactly."""
    n_jobs = processing_times.shape[0]
    if count < 1:
        raise ValueError("count must be positive")
    if count > math.factorial(n_jobs):
        raise ValueError(
            f"requested {count} unique permutations, but only {math.factorial(n_jobs)} exist"
        )

    sampler = qmc.LatinHypercube(d=n_jobs, seed=seed)
    features: list[np.ndarray] = []
    targets: list[float] = []
    permutations: list[np.ndarray] = []
    seen: set[tuple[int, ...]] = set()
    draws = 0
    max_draws = max(10_000, count * 100)
    batch_size = min(max(count, 32), 512)

    # LHS keys can decode to the same permutation. Draw additional LHS batches
    # until the requested number of distinct decoded permutations is reached.
    while len(permutations) < count and draws < max_draws:
        keys = sampler.random(n=min(batch_size, max_draws - draws))
        draws += len(keys)
        for row in keys:
            permutation = np.argsort(row, kind="stable")
            key = tuple(int(value) for value in permutation)
            if key in seen:
                continue
            seen.add(key)
            permutations.append(permutation)
            features.append(permutation_features(permutation))
            targets.append(float(makespan(processing_times, permutation)))
            if len(permutations) == count:
                break
    if len(permutations) != count:
        raise RuntimeError(
            f"LHS produced {len(permutations)} unique permutations after {draws} draws; "
            f"expected {count}"
        )
    return (
        np.vstack(features),
        np.asarray(targets, dtype=np.float64),
        np.vstack(permutations),
    )


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    result = {
        "rmse": float(np.sqrt(np.mean(np.square(y_pred - y_true)))),
        "mae": float(np.mean(np.abs(y_pred - y_true))),
        "r2": float(1.0 - np.sum(np.square(y_pred - y_true)) / np.sum(np.square(y_true - np.mean(y_true)))),
        "spearman": float(spearmanr(y_true, y_pred).statistic),
        "kendall_tau_b": float(kendalltau(y_true, y_pred, variant="b").statistic),
    }
    for key, value in list(result.items()):
        if not np.isfinite(value):
            result[key] = float("nan")
    n = len(y_true)
    for k_requested in (3, 10, 50):
        k = min(k_requested, n)
        actual_top = set(np.argsort(y_true)[:k].tolist())
        predicted_top = set(np.argsort(y_pred)[:k].tolist())
        selected = np.asarray(sorted(predicted_top), dtype=np.int64)
        result[f"top{k_requested}_recall"] = len(actual_top & predicted_top) / k
        result[f"top{k_requested}_regret"] = float(np.min(y_true[selected]) - np.min(y_true))
        result[f"top{k_requested}_selected_mean"] = float(np.mean(y_true[selected]))
    return result


def _summarize(rows: list[dict]) -> list[dict]:
    metrics = [
        "rmse", "mae", "r2", "spearman", "kendall_tau_b",
        "top3_recall", "top3_regret", "top10_recall", "top10_regret",
        "top50_recall", "top50_regret", "training_seconds",
        "dataset_generation_and_labeling_seconds",
    ]
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (row["instance"], row["sampling_method"], row["sample_count"])
        groups.setdefault(key, []).append(row)
    output = []
    for (instance, method, sample_count), group in sorted(groups.items()):
        item = {
            "instance": instance,
            "sampling_method": method,
            "sample_count": sample_count,
            "repetitions": len(group),
        }
        for metric in metrics:
            values = np.asarray([float(row[metric]) for row in group], dtype=float)
            item[f"{metric}_mean"] = float(np.nanmean(values))
            item[f"{metric}_std"] = float(np.nanstd(values, ddof=1)) if len(values) > 1 else 0.0
        output.append(item)
    return output


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _plot_curves(output: Path, summaries: list[dict], instance_name: str) -> None:
    metrics = [
        ("rmse", "RMSE (lower is better)"),
        ("spearman", "Spearman rho (higher is better)"),
        ("kendall_tau_b", "Kendall tau-b (higher is better)"),
        ("top10_recall", "Top-10 recall (higher is better)"),
        ("top10_regret", "Top-10 regret (lower is better)"),
    ]
    for metric, ylabel in metrics:
        plt.figure()
        for method in ("lhs_random_keys", "uniform_permutations"):
            selected = [
                row for row in summaries
                if row["instance"] == instance_name and row["sampling_method"] == method
            ]
            selected.sort(key=lambda row: row["sample_count"])
            if not selected:
                continue
            x = np.asarray([row["sample_count"] for row in selected], dtype=float)
            mean = np.asarray([row[f"{metric}_mean"] for row in selected], dtype=float)
            std = np.asarray([row[f"{metric}_std"] for row in selected], dtype=float)
            plt.plot(x, mean, marker="o", label=method)
            plt.fill_between(x, mean - std, mean + std, alpha=0.15)
        plt.xscale("log")
        plt.xlabel("Training samples (log scale)")
        plt.ylabel(ylabel)
        plt.title(f"{instance_name}: learning curve")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output / f"{instance_name}_{metric}_learning_curve.png", dpi=160)
        plt.close()


def run_instance(
    instance_path: Path,
    output_root: Path,
    sizes: list[int],
    repeats: int,
    test_samples: int,
    base_seed: int,
) -> list[dict]:
    instance = load_taillard_instance(instance_path)
    processing_times = instance.processing_times
    instance_output = output_root / instance.name
    instance_output.mkdir(parents=True, exist_ok=True)

    test_seed = base_seed + 900_000
    test_start = time.perf_counter()
    X_test, y_test, permutations_test = generate_uniform_permutations(
        processing_times, test_samples, test_seed
    )
    test_generation_seconds = time.perf_counter() - test_start
    test_permutation_keys = {tuple(int(value) for value in row) for row in permutations_test}
    np.savez_compressed(
        instance_output / "fixed_test_set.npz",
        X_test=X_test,
        y_test=y_test,
        permutations_test=permutations_test,
    )

    rows: list[dict] = []
    max_samples = max(sizes)
    for repetition in range(repeats):
        # Uniform-permutation arm: one maximum design, nested prefixes.
        uniform_seed = base_seed + repetition * 10_000 + 101
        uniform_start = time.perf_counter()
        X_uniform, y_uniform, permutations_uniform = generate_uniform_permutations(
            processing_times, max_samples, uniform_seed
        )
        uniform_total_generation = time.perf_counter() - uniform_start
        uniform_keys = {tuple(int(value) for value in row) for row in permutations_uniform}
        if uniform_keys & test_permutation_keys:
            raise RuntimeError("uniform training and fixed test sets overlap")
        uniform_label_time_per_sample = uniform_total_generation / max_samples

        for sample_count in sizes:
            for method in ("lhs_random_keys", "uniform_permutations"):
                sampling_seed = (
                    base_seed + repetition * 100_000 + sample_count * 7
                    + (0 if method == "lhs_random_keys" else 1)
                )
                if method == "lhs_random_keys":
                    generation_start = time.perf_counter()
                    X_train, y_train, permutations_train = generate_lhs_dataset(
                        processing_times, sample_count, sampling_seed
                    )
                    generation_seconds = time.perf_counter() - generation_start
                    lhs_keys = {tuple(int(value) for value in row) for row in permutations_train}
                    if lhs_keys & test_permutation_keys:
                        raise RuntimeError("LHS training and fixed test sets overlap")
                else:
                    sampling_seed = uniform_seed
                    X_train = X_uniform[:sample_count]
                    y_train = y_uniform[:sample_count]
                    generation_seconds = uniform_label_time_per_sample * sample_count

                model_seed = base_seed + repetition * 1_000 + sample_count + (
                    500_000 if method == "uniform_permutations" else 0
                )
                model = build_model(model_seed)
                train_start = time.perf_counter()
                model.fit(X_train, y_train)
                training_seconds = time.perf_counter() - train_start
                predictions = model.predict(X_test)
                metrics = evaluate_predictions(y_test, predictions)
                rows.append({
                    "instance": instance.name,
                    "instance_sha256": sha256(instance_path),
                    "jobs": instance.n_jobs,
                    "machines": instance.n_machines,
                    "sampling_method": method,
                    "sample_count": sample_count,
                    "repetition": repetition,
                    "sampling_seed": sampling_seed,
                    "model_seed": model_seed,
                    "test_seed": test_seed,
                    "train_samples_actual": int(len(y_train)),
                    "test_samples": int(len(y_test)),
                    "dataset_generation_and_labeling_seconds": generation_seconds,
                    "training_seconds": training_seconds,
                    "test_set_generation_and_labeling_seconds": test_generation_seconds,
                    **metrics,
                })
                print(
                    f"{instance.name} {method} n={sample_count} "
                    f"rep={repetition + 1}/{repeats} "
                    f"rho={metrics['spearman']:.4f} "
                    f"top10_recall={metrics['top10_recall']:.3f}"
                )

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--instances", nargs="+", type=Path, default=[
            Path("data/benchmarks/taillard/ta071.txt"),
            Path("data/benchmarks/taillard/ta111.txt"),
        ],
    )
    parser.add_argument("--min-samples", type=int, default=300)
    parser.add_argument("--max-samples", type=int, default=4000)
    parser.add_argument("--points", type=int, default=5)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--test-samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20261128)
    parser.add_argument(
        "--output", type=Path,
        default=Path("results/meta_learning_surrogate_learning_curve_v1"),
    )
    args = parser.parse_args()
    if args.repeats < 2:
        parser.error("--repeats must be >= 2")
    if args.test_samples < 50:
        parser.error("--test-samples must be >= 50")

    sizes = geometric_sample_sizes(args.min_samples, args.max_samples, args.points)
    if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
        parser.error(f"output directory already exists and is not empty: {args.output}; choose a new --output")
    args.output.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []
    for instance_path in args.instances:
        all_rows.extend(run_instance(
            instance_path, args.output, sizes, args.repeats,
            args.test_samples, args.seed,
        ))

    summaries = _summarize(all_rows)
    _write_csv(args.output / "learning_curve_runs.csv", all_rows)
    _write_csv(args.output / "learning_curve_summary.csv", summaries)
    metadata = {
        "protocol": "meta_learning_surrogate_learning_curve_v1",
        "growth_function": "round(N_min * (N_max/N_min) ** (i/(K-1)))",
        "sample_sizes": sizes,
        "growth_ratio": (args.max_samples / args.min_samples) ** (1 / (args.points - 1)),
        "repeats": args.repeats,
        "test_samples_per_instance": args.test_samples,
        "base_seed": args.seed,
        "sampling_methods": ["lhs_random_keys", "uniform_permutations"],
        "test_design": "fixed independent uniform permutations per instance, shared across all training sizes and repetitions",
        "training_design": {
            "lhs_random_keys": "independent LHS design for each size and repetition; stable argsort decoder",
            "uniform_permutations": "one maximum-size uniform permutation set per repetition; smaller sizes are nested prefixes",
        },
        "model": "scripts.run_week4_surrogate.build_model; MLP 64x64 with feature and target scaling",
        "instances": [
            {
                "path": str(path),
                "sha256": sha256(path),
                "name": path.stem,
            } for path in args.instances
        ],
        "parallel_execution": False,
        "literature_basis": [
            "Framinan (2025), DOI 10.1049/cim2.70049: PFSP stochastic, GBT, sample sizes 10/100/1000",
            "Muñoz and Kirley (2021), DOI 10.3390/a14010019: logarithmically spaced sample sizes and LHS",
        ],
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    for path in args.instances:
        _plot_curves(args.output, summaries, path.stem)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
