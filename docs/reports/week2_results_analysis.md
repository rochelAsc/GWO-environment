# Week 2 — Taillard PFSP GWO baseline results

**Protocol:** `week2_taillard_pfsp_gwo_v1`  
**Execution environment:** Windows 11, Python 3.14.6, NumPy 2.5.1  
**Result directory:** `results/week2_baseline_v1/`

## 1. Experimental design

The experiment evaluates a synchronous Grey Wolf Optimizer (GWO) with random-key encoding on two Taillard permutation flow shop problem (PFSP) instances. The objective is makespan minimization, with no due dates.

| Parameter | Value |
|---|---:|
| Instances | ta001 (20 jobs × 5 machines), ta011 (20 jobs × 10 machines) |
| Wolves | 30 |
| Iterations | 500 |
| Independent seeds | 0–29 |
| Position encoding | 20 random keys in [0, 1], decoded by stable argsort |
| Parameter schedule | a(t) = 2 − 2t/T |
| Update semantics | Synchronous; alpha, beta and delta frozen within each generation |
| Evaluations per run | 30 × (500 + 1) = 15,030 |
| Runs | 60 |
| Total objective evaluations | 901,800 |

The initial population is evaluated once, followed by 500 generations in which all 30 wolves are evaluated. The best-so-far archive is retained across generations.

## 2. Aggregate results

| Metric | ta001 | ta011 |
|---|---:|---:|
| Runs | 30 | 30 |
| Mean best makespan | 1265.97 | 1628.53 |
| Median | 1265 | 1626 |
| Sample standard deviation | 3.55 | 8.22 |
| Best | **1265** | **1596** |
| Worst | 1279 | 1644 |
| Published upper bound (UB) | 1278 | 1582 |
| Mean runtime per run | 0.861 s | 1.351 s |
| Total measured runtime | 25.82 s | 40.53 s |

### 2.1 Comparison with published upper bounds

The UB is a published feasible-solution reference, not a proof of global optimality. Therefore, differences below are described as distances to the published UB, not as optimality gaps.

- **ta001:** 28 of 30 runs (93.3%) reached a makespan at or below the published UB. The mean is 12.03 units (0.94%) below the UB; the best result, 1265, is 13 units (1.02%) below it. Two runs returned 1279, one unit above the UB.
- **ta011:** no run reached the published UB. The best result, 1596, is 14 units (0.88%) above it. The mean is 46.53 units (2.94%) above the UB.

The results show instance-dependent performance. The baseline is effective relative to the reference on ta001, while ta011 remains harder for this configuration and budget.

## 3. Convergence

The convergence CSV contains 501 records per instance (generation 0 through 500), each aggregating the best-so-far makespan over all 30 runs.

| Convergence statistic | ta001 | ta011 |
|---|---:|---:|
| Mean at generation 0 | 1400.50 | 1875.60 |
| Mean at generation 500 | 1265.97 | 1628.53 |
| Absolute reduction | 134.53 | 247.07 |
| Relative reduction | 9.61% | 13.17% |

The mean best-so-far curve for ta001 first reaches or passes its published UB at generation 135. The mean curve for ta011 does not reach its published UB within 500 iterations. This is an aggregate-curve observation; it does not imply that every individual run crosses the bound at that generation.

Figures:
- `results/week2_baseline_v1/figures/ta001_convergence.png`
- `results/week2_baseline_v1/figures/ta011_convergence.png`

The shaded region represents ±1 sample standard deviation across the 30 runs. It is descriptive variability, not a confidence interval.

## 4. Reproducibility and artifact checks

The committed artifacts are:

- `runs.csv`: 60 run-level records, including seed, makespan, published UB, evaluation count, runtime and best permutation.
- `convergence.csv`: 1,002 records (501 generations × 2 instances).
- `metadata.json`: parameters, environment, seeds, instance dimensions, published bounds, SHA-256 hashes and aggregate statistics.
- Two convergence figures.

The metadata records 15,030 evaluations for each run. The CSV contains 30 records per instance, and each convergence series contains 501 generations. The instance hashes match the values recorded in the pilot metadata, so the same benchmark files were used.

The pilot remains preserved in `results/week2_pilot/`; the full experiment did not overwrite it.

## 5. Interpretation and limitations

1. This is a baseline experiment on two 20-job Taillard instances. It does not establish performance across the full Taillard benchmark suite or larger problem sizes.
2. The results are specific to the stated random-key representation, synchronous update semantics, parameter schedule, population, iteration budget and seeds.
3. The two instances differ in machine count; the observed performance difference should not be attributed to machine count alone from only these two cases.
4. No statistical hypothesis test is required to compare algorithms here because this experiment evaluates one configuration. A formal comparison belongs in the later multi-variant benchmarking stage and must use paired seeds and a predeclared test protocol.
5. The experiment minimizes makespan on classical single-factory PFSP. It is separate from the historical due-date tardiness experiments and the DPFSP-DD implementation.

## 6. Conclusion

The Week 2 reconstruction has been executed and its outputs have been checked. The implementation, CI tests, benchmark inputs, complete run-level data, convergence histories, metadata and figures are available in the repository.

The results provide a reproducible GWO baseline: strong performance against the published UB on ta001, but a remaining gap on ta011. This distinction should be retained in the final presentation rather than reporting only the best observed makespan.
