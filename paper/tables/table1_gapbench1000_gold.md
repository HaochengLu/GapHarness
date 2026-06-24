# Table 1. GapBench-1000 Gold-Obligation Compiler Result

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 1000 | 0.20 | 0.00 | 3.67 | -3.67 | 0.00 | 0.74 | 0.00 | 0.00 |
| tool_router | 1000 | 0.34 | 2.10 | 3.67 | -1.57 | 0.11 | 0.60 | 0.42 | 0.06 |
| difficulty_router | 1000 | 0.43 | 3.46 | 3.67 | -0.21 | 0.28 | 0.51 | 0.16 | 0.14 |
| always_full | 1000 | 0.94 | 16.00 | 3.67 | 12.33 | 0.94 | 0.00 | 0.00 | 0.51 |
| gapharness | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Interpretation: under human-audited gold obligations, GapHarness matches the oracle minimal harness exactly, while baseline policies separate into under-harnessing and over-harnessing failure modes.
