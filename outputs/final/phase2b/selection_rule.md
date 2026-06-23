# Phase 2B Primary Profiler Selection

Rule:

1. under_harness_rate must be <= 0.08
2. success must be >= 0.90
3. among satisfying profilers, choose the lowest minimality regret
4. if none satisfy, choose `llm_recall` and report calibration as an open limitation

| Profiler | Pass Rule | Success | Under | Regret |
|---|---:|---:|---:|---:|
| llm_single | yes | 0.92 | 0.08 | 0.06 |
| llm_recall | yes | 0.96 | 0.04 | 0.32 |
| llm_minimality | yes | 0.98 | 0.02 | 0.20 |

Selected primary profiler: `llm_single`.

Selection rationale: the profiler satisfies the sufficiency guard and has the lowest regret among passing candidates
