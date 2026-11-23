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


def generate_dataset(processing_times: np.ndarray, sample_count: int, seed: int):
    """Generate LHS random keys, deduplicate decoded permutations, and label exactly."""
    if sample_count < 20:
        raise ValueError("sample_count must be at least 20")
    n_jobs = processing_times.shape[0]
    sampler = qmc.LatinHypercube(d=n_jobs, seed=seed)
    keys = sampler.random(n=sample_count)
    unique: dict[tuple[int, ...], tuple[np.ndarray, int]] = {}
    for vector in keys:
        permutation = np.argsort(vector, kind="stable")
        key = tuple(int(x) for x in permutation)
        if key not in unique:
            unique[key] = (permutation, makespan(processing_times, permutation))
    permutations = list(unique.keys())
    features = np.vstack([permutation_features(np.asarray(p)) for p in permutations])
    targets = np.asarray([unique[p][1] for p in permutations], dtype=np.float64)
    return features, targets, len(permutations)


def build_model(seed: int) -> Pipeline:
    return Pipeline([
        ("scale", StandardScaler()),
        ("mlp", MLPRegressor(
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
        )),
    ])


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "mse": float(mean_squared_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "spearman_rho": float(spearmanr(y_true, y_pred).statistic),
    }


def evaluate_instance(instance_path: Path, output: Path, sample_count: int, seed: int):
    output.mkdir(parents=True, exist_ok=True)
    instance = load_taillard_instance(instance_path)
    p = instance.processing_times

    generation_start = time.perf_counter()
    X, y, unique_count = generate_dataset(p, sample_count, seed)
    dataset_generation_seconds = time.perf_counter() - generation_start
    indices = np.arange(len(y))
    train_idx, test_idx = train_test_split(
        indices, test_size=0.2, random_state=seed, shuffle=True
    )
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

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

    # Compare exact and surrogate latency on identical held-out permutations.
    repeats = 20
    exact_start = time.perf_counter()
    for _ in range(repeats):
        for features, target in zip(X_test, y_test):
            # Reconstruct a permutation from its rank representation.
            permutation = np.argsort(features, kind="stable")
            # Features are indexed by job, so argsort gives jobs in processing order.
            makespan(p, permutation)
    exact_elapsed = time.perf_counter() - exact_start

    inference_start = time.perf_counter()
    for _ in range(repeats):
        model.predict(X_test)
    batch_elapsed = time.perf_counter() - inference_start

    single_start = time.perf_counter()
    for _ in range(repeats):
        for row in X_test:
            model.predict(row.reshape(1, -1))
    single_elapsed = time.perf_counter() - single_start

    # The test targets are exact labels; report the best predicted candidate only
    # after retrieving its exact held-out makespan.
    top_k = min(10, len(test_idx))
    best_predicted_indices = np.argsort(pred_test)[:top_k]
    selected_exact = y_test[best_predicted_indices]
    selected_predicted = pred_test[best_predicted_indices]

    with (output / "dataset.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["sample_id", *[f"job_{j}_rank" for j in range(p.shape[0])], "exact_makespan", "split"])
        train_set = set(train_idx.tolist())
        for i, (features, target) in enumerate(zip(X, y)):
            writer.writerow([i, *features.tolist(), int(target), "train" if i in train_set else "test"])

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
        "protocol": "week4_taillard_pfsp_surrogate_v1",
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
            "n_iter_actual": int(model.named_steps["mlp"].n_iter_),
            "random_state": seed,
        },
        "metrics": metrics,
        "timing": {
            "dataset_generation_and_exact_labels_seconds": dataset_generation_seconds,
            "training_seconds": training_seconds,
            "test_exact_total_seconds": exact_elapsed,
            "test_exact_seconds_per_prediction": exact_elapsed / (repeats * len(test_idx)),
            "surrogate_batch_total_seconds": batch_elapsed,
            "surrogate_batch_seconds_per_prediction": batch_elapsed / (repeats * len(test_idx)),
            "surrogate_single_total_seconds": single_elapsed,
            "surrogate_single_seconds_per_prediction": single_elapsed / (repeats * len(test_idx)),
            "timing_repeats": repeats,
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
    parser.add_argument("--samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261123)
    parser.add_argument("--output", type=Path, default=Path("results/week4_surrogate_v1"))
    args = parser.parse_args()
    if args.samples < 20:
        parser.error("--samples must be >= 20")
    for path in args.instances:
        evaluate_instance(path, args.output / path.stem, args.samples, args.seed)


if __name__ == "__main__":
    main()
