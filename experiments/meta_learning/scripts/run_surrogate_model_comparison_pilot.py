"""CPU-only pilot comparing surrogate regressors on the frozen ta111 dataset.

Consumes the original v2 NPZ artifacts without modifying them. Each estimator
is fitted sequentially and checkpointed to JSONL so interrupted runs can resume.
"""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import platform
import threading
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import scipy
import sklearn
try:
    import psutil
except ImportError:  # Optional: metrics remain usable without psutil.
    psutil = None
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from threadpoolctl import threadpool_limits

from scripts.pfs_taillard import load_taillard_instance, makespan
from scripts.run_week4_surrogate import build_model, permutation_features, sha256
from experiments.meta_learning.scripts.run_surrogate_learning_curve_v2 import evaluate_predictions


DEFAULT_SOURCE = Path("results/meta_learning_surrogate_learning_curve_v2_extension")
DEFAULT_OUTPUT = Path("results/meta_learning_surrogate_model_comparison_pilot")
DEFAULT_INSTANCE = Path("data/benchmarks/taillard/ta111.txt")
BASE_SEED = 20261128
SAMPLE_COUNT = 8_000
TEST_COUNT = 1_000
REPETITION = 1
SAMPLING_METHOD = "uniform_permutations"


def _features_batch(permutations: np.ndarray) -> np.ndarray:
    permutations = np.asarray(permutations)
    if permutations.ndim != 2:
        raise ValueError("permutations must be a 2D array")
    n, jobs = permutations.shape
    features = np.empty((n, jobs), dtype=np.float64)
    features[np.arange(n)[:, None], permutations] = np.arange(jobs, dtype=np.float64)
    if jobs > 1:
        features /= jobs - 1
    return features


def _unique_rows(permutations: np.ndarray) -> bool:
    seen: set[bytes] = set()
    for row in np.asarray(permutations):
        key = np.ascontiguousarray(row).tobytes()
        if key in seen:
            return False
        seen.add(key)
    return True


