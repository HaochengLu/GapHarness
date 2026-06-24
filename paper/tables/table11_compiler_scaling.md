# Table 11. Synthetic Registry Scaling

The optimized compiler remains exact. Dominance pruning removes strictly dominated modules, and branch-and-bound prunes branches that cannot cover the profile or cannot beat the current best cost.

| Registry | Brute Candidates | Brute ms | Opt ms | Opt Nodes | Dominated | Opt Cost |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 1,024 | 1.66 | 0.63 | 459 | 1 | 9 |
| 20 | 1,048,576 | 2422.54 | 0.60 | 459 | 11 | 9 |
| 40 | skipped | - | 0.63 | 459 | 31 | 9 |
| 80 | skipped | - | 0.66 | 459 | 71 | 9 |
| 160 | skipped | - | 0.74 | 459 | 151 | 9 |

This table supports practical scaling on redundant synthetic registries. It does not claim polynomial-time exact compilation.
