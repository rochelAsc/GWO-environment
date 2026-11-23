"""Train and evaluate a per-instance neural surrogate for Taillard PFSP makespan."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
import sklearn
from scipy.stats import qmc, spearmanr
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from scripts.pfs_taillard import load_taillard_instance, makespan


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def permutation_features(permutation: np.ndarray) -> np.ndarray:
    """Return normalized job positions; feature[j] is job j's position."""
    order = np.asarray(permutation)
    if order.ndim != 1 or order.size == 0:
        raise ValueError("permutation must be a non-empty vector")
    if not np.issubdtype(order.dtype, np.integer):
        if not np.all(np.isfinite(order)) or not np.all(order == np.floor(order)):
            raise ValueError("permutation must contain integer job ids")
    order = order.astype(np.int64, copy=False)
    n_jobs = order.size
    if not np.array_equal(np.sort(order), np.arange(n_jobs)):
        raise ValueError("permutation must contain each job exactly once")
    ranks = np.empty(n_jobs, dtype=np.float64)
    ranks[order] = np.arange(n_jobs, dtype=np.float64)
    if n_jobs > 1:
        ranks /= n_jobs - 1
    return ranks


def random_keys_features(random_keys: np.ndarray) -> np.ndarray:
    """Apply the same stable random-key decoder and feature encoder to raw keys."""
    keys = np.asarray(random_keys, dtype=np.float64)
    if keys.ndim != 1 or keys.size == 0 or not np.all(np.isfinite(keys)):
        raise ValueError("random_keys must be a finite, non-empty vector")
    permutation = np.argsort(keys, kind="stable")
    return permutation_features(permutation)


def generate_dataset(
    processing_times: np.ndarray, sample_count: int, seed: int
) -> tuple[np.ndarray, np.ndarray, int, np.ndarray]:
    """Generate LHS keys, deduplicate by decoded permutation, and label exactly."""
    if sample_count < 20:
        raise ValueError("sample_count must be at least 20")
    n_jobs = processing_times.shape[0]
    sampler = qmc.LatinHypercube(d=n_jobs, seed=seed)
    sampled_keys = sampler.random(n=sample_count)
    unique: dict[tuple[int, ...], tuple[np.ndarray, int]] = {}
    for keys in sampled_keys:
        permutation = np.argsort(keys, kind="stable")
        permutation_id = tuple(int(x) for x in permutation)
        if permutation_id not in unique:
            unique[permutation_id] = (
                keys.copy(),
                makespan(processing_times, permutation),
            )
    keys = np.vstack([item[0] for item in unique.values()])
    targets = np.asarray([item[1] for item in unique.values()], dtype=np.float64)
    features = np.vstack([random_keys_features(row) for row in keys])
    return features, targets, len(unique), keys