class _PeakRSSSampler:
    """Sample process RSS during one fit/predict block when psutil is available."""

    def __init__(self, interval_seconds: float = 0.05) -> None:
        self.interval_seconds = interval_seconds
        self.peak_bytes: int | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _sample(self) -> None:
        process = psutil.Process()
        while not self._stop.is_set():
            try:
                rss = process.memory_info().rss
                self.peak_bytes = max(self.peak_bytes or 0, rss)
            except psutil.Error:
                pass
            self._stop.wait(self.interval_seconds)

    def __enter__(self) -> "_PeakRSSSampler":
        if psutil is not None:
            self._thread = threading.Thread(target=self._sample, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join()

    @property
    def peak_mb(self) -> float | None:
        return self.peak_bytes / (1024 ** 2) if self.peak_bytes is not None else None


def _make_estimators(seed: int) -> dict[str, Any]:
    return {
        "mlp_64x64": build_model(seed),
        "random_forest": RandomForestRegressor(
            n_estimators=300, min_samples_leaf=2, max_features=1.0,
            n_jobs=1, random_state=seed,
        ),
        "extra_trees": ExtraTreesRegressor(
            n_estimators=300, min_samples_leaf=2, max_features=1.0,
            n_jobs=1, random_state=seed,
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.08, max_leaf_nodes=31,
            l2_regularization=1.0, early_stopping=True, random_state=seed,
        ),
    }


def _load_and_validate_data(
    instance_path: Path, source: Path
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    instance = load_taillard_instance(instance_path)
    name = instance.name
    train_path = source / name / (
        f"{name}_{SAMPLING_METHOD}_n{SAMPLE_COUNT}_rep{REPETITION}_diagnostics.npz"
    )
    test_path = source / name / "fixed_test_set.npz"
    for path in (instance_path, train_path, test_path):
        if not path.is_file():
            raise FileNotFoundError(f"required pilot input not found: {path}")

    with np.load(train_path, allow_pickle=False) as data:
        if "permutations" not in data.files:
            raise ValueError(f"'permutations' array missing from {train_path}")
        train_permutations = data["permutations"].astype(np.int32, copy=True)

    with np.load(test_path, allow_pickle=False) as data:
        required = {"X_test", "y_test", "permutations_test"}
        missing = required.difference(data.files)
        if missing:
            raise ValueError(f"fixed test set missing arrays: {sorted(missing)}")
        X_test = data["X_test"].astype(np.float64, copy=True)
        y_test = data["y_test"].astype(np.float64, copy=True)
        test_permutations = data["permutations_test"].astype(np.int32, copy=True)

    jobs = instance.n_jobs
    if train_permutations.shape != (SAMPLE_COUNT, jobs):
        raise ValueError(
            f"training permutations have shape {train_permutations.shape}; "
            f"expected {(SAMPLE_COUNT, jobs)}"
        )
    if test_permutations.shape != (TEST_COUNT, jobs):
        raise ValueError(
            f"test permutations have shape {test_permutations.shape}; "
            f"expected {(TEST_COUNT, jobs)}"
        )
    if not _unique_rows(train_permutations) or not _unique_rows(test_permutations):
        raise ValueError("duplicate permutations found in frozen train/test data")
    if set(map(bytes, train_permutations)).intersection(map(bytes, test_permutations)):
        raise ValueError("training and fixed test permutations overlap")

    X_train = _features_batch(train_permutations)
    expected_X_test = _features_batch(test_permutations)
    if X_test.shape != expected_X_test.shape or not np.allclose(
        X_test, expected_X_test, rtol=0, atol=1e-12
    ):
        raise ValueError("saved fixed-test features do not match saved permutations")

    y_train = np.fromiter(
        (makespan(instance.processing_times, row) for row in train_permutations),
        dtype=np.float64,
        count=SAMPLE_COUNT,
    )
    if not np.all(np.isfinite(y_train)) or not np.all(np.isfinite(y_test)):
        raise ValueError("non-finite makespan label found")

    metadata = {
        "instance": name,
        "jobs": instance.n_jobs,
        "machines": instance.n_machines,
        "instance_sha256": sha256(instance_path),
        "training_npz": str(train_path),
        "training_npz_sha256": sha256(train_path),
        "fixed_test_npz": str(test_path),
        "fixed_test_npz_sha256": sha256(test_path),
        "training_permutations_sha256": hashlib.sha256(
            np.ascontiguousarray(train_permutations).view(np.uint8)
        ).hexdigest(),
        "test_permutations_sha256": hashlib.sha256(
            np.ascontiguousarray(test_permutations).view(np.uint8)
        ).hexdigest(),
        "train_samples": int(len(y_train)),
        "test_samples": int(len(y_test)),
    }
    return X_train, y_train, X_test, y_test, metadata


def _read_checkpoints(path: Path) -> dict[str, dict]:
    completed: dict[str, dict] = {}
    if not path.exists():
        return completed
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                row = json.loads(line)
                completed[row["model"]] = row
            except (json.JSONDecodeError, KeyError):
                # Ignore only a malformed/truncated line; prior checkpoints remain valid.
                continue
    return completed


def _append_checkpoint(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_pilot(
    instance_path: Path = DEFAULT_INSTANCE,
    source: Path = DEFAULT_SOURCE,
    output: Path = DEFAULT_OUTPUT,
    force: bool = False,
) -> list[dict]:
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output / "pilot_checkpoints.jsonl"
    metadata_path = output / "pilot_metadata.json"
    X_train, y_train, X_test, y_test, data_metadata = _load_and_validate_data(
        instance_path, source
    )
    model_seed = BASE_SEED + REPETITION * 1_000 + SAMPLE_COUNT + 500_000
    config = {
        "protocol": "surrogate_model_comparison_pilot_v1",
        "branch_context": "recovery/surrogate-learning-curve-v2-oom",
        "instance": data_metadata["instance"],
        "sampling_method": SAMPLING_METHOD,
        "sample_count": SAMPLE_COUNT,
        "repetition": REPETITION,
        "model_seed": model_seed,
        "models": {
            "mlp_64x64": "scripts.run_week4_surrogate.build_model",
            "random_forest": {
                "n_estimators": 300, "min_samples_leaf": 2,
                "max_features": 1.0, "n_jobs": 1,
            },
            "extra_trees": {
                "n_estimators": 300, "min_samples_leaf": 2,
                "max_features": 1.0, "n_jobs": 1,
            },
            "hist_gradient_boosting": {
                "max_iter": 300, "learning_rate": 0.08,
                "max_leaf_nodes": 31, "l2_regularization": 1.0,
                "early_stopping": True,
            },
        },
        "data": data_metadata,
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "execution": {
            "device": "CPU",
            "rss_sampling": "psutil process RSS sampled every 50 ms when installed; includes resident data arrays and runtime, not model-only memory",
            "thread_limit": 1,
            "sequential_models": True,
        },
    }
    if metadata_path.exists():
        existing = json.loads(metadata_path.read_text(encoding="utf-8"))
        if existing != config and not force:
            raise RuntimeError(
                f"{metadata_path} belongs to a different input/configuration; "
                "use a new output directory or --force after inspecting it"
            )
    else:
        metadata_path.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    completed = _read_checkpoints(checkpoint_path)
    if force:
        completed = {}
        checkpoint_path.unlink(missing_ok=True)

    rows = list(completed.values())
    estimators = _make_estimators(model_seed)
    for model_name, estimator in estimators.items():
        if model_name in completed:
            print(f"SKIP {model_name}: valid checkpoint already exists")
            continue
        print(f"START {model_name}: X_train={X_train.shape}, X_test={X_test.shape}")
        fit_start = time.perf_counter()
        with _PeakRSSSampler() as memory_sampler:
            with threadpool_limits(limits=1):
                estimator.fit(X_train, y_train)
                training_seconds = time.perf_counter() - fit_start
                inference_start = time.perf_counter()
                predictions = estimator.predict(X_test)
                inference_seconds = time.perf_counter() - inference_start
        metrics = evaluate_predictions(y_test, predictions)
        if not np.all(np.isfinite(predictions)):
            raise ValueError(f"{model_name} produced non-finite predictions")
        row = {
            "model": model_name,
            "instance": data_metadata["instance"],
            "sampling_method": SAMPLING_METHOD,
            "sample_count": SAMPLE_COUNT,
            "repetition": REPETITION,
            "model_seed": model_seed,
            "training_seconds": training_seconds,
            "inference_seconds_batch": inference_seconds,
            "inference_microseconds_per_sample": inference_seconds * 1e6 / len(y_test),
            "peak_process_rss_mb_during_fit_predict": memory_sampler.peak_mb,
            "rss_measurement_available": psutil is not None,
            "train_samples": len(y_train),
            "test_samples": len(y_test),
            **metrics,
        }
        _append_checkpoint(checkpoint_path, row)
        rows.append(row)
        print(
            f"DONE {model_name}: rho={metrics['spearman']:.4f}, "
            f"top10_recall={metrics['top10_recall']:.3f}, "
            f"top10_regret={metrics['top10_regret']:.1f}, "
            f"fit={training_seconds:.1f}s"
        )
        del estimator, predictions
        gc.collect()

    _write_csv(output / "pilot_results.csv", rows)
    summary = {
        "status": "completed" if len({row["model"] for row in rows}) == len(estimators) else "partial",
        "models_completed": sorted(row["model"] for row in rows),
        "results_csv": str(output / "pilot_results.csv"),
        "metadata": str(metadata_path),
    }
    (output / "pilot_status.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=Path, default=DEFAULT_INSTANCE)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    rows = run_pilot(args.instance, args.source, args.output, args.force)
    print(json.dumps({
        "completed_models": [row["model"] for row in rows],
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
