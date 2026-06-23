# Phase 2B Primary Profiler Selection

Rule:

1. under_harness_rate must be <= 0.08
2. success must be >= 0.90
3. among satisfying profilers, choose the lowest minimality regret
4. if none satisfy, choose `llm_recall` and report calibration as an open limitation

| Profiler | Pass Rule | Success | Under | Regret |
|---|---:|---:|---:|---:|
| llm_single | yes | 1.00 | 0.00 | 0.80 |

Selected primary profiler: `llm_single`.

Selection rationale: the profiler satisfies the sufficiency guard and has the lowest regret among passing candidates
