"""Stream-validate populations.csv without loading it entirely into memory."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from scripts.pfs_taillard import load_taillard_instance, makespan

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POP = ROOT / "results/gwo_population_distribution_audit_v1/populations.csv"
DEFAULT_RUNS = ROOT / "results/gwo_population_distribution_audit_v1/runs.csv"
DEFAULT_META = ROOT / "results/gwo_population_distribution_audit_v1/metadata.json"
DEFAULT_INSTANCE = ROOT / "data/benchmarks/taillard/ta111.txt"

EXPECTED_FIELDS = [
    "variant",
    "instance",
    "seed",
    "generation",
    "wolf_index",
    "permutation",
    "makespan",
    "is_generation_best",
    "generation_unique_permutations",
]
VARIANTS = ("baseline", "optuna", "fuzzy", "surrogate")
SEEDS = (0, 1, 2, 3, 4)
EXPECTED_ROWS = 300_600
CFG = {
    "baseline": (30, range(-1, 500)),
    "optuna": (45, range(-1, 333)),
    "fuzzy": (30, range(-1, 500)),
    "surrogate": (30, range(-1, 500)),
}
N_JOBS = 500


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--populations", type=Path, default=DEFAULT_POP)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    parser.add_argument("--instance", type=Path, default=DEFAULT_INSTANCE)
    parser.add_argument("--sample-size", type=int, default=80)
    args = parser.parse_args()

    issues: list[str] = []
    pop = args.populations.resolve()
    if not pop.is_file():
        print(f"FAIL missing file: {pop}")
        return 2

    size = pop.stat().st_size
    sha_hex = file_sha256(pop)
    print(f"FILE size_bytes={size} size_mb={size / 1024 / 1024:.2f}")
    print(f"SHA256 {sha_hex}")

    meta = json.loads(args.metadata.read_text(encoding="utf-8"))
    with args.runs.open(newline="", encoding="utf-8") as stream:
        runs_rows = list(csv.DictReader(stream))
    runs_key = {(r["variant"], r["instance"], int(r["seed"])): r for r in runs_rows}
    print(f"RUNS n={len(runs_rows)} unique_keys={len(runs_key)}")
    if len(runs_rows) != 20 or len(runs_key) != 20:
        issues.append(f"runs.csv unexpected size: rows={len(runs_rows)} unique={len(runs_key)}")

    inst = load_taillard_instance(args.instance)
    if inst.name != "ta111" or inst.n_jobs != N_JOBS:
        issues.append(f"instance load mismatch: {inst.name} jobs={inst.n_jobs}")
    instance_sha = file_sha256(args.instance.resolve())
    if instance_sha != meta["instance"]["sha256"]:
        issues.append("instance sha256 != metadata")
    if meta.get("diagnostic_exact_labels_total") != EXPECTED_ROWS:
        issues.append(
            f"metadata.diagnostic_exact_labels_total="
            f"{meta.get('diagnostic_exact_labels_total')} != {EXPECTED_ROWS}"
        )

    n_rows = 0
    bad_ncols = 0
    parse_errors = 0
    key_dup = 0
    seen_keys: set[tuple] = set()
    counts_run: Counter[tuple] = Counter()
    counts_gen: Counter[tuple] = Counter()
    wolf_set: dict[tuple, set[int]] = defaultdict(set)
    minmax_ms: dict[tuple, list[int]] = {}
    gen_range: dict[tuple, list[int]] = defaultdict(lambda: [10**9, -(10**9)])
    unique_flag_mismatch = 0
    best_flag_mismatch = 0
    perm_invalid = 0
    makespan_nonpos = 0
    instance_bad = 0
    samples: list[tuple] = []
    sample_every_gen = 100
    rng = np.random.default_rng(20261127)

    current_group = None
    group_rows: list[tuple] = []

    def flush_group(rows: list[tuple]) -> None:
        nonlocal unique_flag_mismatch, best_flag_mismatch
        if not rows:
            return
        labels = [item[1] for item in rows]
        best = min(labels)
        unique = len({item[4] for item in rows if item[4] is not None})
        # If any permutation failed parsing, skip unique check for that group.
        if unique == 0 and any(item[4] is None for item in rows):
            return
        for _wolf, ms, is_best, uniq_reported, perm_key in rows:
            if int(is_best) != int(ms == best):
                best_flag_mismatch += 1
            if perm_key is not None and int(uniq_reported) != unique:
                unique_flag_mismatch += 1

    with pop.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_FIELDS:
            print("HEADER_FAIL", reader.fieldnames)
            return 2
        for row in reader:
            n_rows += 1
            if len(row) != len(EXPECTED_FIELDS):
                bad_ncols += 1
                continue
            try:
                variant = row["variant"]
                instance = row["instance"]
                seed = int(row["seed"])
                generation = int(row["generation"])
                wolf = int(row["wolf_index"])
                ms = int(row["makespan"])
                is_best = int(row["is_generation_best"])
                uniq = int(row["generation_unique_permutations"])
                perm_tokens = row["permutation"].split()
            except Exception:
                parse_errors += 1
                continue

            if instance != "ta111":
                instance_bad += 1
            if variant not in VARIANTS or seed not in SEEDS:
                parse_errors += 1
                continue
            if ms <= 0:
                makespan_nonpos += 1

            key = (variant, instance, seed, generation, wolf)
            if key in seen_keys:
                key_dup += 1
            else:
                seen_keys.add(key)

            counts_run[(variant, seed)] += 1
            counts_gen[(variant, seed, generation)] += 1
            wolf_set[(variant, seed, generation)].add(wolf)
            lohi = minmax_ms.setdefault((variant, seed), [ms, ms])
            if ms < lohi[0]:
                lohi[0] = ms
            if ms > lohi[1]:
                lohi[1] = ms
            gr = gen_range[(variant, seed)]
            if generation < gr[0]:
                gr[0] = generation
            if generation > gr[1]:
                gr[1] = generation

            perm_key = None
            if len(perm_tokens) != N_JOBS:
                perm_invalid += 1
            else:
                try:
                    perm = [int(x) for x in perm_tokens]
                except ValueError:
                    perm_invalid += 1
                else:
                    if len(set(perm)) != N_JOBS or min(perm) != 0 or max(perm) != N_JOBS - 1:
                        perm_invalid += 1
                    else:
                        perm_key = tuple(perm)

            gkey = (variant, seed, generation)
            if current_group is None:
                current_group = gkey
            if gkey != current_group:
                flush_group(group_rows)
                group_rows = []
                current_group = gkey
            group_rows.append((wolf, ms, is_best, uniq, perm_key))

            last_gen = CFG[variant][1][-1]
            take = generation in (-1, 0, last_gen) or (
                generation > 0 and generation % sample_every_gen == 0
            )
            if take and wolf == 0 and perm_key is not None:
                samples.append((variant, seed, generation, wolf, perm_key, ms))

            if n_rows % 50_000 == 0:
                print(f"... streamed {n_rows} rows", flush=True)

        flush_group(group_rows)

    print(f"ROWS n={n_rows} expected={EXPECTED_ROWS}")
    if n_rows != EXPECTED_ROWS:
        issues.append(f"row count {n_rows} != {EXPECTED_ROWS}")

    wrong_run_count = []
    wrong_gen_structure = []
    for variant in VARIANTS:
        nwolves, gens = CFG[variant]
        for seed in SEEDS:
            count = counts_run[(variant, seed)]
            if count != 15_030:
                wrong_run_count.append((variant, seed, count))
            for generation in gens:
                cg = counts_gen[(variant, seed, generation)]
                wolves = wolf_set[(variant, seed, generation)]
                if cg != nwolves or wolves != set(range(nwolves)):
                    wrong_gen_structure.append(
                        (variant, seed, generation, cg, len(wolves))
                    )
            expected_gr = [gens[0], gens[-1]]
            if gen_range[(variant, seed)] != expected_gr:
                wrong_gen_structure.append(
                    ("gen_range", variant, seed, gen_range[(variant, seed)], expected_gr)
                )

    best_mismatch = []
    surrogate_diag_better = []
    missing_runs = []
    for (variant, seed), (mn, _mx) in sorted(minmax_ms.items()):
        rk = runs_key.get((variant, "ta111", seed))
        if not rk:
            missing_runs.append((variant, seed))
            continue
        best = int(rk["best_makespan"])
        diag = int(rk["diagnostic_exact_labels"])
        if diag != 15_030:
            issues.append(
                f"runs diagnostic_exact_labels != 15030 for {variant} seed={seed}: {diag}"
            )
        if counts_run[(variant, seed)] != diag:
            issues.append(
                f"pop count != runs.diagnostic for {variant} seed={seed}: "
                f"{counts_run[(variant, seed)]} vs {diag}"
            )
        if variant != "surrogate":
            if mn != best:
                best_mismatch.append((variant, seed, mn, best))
        elif mn < best:
            surrogate_diag_better.append((seed, mn, best))
        elif mn > best:
            best_mismatch.append((variant, seed, mn, best))

    if key_dup:
        issues.append(f"duplicate keys: {key_dup}")
    if bad_ncols:
        issues.append(f"bad ncols rows: {bad_ncols}")
    if parse_errors:
        issues.append(f"parse errors: {parse_errors}")
    if perm_invalid:
        issues.append(f"invalid permutations: {perm_invalid}")
    if makespan_nonpos:
        issues.append(f"non-positive makespan: {makespan_nonpos}")
    if instance_bad:
        issues.append(f"non-ta111 instance rows: {instance_bad}")
    if wrong_run_count:
        issues.append(f"wrong per-run counts: {wrong_run_count}")
    if wrong_gen_structure:
        issues.append(
            f"wrong gen structure examples: {wrong_gen_structure[:5]} "
            f"... n={len(wrong_gen_structure)}"
        )
    if best_mismatch:
        issues.append(f"best_makespan mismatch vs min(pop): {best_mismatch}")
    if best_flag_mismatch:
        issues.append(f"is_generation_best mismatches: {best_flag_mismatch}")
    if unique_flag_mismatch:
        issues.append(
            f"generation_unique_permutations mismatches: {unique_flag_mismatch}"
        )
    if missing_runs:
        issues.append(f"missing runs keys: {missing_runs}")

    if len(samples) > args.sample_size:
        idx = rng.choice(len(samples), size=args.sample_size, replace=False)
        samples = [samples[i] for i in sorted(idx)]

    recalc_ok = 0
    recalc_fail = []
    for variant, seed, generation, wolf, perm, ms in samples:
        got = int(makespan(inst.processing_times, list(perm)))
        if got == ms:
            recalc_ok += 1
        else:
            recalc_fail.append((variant, seed, generation, wolf, ms, got))
    if recalc_fail:
        issues.append(f"makespan recalc failures: {len(recalc_fail)}")

    print("--- STRUCTURE ---")
    covered = sum(1 for v in VARIANTS for s in SEEDS if counts_run[(v, s)] == 15_030)
    print(f"runs covered: {covered}/20")
    print(
        f"duplicate_keys={key_dup} perm_invalid={perm_invalid} parse_errors={parse_errors}"
    )
    print(
        f"best_flag_mismatch={best_flag_mismatch} "
        f"unique_flag_mismatch={unique_flag_mismatch}"
    )
    print(f"best_mismatches={best_mismatch}")
    print(
        "surrogate_diag_strictly_better_than_reported_best="
        f"{len(surrogate_diag_better)} examples={surrogate_diag_better[:5]}"
    )
    print("--- SAMPLE RECALC ---")
    print(f"samples={len(samples)} ok={recalc_ok} fail={len(recalc_fail)}")
    if recalc_fail:
        print("FAIL_EXAMPLES", recalc_fail[:5])

    print("--- VERDICT ---")
    if issues:
        print("FAIL")
        for item in issues:
            print("ISSUE:", item)
        return 1

    print("PASS")
    print(f"sha256={sha_hex}")
    print(f"rows={n_rows}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
