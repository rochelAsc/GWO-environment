"""Aggregate metabasis pilot into per-instance targets and selection baselines."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS = ROOT / "results/meta_learning_metabasis_pilot_v1/runs.csv"
DEFAULT_MANIFEST = ROOT / "experiments/meta_learning/data/instance_manifest.csv"
DEFAULT_OUT = ROOT / "results/meta_learning_metabasis_pilot_v1/analysis"
VARIANTS = ("baseline", "optuna", "fuzzy", "surrogate")
DEFAULT_SEEDS = (0, 1, 2)
REQUIRED_RUN_FIELDS = (
    "variant",
    "instance",
    "jobs",
    "machines",
    "seed",
    "best_makespan",
    "exact_evaluations",
    "surrogate_predictions",
    "runtime_seconds",
    "instance_sha256",
    "model_sha256",
)
NUMERIC_RUN_FIELDS = (
    "best_makespan",
    "exact_evaluations",
    "surrogate_predictions",
    "runtime_seconds",
)


class MetabasisPilotValidationError(ValueError):
    """Raised when pilot runs/manifest fail integrity checks."""


def _finite_float(row: dict[str, str], field: str) -> float:
    raw = row.get(field, "")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise MetabasisPilotValidationError(
            f"non-numeric {field} for {row.get('instance')}/{row.get('variant')}/{row.get('seed')}: {raw!r}"
        ) from exc
    if not math.isfinite(value):
        raise MetabasisPilotValidationError(
            f"non-finite {field} for {row.get('instance')}/{row.get('variant')}/{row.get('seed')}: {raw!r}"
        )
    return value


def validate_metabasis_pilot_runs(
    runs: list[dict[str, str]],
    manifest: list[dict[str, str]],
    *,
    variants: tuple[str, ...] = VARIANTS,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
) -> dict[str, object]:
    """Validate completeness, uniqueness, hashes and numeric integrity.

    Returns a compact audit dict. Raises MetabasisPilotValidationError on failure.
    """
    if not runs:
        raise MetabasisPilotValidationError("runs.csv is empty")
    if not manifest:
        raise MetabasisPilotValidationError("instance manifest is empty")

    missing_cols = [c for c in REQUIRED_RUN_FIELDS if c not in runs[0]]
    if missing_cols:
        raise MetabasisPilotValidationError(f"runs.csv missing columns: {missing_cols}")

    instances = [row["instance"] for row in manifest]
    if len(instances) != len(set(instances)):
        raise MetabasisPilotValidationError("duplicate instances in manifest")
    instance_set = set(instances)
    if not instance_set:
        raise MetabasisPilotValidationError("manifest has no instances")

    variant_set = set(variants)
    seed_set = {str(s) for s in seeds}
    expected = {(i, v, str(s)) for i in instance_set for v in variants for s in seeds}

    keys: list[tuple[str, str, str]] = []
    for row in runs:
        inst = row.get("instance", "").strip()
        variant = row.get("variant", "").strip()
        seed = str(row.get("seed", "")).strip()
        if not inst:
            raise MetabasisPilotValidationError("run with empty instance")
        if variant not in variant_set:
            raise MetabasisPilotValidationError(f"unexpected variant: {variant!r}")
        if seed not in seed_set:
            raise MetabasisPilotValidationError(
                f"unexpected seed {seed!r} for {inst}/{variant}"
            )
        if not row.get("instance_sha256", "").strip():
            raise MetabasisPilotValidationError(f"empty instance_sha256 for {inst}")
        if variant == "surrogate" and not row.get("model_sha256", "").strip():
            raise MetabasisPilotValidationError(
                f"empty model_sha256 for surrogate run {inst}/seed={seed}"
            )
        for field in NUMERIC_RUN_FIELDS:
            value = _finite_float(row, field)
            if field in ("best_makespan", "runtime_seconds") and value <= 0:
                raise MetabasisPilotValidationError(
                    f"{field} must be > 0 for {inst}/{variant}/{seed}: {value}"
                )
            if field in ("exact_evaluations", "surrogate_predictions") and value < 0:
                raise MetabasisPilotValidationError(
                    f"{field} must be >= 0 for {inst}/{variant}/{seed}: {value}"
                )
        keys.append((inst, variant, seed))

    counts = Counter(keys)
    duplicates = [k for k, n in counts.items() if n > 1]
    if duplicates:
        raise MetabasisPilotValidationError(
            f"duplicate instance/variant/seed keys: {duplicates[:5]}"
        )
    observed = set(keys)
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing:
        raise MetabasisPilotValidationError(
            f"missing {len(missing)} expected keys; first={missing[:5]}"
        )
    if extra:
        raise MetabasisPilotValidationError(
            f"extra {len(extra)} unexpected keys; first={extra[:5]}"
        )

    ub_missing = [
        row["instance"]
        for row in manifest
        if not str(row.get("upper_bound", "")).strip()
        or str(row.get("upper_bound", "")).strip() == "None"
    ]

    return {
        "n_runs": len(runs),
        "n_instances": len(instance_set),
        "variants": list(variants),
        "seeds": list(seeds),
        "missing_keys": 0,
        "extra_keys": 0,
        "duplicate_keys": 0,
        "manifest_without_ub": ub_missing,
        "ok": True,
    }


def aggregate_metabasis_pilot(
    runs: list[dict[str, str]],
    manifest_by_instance: dict[str, dict[str, str]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Build per-instance targets and summary from validated runs."""
    by: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    times: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    meta: dict[str, tuple[int, int]] = {}
    for row in runs:
        inst = row["instance"]
        by[inst][row["variant"]].append(int(float(row["best_makespan"])))
        times[inst][row["variant"]].append(float(row["runtime_seconds"]))
        meta[inst] = (int(row["jobs"]), int(row["machines"]))

    rows: list[dict[str, object]] = []
    wins: dict[str, int] = defaultdict(int)
    close = 0
    norm_counts: dict[str, int] = defaultdict(int)
    for inst in sorted(by):
        means = {v: float(np.mean(by[inst][v])) for v in VARIANTS}
        stds = {v: float(np.std(by[inst][v], ddof=1)) for v in VARIANTS}
        ub_raw = manifest_by_instance.get(inst, {}).get("upper_bound")
        ub = int(ub_raw) if ub_raw not in (None, "", "None") else None
        if ub:
            y = {v: means[v] / ub for v in VARIANTS}
            norm = "ub"
        else:
            best_mean = min(means.values())
            y = {v: means[v] / best_mean for v in VARIANTS}
            norm = "rel_best"
        norm_counts[norm] += 1
        ordered = sorted(VARIANTS, key=lambda v: y[v])
        winner = ordered[0]
        margin = y[ordered[1]] - y[winner]
        wins[winner] += 1
        if margin < 0.005:
            close += 1
        jobs, machines = meta[inst]
        rows.append({
            "instance": inst,
            "jobs": jobs,
            "machines": machines,
            "norm": norm,
            "ub": ub if ub is not None else "",
            "winner": winner,
            "margin_y": margin,
            "low_confidence": int(margin < 0.005),
            **{f"mean_{v}": means[v] for v in VARIANTS},
            **{f"std_{v}": stds[v] for v in VARIANTS},
            **{f"y_{v}": y[v] for v in VARIANTS},
            **{f"t_mean_{v}": float(np.mean(times[inst][v])) for v in VARIANTS},
        })

    def regret(choice: str) -> float:
        return float(np.mean([
            r[f"y_{choice}"] - min(r[f"y_{v}"] for v in VARIANTS) for r in rows
        ]))

    wins_by_group: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        group = f"{row['jobs']}x{row['machines']}"
        wins_by_group[group][row["winner"]] += 1

    pairwise = {}
    for i, a in enumerate(VARIANTS):
        for b in VARIANTS[i + 1 :]:
            aw = sum(1 for r in rows if r[f"y_{a}"] < r[f"y_{b}"])
            bw = sum(1 for r in rows if r[f"y_{b}"] < r[f"y_{a}"])
            pairwise[f"{a}_vs_{b}"] = {"a_wins": aw, "b_wins": bw, "ties": len(rows) - aw - bw}

    summary = {
        "n_instances": len(rows),
        "n_runs": len(runs),
        "wins": dict(wins),
        "low_confidence_labels_margin_lt_0.5pct": close,
        "normalization_counts": dict(norm_counts),
        "mean_normalized_y": {
            v: float(np.mean([r[f"y_{v}"] for r in rows])) for v in VARIANTS
        },
        "mean_regret_vs_oracle_if_always": {v: regret(v) for v in VARIANTS},
        "mean_runtime_seconds": {
            v: float(np.mean([r[f"t_mean_{v}"] for r in rows])) for v in VARIANTS
        },
        "wins_by_group": {g: dict(wins_by_group[g]) for g in sorted(wins_by_group)},
        "pairwise_mean_y": pairwise,
        "primary_selection_metric": "per_instance_regret_vs_oracle",
        "notes": [
            "Unit=instance; 3 seeds per variant aggregated by mean makespan.",
            "Normalization: UB when available else relative to best mean among variants (rel_best).",
            "When norm mixes ub and rel_best, do not treat global mean_y as one common scale; use per-instance regret.",
            "Pilot only; not confirmatory Meta-Learning evaluation.",
        ],
    }
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip integrity checks (not recommended).",
    )
    args = parser.parse_args()

    with args.runs.open(newline="", encoding="utf-8") as stream:
        runs = list(csv.DictReader(stream))
    with args.manifest.open(newline="", encoding="utf-8") as stream:
        manifest_rows = list(csv.DictReader(stream))
    manifest = {row["instance"]: row for row in manifest_rows}

    if not args.skip_validate:
        audit = validate_metabasis_pilot_runs(runs, manifest_rows)
        print("VALIDATE", {k: audit[k] for k in (
            "n_runs", "n_instances", "missing_keys", "duplicate_keys",
            "manifest_without_ub",
        )})

    rows, summary = aggregate_metabasis_pilot(runs, manifest)

    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    target_path = out / "per_instance_targets.csv"
    with target_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"N_INST {len(rows)}")
    print(f"WINS {summary['wins']}")
    print(f"LOW_CONF {summary['low_confidence_labels_margin_lt_0.5pct']}")
    print("NORM", summary["normalization_counts"])
    print("MEAN_Y", {v: round(summary['mean_normalized_y'][v], 6) for v in VARIANTS})
    print("REGRET", {v: round(summary['mean_regret_vs_oracle_if_always'][v], 6) for v in VARIANTS})
    print("MEAN_T", {v: round(summary['mean_runtime_seconds'][v], 2) for v in VARIANTS})
    print("WINS_BY_GROUP")
    for group, counts in summary["wins_by_group"].items():
        print(group, counts)
    print("PAIRWISE", summary["pairwise_mean_y"])
    print(f"WROTE {out}")


if __name__ == "__main__":
    main()
