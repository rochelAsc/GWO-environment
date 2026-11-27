# Taillard PFSP Meta-Learning pilot subset

This directory contains a stratified **36-instance** subset of the classical Taillard PFSP benchmark (3 instances × 12 size groups).

## Selection

| Group | Instances |
|---|---|
| 20×5 | ta001, ta002, ta003 |
| 20×10 | ta011, ta012, ta013 |
| 20×20 | ta021, ta022, ta023 |
| 50×5 | ta031, ta032, ta033 |
| 50×10 | ta041, ta042, ta043 |
| 50×20 | ta051, ta052, ta053 |
| 100×5 | ta061, ta062, ta063 |
| 100×10 | ta071, ta072, ta073 |
| 100×20 | ta081, ta082, ta083 |
| 200×10 | ta091, ta092, ta093 |
| 200×20 | ta101, ta102, ta103 |
| 500×20 | ta111, ta112, ta113 |

This is a **viability / meta-base pilot subset**. It is not by itself confirmatory evidence of Meta-Learning generalization. Larger expansions (60–120) remain conditional on cost and coverage.

## Provenance

- Benchmark: Taillard (1993), *Benchmarks for basic scheduling problems*, European Journal of Operational Research, 64(2), 278–285. DOI: https://doi.org/10.1016/0377-2217(93)90182-M
- Source mirror: [PISCO Taillard PFSP instances](https://github.com/arnaud-m/pisco/tree/master/pisco-shop/src/main/benchmarks/instances/flow-shop/taillard)
- Source files are retained in their plain-text benchmark format. The parser reads dimensions, processing times and, where available, published seed/upper/lower-bound metadata.
- The instance feature extractor records SHA-256 for each local file when generating the feature table.

Do not overwrite existing benchmark files or experimental results. New subsets or corrected source copies must be versioned and documented separately.
