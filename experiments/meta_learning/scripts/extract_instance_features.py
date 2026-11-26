"""Deterministic, outcome-independent features for Taillard PFSP instances."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

import numpy as np
import pandas as pd

try:
    from scripts.pfs_taillard import load_taillard_instance
except ModuleNotFoundError:  # Support direct execution from the repository root.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.pfs_taillard import load_taillard_instance


FEATURE_VERSION = "taillard_pfsp_features_v1"


def _summary(prefix: str, values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64).ravel()
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=0))
    return {
        f"{prefix}_mean": mean,
        f"{prefix}_std": std,
        f"{prefix}_cv": std / mean if mean else 0.0,
        f"{prefix}_min": float(np.min(values)),
        f"{prefix}_q25": float(np.quantile(values, 0.25)),
        f"{prefix}_median": float(np.median(values)),
        f"{prefix}_q75": float(np.quantile(values, 0.75)),
        f"{prefix}_max": float(np.max(values)),
    }


def extract_instance_features(processing_times: np.ndarray) -> dict[str, float | int]:
    """Return features computed only from the positive integer processing matrix.

    No file name, benchmark bound, solver outcome, or random seed is used.
    Machine order is retained only for the adjacent-machine load correlations.
    """
    p = np.asarray(processing_times)
    if p.ndim != 2 or not p.shape[0] or not p.shape[1]:
        raise ValueError("processing_times must be a non-empty 2D matrix")
    if not np.issubdtype(p.dtype, np.integer) or np.any(p <= 0):
        raise ValueError("processing_times must contain positive integers")

    p = p.astype(np.float64, copy=False)
    job_loads = p.sum(axis=1)
    machine_loads = p.sum(axis=0)
    machine_means = p.mean(axis=0)
    machine_stds = p.std(axis=0)
    machine_cvs = np.divide(
        machine_stds, machine_means,
        out=np.zeros_like(machine_stds), where=machine_means != 0,
    )

    features: dict[str, float | int] = {
        "n_jobs": int(p.shape[0]),
        "n_machines": int(p.shape[1]),
        "jobs_per_machine": float(p.shape[0] / p.shape[1]),
        "machine_load_max_share": float(machine_loads.max() / machine_loads.sum()),
        "machine_load_min_share": float(machine_loads.min() / machine_loads.sum()),
        "machine_load_range_ratio": float(
            (machine_loads.max() - machine_loads.min()) / machine_loads.mean()
        ),
        "mean_machine_cv": float(machine_cvs.mean()),
        "std_machine_cv": float(machine_cvs.std()),
        "max_machine_cv": float(machine_cvs.max()),
    }
    features.update(_summary("processing", p))
    features.update(_summary("job_load", job_loads))
    features.update(_summary("machine_load", machine_loads))

    if p.shape[1] > 1:
        adjacent = []
        for j in range(p.shape[1] - 1):
            # Correlation across jobs for adjacent machine columns.
            a, b = p[:, j], p[:, j + 1]
            if np.std(a) > 0 and np.std(b) > 0:
                adjacent.append(float(np.corrcoef(a, b)[0, 1]))
        features["adjacent_machine_corr_mean"] = (
            float(np.mean(adjacent)) if adjacent else 0.0
        )
        features["adjacent_machine_corr_std"] = (
            float(np.std(adjacent)) if adjacent else 0.0
        )
    else:
        features["adjacent_machine_corr_mean"] = 0.0
        features["adjacent_machine_corr_std"] = 0.0

    return features


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_directory(input_dir: str | Path) -> pd.DataFrame:
    root = Path(input_dir)
    paths = sorted(root.rglob("ta*.txt"))
    if not paths:
        raise FileNotFoundError(f"No ta*.txt instances found under {root}")

    rows = []
    for path in paths:
        instance = load_taillard_instance(path)
        row = {
            "instance": path.stem,
            "sha256": sha256_file(path),
            "feature_version": FEATURE_VERSION,
            **extract_instance_features(instance.processing_times),
        }
        rows.append(row)

    frame = pd.DataFrame(rows).sort_values("instance").reset_index(drop=True)
    if frame["instance"].duplicated().any():
        raise ValueError("Duplicate instance identifiers found")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir", type=Path,
        default=Path("data/benchmarks/taillard"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("experiments/meta_learning/data/instance_features.csv"),
    )
    args = parser.parse_args()

    frame = extract_directory(args.input_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False, float_format="%.12g")
    print(f"Instances: {len(frame)}")
    print(f"Features: {len([c for c in frame if c not in {'instance', 'sha256', 'feature_version'}])}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
