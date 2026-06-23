# Phase 2B Primary Profiler Selection

Rule:

1. under_harness_rate must be <= 0.08
2. success must be >= 0.90
3. among satisfying profilers, choose the lowest minimality regret
4. if none satisfy, choose `llm_recall` and report calibration as an open limitation

| Profiler | Pass Rule | Success | Under | Regret |
|---|---:|---:|---:|---:|
| llm_single | no | 0.69 | 0.15 | 0.45 |

Selected primary profiler: `llm_recall`.

Selection rationale: no profiler satisfied both sufficiency guards, so recall-biased profiling is selected as the conservative limitation path
