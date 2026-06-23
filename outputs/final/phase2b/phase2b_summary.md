# Phase 2B Summary: LLM Profiler Calibration + Held-out Test Sweep

## Deterministic Boundary

Checkpoint: `phase2-deterministic-artifacts-v1`

Phase 2B evaluates LLM-inferred obligations only. It does not modify GapBench v1.0 labels, compiler rules, deterministic baselines, or Phase 2 gold results.

## Dev200 Calibration

Profilers evaluated:

- `llm_single`
- `llm_recall`
- `llm_minimality`

Selection rule:

1. under_harness_rate must be <= 0.08
2. success must be >= 0.90
3. among satisfying profilers, choose the lowest minimality regret
4. if none satisfy, choose `llm_recall` and report calibration as an open limitation

Dev200 summary:

| Profiler | Success | Avg Cost | Regret | Over | Under | Wrong | Obl P | Obl R | Obl F1 | Exact Set |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_single | 0.92 | 3.68 | 0.06 | 0.19 | 0.08 | 0.00 | 0.905 | 0.955 | 0.929 | 0.79 |
| llm_recall | 0.96 | 3.94 | 0.32 | 0.20 | 0.04 | 0.00 | 0.895 | 0.969 | 0.930 | 0.80 |
| llm_minimality | 0.98 | 3.82 | 0.20 | 0.14 | 0.02 | 0.00 | 0.929 | 0.969 | 0.949 | 0.86 |

Selected primary profiler: `llm_single`.

## Held-out Test800

Only the selected profiler was evaluated on test800.

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 800 | 0.20 | 0.00 | 3.69 | -3.69 | 0.00 | 0.74 | 0.00 | 0.00 |
| tool_router | 800 | 0.32 | 1.96 | 3.69 | -1.72 | 0.09 | 0.62 | 0.43 | 0.06 |
| difficulty_router | 800 | 0.41 | 3.22 | 3.69 | -0.47 | 0.26 | 0.53 | 0.15 | 0.13 |
| always_full | 800 | 0.94 | 16.00 | 3.69 | 12.31 | 0.94 | 0.00 | 0.00 | 0.51 |
| gold_oracle_gap_harness | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| selected_llm_gap_harness | 800 | 0.89 | 3.59 | 3.69 | -0.09 | 0.14 | 0.09 | 0.01 | 0.05 |

## Interpretation

The selected LLM profiler substantially improves over Direct, Tool Router, and Difficulty Router at near-oracle cost, but it does not yet match Always-full sufficiency. Always-full reaches 0.94 success by paying 16.00 average cost and 0.94 over-harness rate; selected LLM GapHarness reaches 0.89 success at 3.59 average cost.

The held-out result is therefore best framed as a calibration result, not a solved-profiler result. The current profiler is practical enough to support the paper's API-only harness synthesis story, but the remaining under-harness rate is an explicit limitation.

## Main Error Pattern

The dominant under-harness pattern is capability lowering rather than obligation recognition alone. Several failures predict the right high-level obligations but include `real_world_side_effect`, which the MVP registry intentionally does not cover for sandbox/mock actions. This causes the compiler to return `unsupported` even when the benchmark expects a sandbox-supported harness.

Recommended next step: add a dev-only registry guard or cascade that trims `real_world_side_effect` unless the query explicitly asks for a real irreversible external action. This should be treated as a new calibrated profiler variant and evaluated under a new held-out protocol, not silently folded into the current test result.
