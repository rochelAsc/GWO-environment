"""Memory-bounded recovery of an interrupted v2 surrogate learning-curve run.

Reuses saved permutation NPZs, deterministically regenerates only missing designs,
and checkpoints every fitted model to JSONL. Outputs are kept separate from the
original interrupted directory.
"""
from __future__ import annotations

import argparse
import csv
import gc
import json
import platform
import time
from pathlib import Path

import numpy as np
import scipy
import sklearn
from scipy.stats import kendalltau, qmc, spearmanr

from scripts.pfs_taillard import load_taillard_instance, makespan
from scripts.run_week4_surrogate import build_model, sha256
from experiments.meta_learning.scripts.run_surrogate_learning_curve_v2 import (
    evaluate_predictions,
    geometric_sample_sizes,
)


def _unique_rows(permutations: np.ndarray) -> bool:
    """Exact duplicate check without materializing Python tuples of integers."""
    seen: set[bytes] = set()
    for row in np.asarray(permutations):
        key = np.ascontiguousarray(row).tobytes()
        if key in seen:
            return False
        seen.add(key)
    return True


def _features_batch(permutations: np.ndarray) -> np.ndarray:
    permutations = np.asarray(permutations)
    n, jobs = permutations.shape
    ranks = np.empty((n, jobs), dtype=np.float64)
    ranks[np.arange(n)[:, None], permutations] = np.arange(jobs, dtype=np.float64)
    if jobs > 1:
        ranks /= jobs - 1
    return ranks


def _uniform_permutations(jobs: int, count: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    result = np.empty((count, jobs), dtype=np.int32)
    for i in range(count):
        result[i] = rng.permutation(jobs)
    if not _unique_rows(result):
        raise RuntimeError("duplicate uniform permutations; deterministic sequence differs from expected protocol")
    return result


def _lhs_permutations(jobs: int, count: int, seed: int, max_attempts: int = 100) -> tuple[np.ndarray, int]:
    for attempt in range(max_attempts):
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), int(attempt)]))
        keys = qmc.LatinHypercube(d=jobs, seed=rng).random(n=count)
        permutations = np.argsort(keys, axis=1, kind="stable").astype(np.int32, copy=False)
        del keys
        if _unique_rows(permutations):
            return permutations, attempt + 1
        del permutations
    raise RuntimeError(f"LHS did not produce {count} unique permutations in {max_attempts} attempts")


def _labels(processing_times: np.ndarray, permutations: np.ndarray) -> np.ndarray:
    values = np.empty(len(permutations), dtype=np.float64)
    for i, permutation in enumerate(permutations):
        values[i] = makespan(processing_times, permutation)
    return values


def _diagnostic_arrays(permutations: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    n, jobs = permutations.shape
    positions = np.zeros((jobs, jobs), dtype=np.int64)
    for pos in range(jobs):
        np.add.at(positions[:, pos], permutations[:, pos], 1)

    rng = np.random.default_rng(seed)
    sample_n = min(n, 512)
    indices = np.sort(rng.choice(n, size=sample_n, replace=False))
    sample = permutations[indices]
    ranks = np.argsort(sample, axis=1)
    precedence_counts = np.zeros((jobs, jobs), dtype=np.int64)
    for offset in range(0, sample_n, 16):
        chunk = ranks[offset:offset + 16]
        precedence_counts += np.sum(chunk[:, :, None] < chunk[:, None, :], axis=0)
    return positions, precedence_counts / sample_n


def _record_key(instance: str, method: str, n: int, rep: int) -> str:
    return f"{instance}|{method}|{n}|{rep}"


def _read_completed(path: Path) -> set[str]:
    completed: set[str] = set()
    if not path.exists():
        return completed
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                row = json.loads(line)
                completed.add(row["record_key"])
            except (json.JSONDecodeError, KeyError):
                # A truncated final line is ignored; valid prior checkpoints remain.
                continue
    return completed


def _append_checkpoint(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, allow_nan=True) + "\n")
        stream.flush()


