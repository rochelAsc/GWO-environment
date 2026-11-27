"""Aggregate metabasis pilot into per-instance targets and selection baselines."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS = ROOT / "results/meta_learning_metabasis_pilot_v1/runs.csv"
DEFAULT_MANIFEST = ROOT / "experiments/meta_learning/data/instance_manifest.csv"
DEFAULT_OUT = ROOT / "results/meta_learning_metabasis_pilot_v1/analysis"
VARIANTS = ("baseline", "optuna", "fuzzy", "surrogate")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    with args.runs.open(newline="", encoding="utf-8") as stream:
        runs = list(csv.DictReader(stream))
    with args.manifest.open(newline="", encoding="utf-8") as stream:
        manifest = {row["instance"]: row for row in csv.DictReader(stream)}

    by: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    times: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    meta: dict[str, tuple[int, int]] = {}
    for row in runs:
        inst = row["instance"]
        by[inst][row["variant"]].append(int(row["best_makespan"]))
        times[inst][row["variant"]].append(float(row["runtime_seconds"]))
        meta[inst] = (int(row["jobs"]), int(row["machines"]))

    rows = []
    wins: dict[str, int] = defaultdict(int)
    close = 0
    for inst in sorted(by):
        means = {v: float(np.mean(by[inst][v])) for v in VARIANTS}
        stds = {v: float(np.std(by[inst][v], ddof=1)) for v in VARIANTS}
        ub_raw = manifest.get(inst, {}).get("upper_bound")
        ub = int(ub_raw) if ub_raw not in (None, "", "None") else None
        if ub:
            y = {v: means[v] / ub for v in VARIANTS}
            norm = "ub"
        else:
            best_mean = min(means.values())
            y = {v: means[v] / best_mean for v in VARIANTS}
            norm = "rel_best"
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

    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    target_path = out / "per_instance_targets.csv"
    with target_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "n_instances": len(rows),
        "n_runs": len(runs),
        "wins": dict(wins),
        "low_confidence_labels_margin_lt_0.5pct": close,
        "mean_normalized_y": {
            v: float(np.mean([r[f"y_{v}"] for r in rows])) for v in VARIANTS
        },
        "mean_regret_vs_oracle_if_always": {v: regret(v) for v in VARIANTS},
        "mean_runtime_seconds": {
            v: float(np.mean([r[f"t_mean_{v}"] for r in rows])) for v in VARIANTS
        },
        "wins_by_group": {g: dict(wins_by_group[g]) for g in sorted(wins_by_group)},
        "pairwise_mean_y": pairwise,
        "notes": [
            "Unit=instance; 3 seeds per variant aggregated by mean makespan.",
            "Normalization: UB when available else relative to best mean among variants.",
            "Pilot only; not confirmatory Meta-Learning evaluation.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"N_INST {len(rows)}")
    print(f"WINS {dict(wins)}")
    print(f"LOW_CONF {close}")
    print("MEAN_Y", {v: round(summary['mean_normalized_y'][v], 6) for v in VARIANTS})
    print("REGRET", {v: round(summary['mean_regret_vs_oracle_if_always'][v], 6) for v in VARIANTS})
    print("MEAN_T", {v: round(summary['mean_runtime_seconds'][v], 2) for v in VARIANTS})
    print("WINS_BY_GROUP")
    for group, counts in summary["wins_by_group"].items():
        print(group, counts)
    print("PAIRWISE", pairwise)
    print(f"WROTE {out}")


if __name__ == "__main__":
    main()
