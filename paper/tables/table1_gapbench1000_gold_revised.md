# Table 1. GapBench-1000 Gold-Profile Compiler Result

This table validates obligation-coverage compilation under gold profiles. Harness success is not answer-level semantic correctness.

| System | N | Harness Success | Declared Cost | Oracle Declared Cost | Cost Delta | Excess Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 1000 | 0.20 | 0.00 | 3.67 | -3.67 | 0.00 | 0.00 | 0.74 | 0.00 |
| tool_router | 1000 | 0.34 | 2.10 | 3.67 | -1.57 | 0.27 | 0.11 | 0.60 | 0.42 |
| difficulty_router | 1000 | 0.43 | 3.46 | 3.67 | -0.21 | 1.47 | 0.28 | 0.51 | 0.16 |
| always_full | 1000 | 0.94 | 16.00 | 3.67 | 12.33 | 12.33 | 0.94 | 0.00 | 0.00 |
| gapharness | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