def recover_instance(
    instance_path: Path,
    source: Path,
    destination: Path,
    sizes: list[int],
    repeats: int,
    base_seed: int,
    lhs_max_attempts: int,
    completed: set[str],
) -> None:
    instance = load_taillard_instance(instance_path)
    name = instance.name
    jobs = instance.n_jobs
    source_instance = source / name
    destination_instance = destination / name
    destination_instance.mkdir(parents=True, exist_ok=True)

    test_path = source_instance / "fixed_test_set.npz"
    if not test_path.exists():
        raise FileNotFoundError(f"fixed test set missing: {test_path}")
    with np.load(test_path, allow_pickle=False) as data:
        X_test = data["X_test"].copy()
        y_test = data["y_test"].copy()
        test_permutations = data["permutations_test"].copy()
    if X_test.shape != (len(y_test), jobs) or test_permutations.shape != X_test.shape:
        raise ValueError(f"invalid fixed test set dimensions for {name}")
    if not np.allclose(X_test, _features_batch(test_permutations), rtol=0, atol=1e-12):
        raise ValueError(f"fixed test features do not match saved permutations for {name}")
    test_seed = base_seed + 900_000

    # Validate the local SciPy/QMC implementation against a saved LHS design
    # before trusting deterministic regeneration of the missing 32k design.
    lhs_validation_seed = base_seed + (repeats - 1) * 100_000 + min(sizes) * 7
    validation_path = source_instance / (
        f"{name}_lhs_random_keys_n{min(sizes)}_rep{repeats}_diagnostics.npz"
    )
    with np.load(validation_path, allow_pickle=False) as data:
        saved_lhs_validation = data["permutations"].astype(np.int32, copy=True)
    regenerated_lhs_validation, _ = _lhs_permutations(
        jobs, min(sizes), lhs_validation_seed, lhs_max_attempts
    )
    if not np.array_equal(regenerated_lhs_validation, saved_lhs_validation):
        raise RuntimeError(
            f"local SciPy/QMC does not reproduce the saved LHS design for {name}; "
            "use the original virtual environment/version before recovering the missing LHS design"
        )
    del saved_lhs_validation, regenerated_lhs_validation
    gc.collect()

    # Only the interrupted rep-5 uniform maximum design is regenerated.
    for repetition in range(repeats):
        uniform_seed = base_seed + repetition * 10_000 + 101
        uniform_rep5: np.ndarray | None = None

        for sample_count in sizes:
            for method in ("lhs_random_keys", "uniform_permutations"):
                key = _record_key(name, method, sample_count, repetition)
                if key in completed:
                    continue

                diagnostic_path = source_instance / (
                    f"{name}_{method}_n{sample_count}_rep{repetition + 1}_diagnostics.npz"
                )
                attempts: int | None = None
                if diagnostic_path.exists():
                    with np.load(diagnostic_path, allow_pickle=False) as data:
                        if "permutations" not in data.files:
                            raise ValueError(f"permutations missing in {diagnostic_path}")
                        permutations = data["permutations"].astype(np.int32, copy=True)
                elif method == "lhs_random_keys":
                    sampling_seed = base_seed + repetition * 100_000 + sample_count * 7
                    permutations, attempts = _lhs_permutations(
                        jobs, sample_count, sampling_seed, lhs_max_attempts
                    )
                else:
                    attempts = 0
                    if repetition != repeats - 1:
                        raise FileNotFoundError(f"unexpected missing uniform design: {diagnostic_path}")
                    if uniform_rep5 is None:
                        uniform_rep5 = _uniform_permutations(
                            jobs, max(sizes), uniform_seed
                        )
                        # Prove the regenerated stream agrees with the saved nested prefix.
                        prefix_path = source_instance / (
                            f"{name}_uniform_permutations_n{min(sizes)}_rep{repetition + 1}_diagnostics.npz"
                        )
                        with np.load(prefix_path, allow_pickle=False) as data:
                            saved_prefix = data["permutations"].astype(np.int32, copy=False)
                        if not np.array_equal(uniform_rep5[:min(sizes)], saved_prefix):
                            raise RuntimeError(
                                f"uniform regenerated prefix differs from saved data for {name}, rep {repetition + 1}"
                            )
                    permutations = uniform_rep5[:sample_count]

                if permutations.shape != (sample_count, jobs) or not _unique_rows(permutations):
                    raise ValueError(f"invalid or duplicate permutations in {diagnostic_path}")
                X_train = _features_batch(permutations)
                y_train = _labels(instance.processing_times, permutations)

                # Persist only genuinely missing diagnostic files; never alter existing originals.
                if not diagnostic_path.exists():
                    diagnostic_seed = (
                        base_seed + repetition * 100_000 + sample_count * 7
                        if method == "lhs_random_keys" else uniform_seed
                    )
                    positions, precedence = _diagnostic_arrays(
                        permutations, diagnostic_seed + 73_001,
                    )
                    np.savez_compressed(
                        destination_instance / diagnostic_path.name,
                        position_counts=positions,
                        pairwise_precedence=precedence,
                        permutations=permutations.astype(np.uint16),
                    )

                model_seed = base_seed + repetition * 1_000 + sample_count + (
                    500_000 if method == "uniform_permutations" else 0
                )
                model = build_model(model_seed)
                train_start = time.perf_counter()
                model.fit(X_train, y_train)
                training_seconds = time.perf_counter() - train_start
                predictions = model.predict(X_test)
                metrics = evaluate_predictions(y_test, predictions)
                row = {
                    "record_key": key,
                    "instance": name,
                    "instance_sha256": sha256(instance_path),
                    "jobs": jobs,
                    "machines": instance.n_machines,
                    "sampling_method": method,
                    "sample_count": sample_count,
                    "repetition": repetition,
                    "sampling_seed": (
                        base_seed + repetition * 100_000 + sample_count * 7
                        if method == "lhs_random_keys" else uniform_seed
                    ),
                    "model_seed": model_seed,
                    "test_seed": test_seed,
                    "train_samples_actual": int(len(y_train)),
                    "test_samples": int(len(y_test)),
                    "lhs_complete_design_attempts": attempts,
                    "python_version": platform.python_version(),
                    "numpy_version": np.__version__,
                    "scipy_version": scipy.__version__,
                    "scikit_learn_version": sklearn.__version__,
                    "training_seconds_recovered": training_seconds,
                    "dataset_generation_and_labeling_seconds_original": None,
                    "metrics_reconstructed": True,
                    **metrics,
                }
                _append_checkpoint(destination / "recovered_runs.jsonl", row)
                completed.add(key)
                print(f"RECOVERED {key}: rho={metrics['spearman']:.4f}, "
                      f"top10_recall={metrics['top10_recall']:.3f}", flush=True)

                del model, predictions, X_train, y_train, permutations
                gc.collect()

        del uniform_rep5
        uniform_rep5 = None
        gc.collect()

    del X_test, y_test, test_permutations
    gc.collect()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--instances", nargs="+", type=Path, default=[
        Path("data/benchmarks/taillard/ta071.txt"),
        Path("data/benchmarks/taillard/ta111.txt"),
    ])
    parser.add_argument("--min-samples", type=int, default=8000)
    parser.add_argument("--max-samples", type=int, default=32000)
    parser.add_argument("--points", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261128)
    parser.add_argument("--lhs-max-attempts", type=int, default=100)
    args = parser.parse_args()

    if not args.source.is_dir():
        parser.error(f"source directory does not exist: {args.source}")
    args.output.mkdir(parents=True, exist_ok=True)
    sizes = geometric_sample_sizes(args.min_samples, args.max_samples, args.points)
    if sizes != [8000, 16000, 32000]:
        parser.error(f"this recovery implementation expects [8000, 16000, 32000], got {sizes}")

    checkpoint = args.output / "recovered_runs.jsonl"
    completed = _read_completed(checkpoint)
    for instance_path in args.instances:
        recover_instance(
            instance_path, args.source, args.output, sizes, args.repeats,
            args.seed, args.lhs_max_attempts, completed,
        )

    rows = []
    with checkpoint.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    expected = len(args.instances) * len(sizes) * 2 * args.repeats
    if len({row["record_key"] for row in rows}) != expected:
        print(f"CHECKPOINTS: {len(rows)}/{expected}; rerun same command to resume", flush=True)
        return

    csv_path = args.output / "recovered_runs.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "protocol": "meta_learning_surrogate_learning_curve_v2_recovery",
        "source_directory": str(args.source),
        "sample_sizes": sizes,
        "repeats": args.repeats,
        "base_seed": args.seed,
        "instances": [str(path) for path in args.instances],
        "records": len(rows),
        "software_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "recovery_policy": "reuses saved permutations; regenerates missing designs deterministically; verifies rep-5 uniform prefix; one model fit at a time; JSONL checkpoint after every fit",
        "limitations": [
            "original dataset-generation timings were not checkpointed and cannot be recovered",
            "training times are measured during recovery, not the interrupted original run",
            "the original run's software-version metadata was not written before interruption",
            "top-k metrics use the original v2 argsort tie handling",
        ],
    }
    (args.output / "recovery_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
