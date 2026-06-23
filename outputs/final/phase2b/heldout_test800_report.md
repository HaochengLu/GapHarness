# Phase 2B Held-out Test800 Sweep

Selected profiler: `llm_single`

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 800 | 0.20 | 0.00 | 3.69 | -3.69 | 0.00 | 0.74 | 0.00 | 0.00 |
| tool_router | 800 | 0.32 | 1.96 | 3.69 | -1.72 | 0.09 | 0.62 | 0.43 | 0.06 |
| difficulty_router | 800 | 0.41 | 3.22 | 3.69 | -0.47 | 0.26 | 0.53 | 0.15 | 0.13 |
| always_full | 800 | 0.94 | 16.00 | 3.69 | 12.31 | 0.94 | 0.00 | 0.00 | 0.51 |
| gold_oracle_gap_harness | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| selected_llm_gap_harness | 800 | 0.89 | 3.59 | 3.69 | -0.09 | 0.14 | 0.09 | 0.01 | 0.05 |

Interpretation boundary: this is a held-out obligation/harness coverage evaluation, not open-world answer-level accuracy.
