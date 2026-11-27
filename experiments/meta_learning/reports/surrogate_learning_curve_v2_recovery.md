# Recovery of the v2 surrogate learning curve after OOM

## Source data and preservation

The interrupted source directory is treated as immutable:

`results/meta_learning_surrogate_learning_curve_v2_extension/`

The recovery runner reads the 57 existing training-diagnostic NPZ files and both fixed test sets. It writes recovered outputs to a separate directory and never overwrites the interrupted source.

The 57 existing NPZ files were opened and checked locally on 2026-11-26: 59 NPZ files were found (57 training diagnostics plus two fixed test sets), all 59 were readable, and no arrays were empty or contained non-finite numeric values. This establishes structural integrity, not semantic correctness by itself.

## Recovery implementation

Run from the repository root, using the same virtual environment and SciPy version as the interrupted experiment if possible:

```bash
python -m experiments.meta_learning.scripts.recover_surrogate_learning_curve_v2 \
  --source results/meta_learning_surrogate_learning_curve_v2_extension \
  --output results/meta_learning_surrogate_learning_curve_v2_extension_recovered
```

The runner:

1. Reuses each saved permutation matrix and reconstructs normalized-rank features and exact PFSP makespan labels.
2. Regenerates the missing rep-5 uniform sequence from its original seed and verifies its first 8,000 permutations against the already-saved NPZ before using the 16,000 and 32,000 prefixes.
3. Regenerates the missing rep-5, 32,000-point LHS design from the original deterministic seed and the v2 global-LHS procedure.
4. Fits one MLP at a time, appending each completed result to `recovered_runs.jsonl`.
5. Can be rerun with the same command: completed record keys are skipped and remaining records continue.
6. Writes missing diagnostic NPZ files and final CSV/metadata only in the recovery output directory.

The implementation avoids Python sets of 500-element integer tuples. Duplicate checks use the raw bytes of each fixed-width permutation row. Model fitting is sequential, with large arrays released after each record.

## Expected workload

- Instances: ta071 and ta111.
- Sample sizes: 8,000, 16,000, 32,000.
- Sampling methods: global LHS random keys and nested uniform permutations.
- Repetitions: 5.
- Expected model fits: 60.

## Interpretation and limitations

Recovered metrics are recomputed from the saved permutations, the original fixed test sets, and the exact makespan implementation. They are not recovered from the interrupted process memory.

The following original measurements cannot be reconstructed because the original run did not checkpoint them:

- Dataset-generation and exact-labeling wall-clock times.
- The software-version metadata that would have been written only after all instances completed.

The recovery report therefore labels training times as measurements from the recovery execution, not the original execution. The original v2 top-k calculation uses `argsort` and does not resolve makespan ties specially; this behavior is retained for comparability and must remain a stated limitation.

The missing LHS design is deterministic for the same NumPy/SciPy implementation and seed. Because the interrupted run never wrote its environment metadata, use the same local virtual environment where possible and record the versions reported by the recovery metadata.

## Safety

Do not delete, rename, or modify the original extension directory. Inspect the recovered output and its checkpoint count before considering any later consolidation.
