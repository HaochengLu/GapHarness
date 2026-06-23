# Synthetic Registry Scaling

The optimized compiler remains exact. Dominance pruning removes strictly dominated modules, and branch-and-bound prunes branches that cannot cover the profile or cannot beat the current best cost. Naive brute force is run only where feasible.

| Registry | Brute run | Brute candidates | Brute ms | Opt ms | Opt nodes | Dominated | Same cost | Same modules | Opt cost |
|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| 10 | True | 1024 | 1.66 | 0.63 | 459 | 1 | True | True | 9 |
| 20 | True | 1048576 | 2422.54 | 0.60 | 459 | 11 | True | True | 9 |
| 40 | False | 2^40 skipped | - | 0.63 | 459 | 31 | None | None | 9 |
| 80 | False | 2^80 skipped | - | 0.66 | 459 | 71 | None | None | 9 |
| 160 | False | 2^160 skipped | - | 0.74 | 459 | 151 | None | None | 9 |

Worst-case exact search remains exponential. The point of this experiment is narrower: for declared agent registries with many redundant or dominated affordance declarations, exact compilation can remain practical while preserving the same optimum as brute force on feasible sizes.
