"""Evaluate frozen surrogate ranking utility on real GWO population rows."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
from scipy.stats import spearmanr

from scripts.run_week4_surrogate import permutation_features

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POP = ROOT / "results/gwo_population_distribution_audit_v1/populations.csv"
DEFAULT_MODEL = ROOT / "results/meta_learning_cost_pilot_v2/surrogates/ta111/surrogate.joblib"
DEFAULT_OUT = ROOT / "results/gwo_population_distribution_audit_v1/analysis"
# Subsample generations to keep runtime bounded while covering trajectory.
GEN_KEEP = {-1, 0, 1, 2, 5, 10, 25, 50, 100, 150, 200, 250, 300, 332, 400, 450, 499}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def topk_recall(exact: np.ndarray, pred: np.ndarray, k: int) -> float:
    true_top = set(np.argsort(exact, kind="stable")[:k].tolist())
    pred_top = set(np.argsort(pred, kind="stable")[:k].tolist())
    return len(true_top & pred_top) / float(k)


def topk_regret(exact: np.ndarray, pred: np.ndarray, k: int) -> float:
    true_best = float(np.min(exact))
    pred_top = np.argsort(pred, kind="stable")[:k]
    selected_best = float(np.min(exact[pred_top]))
    return selected_best - true_best


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--populations", type=Path, default=DEFAULT_POP)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--variants", nargs="+", default=["surrogate", "baseline"])
    args = parser.parse_args()

    model_path = args.model.resolve()
    model = joblib.load(model_path)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    variants = set(args.variants)

    rows_out: list[dict] = []
    current = None
    buffer: list[tuple[list[int], int]] = []

    def flush(key: tuple, items: list[tuple[list[int], int]]) -> None:
        if not items:
            return
        variant, seed, generation = key
        perms = [perm for perm, _ in items]
        exact = np.asarray([ms for _, ms in items], dtype=np.float64)
        features = np.vstack([permutation_features(np.asarray(p, dtype=np.int64)) for p in perms])
        pred = np.asarray(model.predict(features), dtype=np.float64)
        if pred.shape != exact.shape:
            raise ValueError(f"prediction shape mismatch at {key}")
        rho = float(spearmanr(exact, pred).statistic) if len(exact) >= 3 else float("nan")
        rmse = float(np.sqrt(np.mean((pred - exact) ** 2)))
        rows_out.append({
            "variant": variant,
            "seed": seed,
            "generation": generation,
            "n": len(exact),
            "rmse": rmse,
            "spearman": rho,
            "recall_top3": topk_recall(exact, pred, 3),
            "regret_top3": topk_regret(exact, pred, 3),
            "recall_top10": topk_recall(exact, pred, min(10, len(exact))),
            "regret_top10": topk_regret(exact, pred, min(10, len(exact))),
            "exact_best": float(np.min(exact)),
            "pred_selected_best_top3": float(
                np.min(exact[np.argsort(pred, kind="stable")[:3]])
            ),
        })

    with args.populations.resolve().open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            variant = row["variant"]
            if variant not in variants:
                continue
            generation = int(row["generation"])
            if generation not in GEN_KEEP:
                continue
            seed = int(row["seed"])
            key = (variant, seed, generation)
            perm = [int(x) for x in row["permutation"].split()]
            ms = int(row["makespan"])
            if current is None:
                current = key
            if key != current:
                flush(current, buffer)
                buffer = []
                current = key
            buffer.append((perm, ms))
        flush(current, buffer)

    detail_path = out / "surrogate_ranking_on_gwo_populations.csv"
    with detail_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows_out[0]))
        writer.writeheader()
        writer.writerows(rows_out)

    # Aggregate by variant (and early vs late)
    def agg(subset: list[dict]) -> dict:
        if not subset:
            return {}
        keys = ["rmse", "spearman", "recall_top3", "regret_top3", "recall_top10", "regret_top10"]
        return {
            "n_generations": len(subset),
            **{f"{k}_mean": float(np.nanmean([r[k] for r in subset])) for k in keys},
            **{f"{k}_median": float(np.nanmedian([r[k] for r in subset])) for k in keys},
        }

    summary: dict = {
        "model_path": str(model_path.relative_to(ROOT)),
        "model_sha256": sha256(model_path),
        "populations": str(args.populations.resolve().relative_to(ROOT)),
        "generations_evaluated": sorted(GEN_KEEP),
        "variants": sorted(variants),
        "by_variant": {},
        "by_variant_late": {},
        "decision_inputs": {
            "ranking_is_within_generation": True,
            "top_k_operational": 3,
            "note": (
                "Utility for surrogate-assisted GWO is within-generation top-k recall/"
                "regret, not global RMSE on random permutations."
            ),
        },
    }
    by_variant: dict[str, list] = defaultdict(list)
    for row in rows_out:
        by_variant[row["variant"]].append(row)
    for variant, subset in by_variant.items():
        summary["by_variant"][variant] = agg(subset)
        late = [r for r in subset if int(r["generation"]) >= 250]
        summary["by_variant_late"][variant] = agg(late)

    summary_path = out / "surrogate_ranking_on_gwo_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {detail_path} rows={len(rows_out)}")
    print(f"wrote {summary_path}")
    print(json.dumps(summary["by_variant"], indent=2))


if __name__ == "__main__":
    main()
