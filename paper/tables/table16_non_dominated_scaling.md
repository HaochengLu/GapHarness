# Table 16. Mostly Non-Dominated Registry Scaling Stress

This secondary scaling stress is intentionally less dominance-prunable. It documents the exact compiler boundary rather than claiming polynomial scaling.

| Registry | Brute Candidates | Brute ms | Optimized ms | Optimized Nodes | Dominated | Same Cost | Greedy Cost | Opt Cost |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 20 | 1048576 | 2004.67 | 36.70 | 29417 | 0 | True | 16 | 16 |
| 30 | 2^30 skipped | - | 303.29 | 263301 | 0 | None | 16 | 16 |
| 40 | 2^40 skipped | - | 3297.16 | 3003289 | 0 | None | 16 | 16 |
