# Table 15. Compiler Optimization and Scaling Ablation

Brute force is run only where feasible; optimized exact search preserves the brute-force optimum on feasible sizes.

| Registry | Brute Candidates | Brute ms | Optimized ms | Optimized Nodes | Dominated | Same Cost | Greedy Cost | Opt Cost |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 10 | 1024 | 1.77 | 0.68 | 459 | 1 | True | 9 | 9 |
| 20 | 1048576 | 2382.54 | 0.63 | 459 | 11 | True | 9 | 9 |
| 40 | 2^40 skipped | - | 0.61 | 459 | 31 | None | 9 | 9 |
| 80 | 2^80 skipped | - | 0.65 | 459 | 71 | None | 9 | 9 |
| 160 | 2^160 skipped | - | 0.74 | 459 | 151 | None | 9 | 9 |
