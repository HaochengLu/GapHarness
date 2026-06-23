# Table 8. Cost-Model Sensitivity

Costs are recomputed analytically on existing selected modules; no new experiment is run.

| Variant | System | N | Harness Success | Recomputed Cost | Oracle Cost | Cost Delta |
|---|---|---:|---:|---:|---:|---:|
| default | direct | 1000 | 0.20 | 0.00 | 3.67 | -3.67 |
| default | tool_router | 1000 | 0.34 | 2.10 | 3.67 | -1.57 |
| default | difficulty_router | 1000 | 0.43 | 3.46 | 3.67 | -0.21 |
| default | always_full | 1000 | 0.94 | 16.00 | 3.67 | 12.33 |
| default | gapharness | 1000 | 1.00 | 3.67 | 3.67 | 0.00 |
| execution_x2 | direct | 1000 | 0.20 | 0.00 | 4.32 | -4.32 |
| execution_x2 | tool_router | 1000 | 0.34 | 2.47 | 4.32 | -1.85 |
| execution_x2 | difficulty_router | 1000 | 0.43 | 4.13 | 4.32 | -0.18 |
| execution_x2 | always_full | 1000 | 0.94 | 19.00 | 4.32 | 14.68 |
| execution_x2 | gapharness | 1000 | 1.00 | 4.32 | 4.32 | 0.00 |
| verification_x2 | direct | 1000 | 0.20 | 0.00 | 4.13 | -4.13 |
| verification_x2 | tool_router | 1000 | 0.34 | 2.10 | 4.13 | -2.02 |
| verification_x2 | difficulty_router | 1000 | 0.43 | 4.04 | 4.13 | -0.09 |
| verification_x2 | always_full | 1000 | 0.94 | 19.00 | 4.13 | 14.87 |
| verification_x2 | gapharness | 1000 | 1.00 | 4.13 | 4.13 | 0.00 |