def build_model(seed: int) -> Pipeline:
    regressor = MLPRegressor(
        hidden_layer_sizes=(64, 64),
        activation="relu",
        solver="adam",
        alpha=1e-4,
        learning_rate_init=1e-3,
        max_iter=1000,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=30,
        random_state=seed,
    )
    return Pipeline([
        ("scale_features", StandardScaler()),
        ("regressor", TransformedTargetRegressor(
            regressor=regressor,
            transformer=StandardScaler(),
        )),
    ])


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    rho = float(spearmanr(y_true, y_pred).statistic)
    return {
        "mse": float(mean_squared_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "spearman_rho": rho if np.isfinite(rho) else None,
    }


def benchmark_latency(
    processing_times: np.ndarray,
    model: Pipeline,
    test_keys: np.ndarray,
    repeats: int = 30,
) -> dict:
    """Compare exact and surrogate paths from identical raw random-key vectors."""
    if test_keys.ndim != 2 or len(test_keys) == 0:
        raise ValueError("test_keys must be a non-empty 2D array")

    def exact_pass():
        for keys in test_keys:
            makespan(processing_times, np.argsort(keys, kind="stable"))

    def surrogate_batch_pass():
        features = np.vstack([random_keys_features(keys) for keys in test_keys])
        model.predict(features)

    def surrogate_single_pass():
        for keys in test_keys:
            features = random_keys_features(keys)
            model.predict(features.reshape(1, -1))

    # Warm-up both paths before collecting repeated measurements.
    exact_pass()
    surrogate_batch_pass()
    surrogate_single_pass()

    measurements = {"exact": [], "surrogate_batch": [], "surrogate_single": []}
    passes = {
        "exact": exact_pass,
        "surrogate_batch": surrogate_batch_pass,
        "surrogate_single": surrogate_single_pass,
    }
    for _ in range(repeats):
        for name, operation in passes.items():
            start = time.perf_counter()
            operation()
            elapsed = time.perf_counter() - start
            measurements[name].append(elapsed / len(test_keys))

    summary = {}
    for name, values in measurements.items():
        values_array = np.asarray(values, dtype=np.float64)
        summary[name] = {
            "median_seconds_per_prediction": float(np.median(values_array)),
            "mean_seconds_per_prediction": float(np.mean(values_array)),
            "std_seconds_per_prediction": float(np.std(values_array, ddof=1)),
            "min_seconds_per_prediction": float(np.min(values_array)),
            "max_seconds_per_prediction": float(np.max(values_array)),
            "repeats": repeats,
        }
    exact_median = summary["exact"]["median_seconds_per_prediction"]
    summary["speedup_vs_exact"] = {
        "surrogate_batch": (
            exact_median
            / summary["surrogate_batch"]["median_seconds_per_prediction"]
        ),
        "surrogate_single": (
            exact_median
            / summary["surrogate_single"]["median_seconds_per_prediction"]
        ),
    }
    summary["comparison_basis"] = (
        "same held-out raw random_keys; exact=decode+makespan; "
        "surrogate=decode+feature_encoding+predict"
    )
    return summary


def evaluate_instance(instance_path: Path, output: Path, sample_count: int, seed: int):
    output.mkdir(parents=True, exist_ok=True)
    instance = load_taillard_instance(instance_path)
    processing_times = instance.processing_times

    generation_start = time.perf_counter()
    X, y, unique_count, random_keys = generate_dataset(
        processing_times, sample_count, seed
    )
    dataset_generation_seconds = time.perf_counter() - generation_start
    indices = np.arange(len(y))
    train_idx, test_idx = train_test_split(
        indices, test_size=0.2, random_state=seed, shuffle=True
    )
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    keys_test = random_keys[test_idx]

    model = build_model(seed)
    train_start = time.perf_counter()
    model.fit(X_train, y_train)
    training_seconds = time.perf_counter() - train_start

    pred_train = model.predict(X_train)
    pred_test = model.predict(X_test)
    metrics = {
        "train": regression_metrics(y_train, pred_train),
        "test": regression_metrics(y_test, pred_test),
    }

    timing = benchmark_latency(processing_times, model, keys_test, repeats=30)

    top_k = min(10, len(test_idx))
    selected_indices = np.argsort(pred_test)[:top_k]
    selected_exact = y_test[selected_indices]
    selected_predicted = pred_test[selected_indices]

    with (output / "dataset.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "sample_id",
            *[f"job_{j}_random_key" for j in range(processing_times.shape[0])],
            *[f"job_{j}_rank" for j in range(processing_times.shape[0])],
            "exact_makespan",
            "split",
        ])
        train_set = set(train_idx.tolist())
        for i, (keys, features, target) in enumerate(zip(random_keys, X, y)):
            writer.writerow([
                i, *keys.tolist(), *features.tolist(), int(target),
                "train" if i in train_set else "test",
            ])

    joblib.dump(model, output / "surrogate.joblib")
    plt.figure()
    plt.scatter(y_test, pred_test, alpha=0.65)
    lower = float(min(y_test.min(), pred_test.min()))
    upper = float(max(y_test.max(), pred_test.max()))
    plt.plot([lower, upper], [lower, upper], linestyle="--")
    plt.xlabel("Makespan exato")
    plt.ylabel("Makespan previsto")
    plt.title(f"{instance.name}: previsto vs. exato (teste)")
    plt.tight_layout()
    plt.savefig(output / "predicted_vs_exact.png", dpi=150)
    plt.close()

    plt.figure()
    plt.scatter(pred_test, pred_test - y_test, alpha=0.65)
    plt.axhline(0.0, linestyle="--")
    plt.xlabel("Makespan previsto")
    plt.ylabel("Resíduo (previsto - exato)")
    plt.title(f"{instance.name}: resíduos (teste)")
    plt.tight_layout()
    plt.savefig(output / "residuals.png", dpi=150)
    plt.close()

    metadata = {
        "protocol": "week4_taillard_pfsp_surrogate_v2",
        "instance": instance.name,
        "instance_path": str(instance_path),
        "instance_sha256": sha256(instance_path),
        "jobs": instance.n_jobs,
        "machines": instance.n_machines,
        "published_upper_bound": instance.upper_bound,
        "published_lower_bound": instance.lower_bound,
        "sample_count_requested": sample_count,
        "unique_permutations": unique_count,
        "duplicate_rate": float(1.0 - unique_count / sample_count),
        "train_samples": int(len(train_idx)),
        "test_samples": int(len(test_idx)),
        "seed": seed,
        "feature_encoding": "normalized_job_rank_permutation",
        "sampling": "scipy_qmc_latin_hypercube_on_random_keys_then_stable_argsort",
        "model": {
            "class": "sklearn.neural_network.MLPRegressor",
            "hidden_layer_sizes": [64, 64],
            "activation": "relu",
            "solver": "adam",
            "alpha": 1e-4,
            "learning_rate_init": 1e-3,
            "max_iter": 1000,
            "early_stopping": True,
            "n_iter_no_change": 30,
            "n_iter_actual": int(
                model.named_steps["regressor"].regressor_.n_iter_
            ),
            "random_state": seed,
        },
        "metrics": metrics,
        "timing": {
            "dataset_generation_and_exact_labels_seconds": dataset_generation_seconds,
            "training_seconds": training_seconds,
            **timing,
        },
        "selection_check": {
            "top_k_by_predicted_makespan": top_k,
            "best_predicted_makespan": float(selected_predicted.min()),
            "best_exact_makespan_among_selected": int(selected_exact.min()),
            "mean_exact_makespan_among_selected": float(selected_exact.mean()),
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }
    (output / "metrics.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "instance": instance.name,
        "unique_permutations": unique_count,
        "test_metrics": metrics["test"],
        "timing": metadata["timing"],
        "selection_check": metadata["selection_check"],
    }, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", nargs="+", type=Path, default=[
        Path("data/benchmarks/taillard/ta001.txt"),
        Path("data/benchmarks/taillard/ta011.txt"),
    ])
    parser.add_argument("--samples", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20261123)
    parser.add_argument(
        "--output", type=Path, default=Path("results/week4_surrogate_pilot_v2")
    )
    args = parser.parse_args()
    if args.samples < 20:
        parser.error("--samples must be >= 20")
    for path in args.instances:
        evaluate_instance(path, args.output / path.stem, args.samples, args.seed)


if __name__ == "__main__":
    main()
