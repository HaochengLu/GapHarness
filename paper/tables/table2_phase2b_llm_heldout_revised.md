# Table 2. LLM-Inferred Profiles on GapBench Test800

This table measures held-out harness-coverage success for inferred profiles. It does not claim the profiler is fully calibrated.

| System | N | Harness Success | Declared Cost | Oracle Declared Cost | Cost Delta | Excess Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 800 | 0.20 | 0.00 | 3.69 | -3.69 | 0.00 | 0.00 | 0.74 | 0.00 |
| tool_router | 800 | 0.32 | 1.96 | 3.69 | -1.72 | 0.25 | 0.09 | 0.62 | 0.43 |
| difficulty_router | 800 | 0.41 | 3.22 | 3.69 | -0.47 | 1.34 | 0.26 | 0.53 | 0.15 |
| always_full | 800 | 0.94 | 16.00 | 3.69 | 12.31 | 12.31 | 0.94 | 0.00 | 0.00 |
| gold_oracle_gap_harness | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| selected_llm_gap_harness | 800 | 0.89 | 3.59 | 3.69 | -0.09 | 0.37 | 0.14 | 0.09 | 0.01 |
