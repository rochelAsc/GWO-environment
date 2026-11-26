# Taillard PFSP pilot subset

This directory contains a stratified 12-instance subset of the classical Taillard PFSP benchmark.

## Selection

| Instance | Jobs | Machines | Group |
|---|---:|---:|---|
| ta001 | 20 | 5 | 20×5 |
| ta011 | 20 | 10 | 20×10 |
| ta021 | 20 | 20 | 20×20 |
| ta031 | 50 | 5 | 50×5 |
| ta041 | 50 | 10 | 50×10 |
| ta051 | 50 | 20 | 50×20 |
| ta061 | 100 | 5 | 100×5 |
| ta071 | 100 | 10 | 100×10 |
| ta081 | 100 | 20 | 100×20 |
| ta091 | 200 | 10 | 200×10 |
| ta101 | 200 | 20 | 200×20 |
| ta111 | 500 | 20 | 500×20 |

One instance was selected from each of the 12 standard Taillard size groups. This is a **technical pilot subset**, not a statistically sufficient training or test dataset. Additional replicates from each group should be considered only after measuring runtime and validating the feature extractor.

## Provenance

- Benchmark: Taillard (1993), *Benchmarks for basic scheduling problems*, European Journal of Operational Research, 64(2), 278–285. DOI: https://doi.org/10.1016/0377-2217(93)90182-M
- Source mirror: [PISCO Taillard PFSP instances](https://github.com/arnaud-m/pisco/tree/master/pisco-shop/src/main/benchmarks/instances/flow-shop/taillard)
- Source files are retained in their plain-text benchmark format. The parser reads dimensions, processing times and, where available, published seed/upper/lower-bound metadata.
- The instance feature extractor records SHA-256 for each local file when generating the feature table.

Do not overwrite existing benchmark files or experimental results. New subsets or corrected source copies must be versioned and documented separately.
