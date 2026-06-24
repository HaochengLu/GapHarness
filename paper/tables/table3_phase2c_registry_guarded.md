# Table 3. Phase 2C Registry-Guarded Profiler Calibration

| Split | Profiler | N | Success | Avg Cost | Regret | Over | Under | Wrong | Unsupported FP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dev200 | Phase 2B llm_single | 200 | 0.92 | 3.68 | 0.06 | 0.19 | 0.08 | 0.00 | 14 |
| dev200 | Phase 2C registry_guarded | 200 | 0.97 | 4.02 | 0.40 | 0.20 | 0.03 | 0.00 | 4 |
| test800 | Phase 2B selected llm_single | 800 | 0.89 | 3.59 | -0.09 | 0.14 | 0.09 | 0.01 | 56 |
| test800 | Phase 2C registry_guarded | 800 | 0.94 | 3.98 | 0.30 | 0.15 | 0.03 | 0.01 | 12 |

Interpretation: registry guarding reduces unsupported false positives and under-harnessing by repairing sandbox/mock action lowering, at the cost of slightly higher cost and regret.
