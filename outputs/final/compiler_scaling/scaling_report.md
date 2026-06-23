# Synthetic Registry Scaling

The optimized compiler remains exact. Dominance pruning removes strictly dominated modules, and branch-and-bound prunes branches that cannot cover the profile or cannot beat the current best cost. Naive brute force is run only where feasible.

| Registry | Brute run | Brute candidates | Brute ms | Opt ms | Opt nodes | Dominated | Same cost | Greedy cost | Opt cost |
|---:|---|---:|---:|---:|---:|---:|---|---:|---:|
| 10 | True | 1024 | 1.77 | 0.68 | 459 | 1 | True | 9 | 9 |
| 20 | True | 1048576 | 2382.54 | 0.63 | 459 | 11 | True | 9 | 9 |
| 40 | False | 2^40 skipped | - | 0.61 | 459 | 31 | None | 9 | 9 |
| 80 | False | 2^80 skipped | - | 0.65 | 459 | 71 | None | 9 | 9 |
| 160 | False | 2^160 skipped | - | 0.74 | 459 | 151 | None | 9 | 9 |

Worst-case exact search remains exponential. The point of this experiment is narrower: for declared agent registries with many redundant or dominated affordance declarations, exact compilation can remain practical while preserving the same optimum as brute force on feasible sizes.

## Mostly Non-Dominated Stress

This secondary stress uses overlapping modules that are intentionally much less dominance-prunable. It is a boundary diagnostic, not a performance claim.

| Registry | Brute run | Brute candidates | Brute ms | Opt ms | Opt nodes | Dominated | Same cost | Greedy cost | Opt cost |
|---:|---|---:|---:|---:|---:|---:|---|---:|---:|
| 20 | True | 1048576 | 2004.67 | 36.70 | 29417 | 0 | True | 16 | 16 |
| 30 | False | 2^30 skipped | - | 303.29 | 263301 | 0 | None | 16 | 16 |
| 40 | False | 2^40 skipped | - | 3297.16 | 3003289 | 0 | None | 16 | 16 |
