"""Stream descriptive stats from populations.csv without loading it whole."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POP = ROOT / "results/gwo_population_distribution_audit_v1/populations.csv"
DEFAULT_OUT = ROOT / "results/gwo_population_distribution_audit_v1/analysis"
N_JOBS = 500
ENTROPY_GENS = (-1, 0, 100, 250, 332, 499)


def shannon_entropy(counts: np.ndarray) -> float:
    total = float(counts.sum())
    if total <= 0:
        return 0.0
    probs = counts[counts > 0] / total
    return float(-(probs * np.log2(probs)).sum())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--populations", type=Path, default=DEFAULT_POP)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    pop = args.populations.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)

    # Accumulators: (variant, seed, generation) -> stats
    n = defaultdict(int)
    sum_ms = defaultdict(float)
    sumsq_ms = defaultdict(float)
    min_ms = {}
    max_ms = {}
    unique_reported = {}
    # Position counts only for selected generations: (variant, seed, gen, position) -> job counts
    pos_counts: dict[tuple, np.ndarray] = {}
    # Pair precedence sample: first 20 jobs adjacency, gens of interest only
    pair_counts: dict[tuple, np.ndarray] = {}
    n_jobs_pair = 20

    with pop.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            variant = row["variant"]
            seed = int(row["seed"])
            generation = int(row["generation"])
            ms = int(row["makespan"])
            key = (variant, seed, generation)
            n[key] += 1
            sum_ms[key] += ms
            sumsq_ms[key] += float(ms) * ms
            min_ms[key] = ms if key not in min_ms else min(min_ms[key], ms)
            max_ms[key] = ms if key not in max_ms else max(max_ms[key], ms)
            unique_reported[key] = int(row["generation_unique_permutations"])

            if generation not in ENTROPY_GENS:
                continue
            perm = [int(x) for x in row["permutation"].split()]
            if len(perm) != N_JOBS:
                continue
            pkey = (variant, seed, generation)
            if pkey not in pos_counts:
                pos_counts[pkey] = np.zeros((N_JOBS, N_JOBS), dtype=np.uint16)
                pair_counts[pkey] = np.zeros((n_jobs_pair, n_jobs_pair), dtype=np.uint32)
            for position, job in enumerate(perm):
                pos_counts[pkey][position, job] += 1
            job_pos = {job: idx for idx, job in enumerate(perm) if job < n_jobs_pair}
            for i in range(n_jobs_pair):
                for j in range(i + 1, n_jobs_pair):
                    if i not in job_pos or j not in job_pos:
                        continue
                    if job_pos[i] < job_pos[j]:
                        pair_counts[pkey][i, j] += 1
                    else:
                        pair_counts[pkey][j, i] += 1

    gen_rows = []
    for key in sorted(n):
        variant, seed, generation = key
        count = n[key]
        mean = sum_ms[key] / count
        var = max(sumsq_ms[key] / count - mean * mean, 0.0)
        gen_rows.append({
            "variant": variant,
            "seed": seed,
            "generation": generation,
            "n_wolves": count,
            "unique_permutations": unique_reported[key],
            "unique_ratio": unique_reported[key] / count,
            "makespan_mean": mean,
            "makespan_std": math.sqrt(var),
            "makespan_min": min_ms[key],
            "makespan_max": max_ms[key],
        })

    gen_path = out / "by_generation.csv"
    with gen_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(gen_rows[0]))
        writer.writeheader()
        writer.writerows(gen_rows)

    # Aggregate across seeds: mean unique_ratio and makespan_mean by variant/generation
    agg: dict[tuple, list] = defaultdict(list)
    for row in gen_rows:
        agg[(row["variant"], row["generation"])].append(row)
    agg_rows = []
    for (variant, generation), rows in sorted(agg.items()):
        uniq = [r["unique_ratio"] for r in rows]
        means = [r["makespan_mean"] for r in rows]
        mins = [r["makespan_min"] for r in rows]
        agg_rows.append({
            "variant": variant,
            "generation": generation,
            "n_seeds": len(rows),
            "unique_ratio_mean": float(np.mean(uniq)),
            "unique_ratio_std": float(np.std(uniq, ddof=1)) if len(uniq) > 1 else 0.0,
            "makespan_mean_mean": float(np.mean(means)),
            "makespan_mean_std": float(np.std(means, ddof=1)) if len(means) > 1 else 0.0,
            "best_of_seed_means_min": float(np.min(mins)),
        })
    agg_path = out / "by_generation_agg.csv"
    with agg_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(agg_rows[0]))
        writer.writeheader()
        writer.writerows(agg_rows)

    entropy_rows = []
    for pkey, counts in sorted(pos_counts.items()):
        variant, seed, generation = pkey
        position_entropy = [shannon_entropy(counts[pos].astype(np.float64)) for pos in range(N_JOBS)]
        mean_ent = float(np.mean(position_entropy))
        # Uniform max entropy for discrete jobs over population size is log2(min(n_wolves, n_jobs))
        # Report raw mean entropy over positions.
        pair = pair_counts[pkey]
        decided = 0
        ties = 0
        for i in range(n_jobs_pair):
            for j in range(i + 1, n_jobs_pair):
                a = int(pair[i, j])
                b = int(pair[j, i])
                if a == b:
                    ties += 1
                else:
                    decided += 1
        entropy_rows.append({
            "variant": variant,
            "seed": seed,
            "generation": generation,
            "mean_position_entropy_bits": mean_ent,
            "min_position_entropy_bits": float(np.min(position_entropy)),
            "max_position_entropy_bits": float(np.max(position_entropy)),
            "pair_precedence_decided_among_first20_jobs": decided,
            "pair_precedence_tied_among_first20_jobs": ties,
        })
    ent_path = out / "diversity_snapshots.csv"
    with ent_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(entropy_rows[0]))
        writer.writeheader()
        writer.writerows(entropy_rows)

    # Compact summary JSON for report
    def snapshot(variant: str, generation: int) -> dict:
        rows = [r for r in entropy_rows if r["variant"] == variant and r["generation"] == generation]
        if not rows:
            return {}
        return {
            "n_seeds": len(rows),
            "mean_position_entropy_bits": float(np.mean([r["mean_position_entropy_bits"] for r in rows])),
            "unique_ratio_mean": float(np.mean([
                next(
                    g["unique_ratio"]
                    for g in gen_rows
                    if g["variant"] == variant and g["seed"] == r["seed"] and g["generation"] == generation
                )
                for r in rows
            ])),
        }

    summary = {
        "protocol": "gwo_population_distribution_audit_v1",
        "rows_scanned_expected": 300_600,
        "artifacts": {
            "by_generation": str(gen_path.relative_to(ROOT)),
            "by_generation_agg": str(agg_path.relative_to(ROOT)),
            "diversity_snapshots": str(ent_path.relative_to(ROOT)),
        },
        "entropy_generations": list(ENTROPY_GENS),
        "initial_vs_late": {
            variant: {
                "generation_-1": snapshot(variant, -1),
                "generation_late": snapshot(variant, 499 if variant != "optuna" else 332),
            }
            for variant in ("baseline", "optuna", "fuzzy", "surrogate")
        },
        "notes": [
            "Observations within a trajectory are dependent; do not treat candidates as iid.",
            "Kendall-tau skipped: O(n^2) on 500-job perms at this volume is not viable for full audit.",
            "Pair precedence counts order among job ids 0..19 only.",
        ],
    }
    summary_path = out / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {gen_path}")
    print(f"wrote {agg_path}")
    print(f"wrote {ent_path}")
    print(f"wrote {summary_path}")


if __name__ == "__main__":
    main()
