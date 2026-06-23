# Table 13. Feedback-Assisted Strategy Baselines

All strategies run over the same declared registry, executor, and verifier. Verifier-repair, ReAct, and GapHarness-Repair use verifier diagnostics after failed routes and are feedback-assisted upper-bound baselines.

| Dataset | System | N | HS | Cost | Excess | Over | Under | Wrong | LLM Calls | Steps | Certificate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GapBench test800 | GapHarness LLM | 800 | 0.89 | 3.59 | 0.37 | 0.14 | 0.09 | 0.01 | 1.00 | 1.00 | yes |
| GapBench test800 | Registry-guarded GH | 800 | 0.94 | 3.98 | 0.38 | 0.15 | 0.03 | 0.01 | 1.00 | 1.00 | yes |
| GapBench test800 | LLM Tool Router | 800 | 0.80 | 3.51 | 0.13 | 0.12 | 0.20 | 0.17 | 1.00 | 1.00 | no |
| GapBench test800 | Workflow Generator | 800 | 0.77 | 3.37 | 0.11 | 0.10 | 0.23 | 0.18 | 1.00 | 1.00 | no |
| GapBench test800 | Verifier-Repair Router | 800 | 1.00 | 3.85 | 0.16 | 0.14 | 0.00 | 0.00 | 1.20 | 0.20 | no |
| GapBench test800 | ReAct Module Selector | 800 | 1.00 | 3.90 | 0.21 | 0.20 | 0.00 | 0.00 | 1.08 | 1.08 | no |
| GapBench test800 | GapHarness-Repair | 800 | 1.00 | 3.96 | 0.28 | 0.15 | 0.00 | 0.00 | 1.00 | 0.11 | yes |
| HarnessChallenge-200 | GapHarness LLM | 200 | 0.69 | 3.92 | 0.96 | 0.05 | 0.15 | 0.11 | 1.00 | 1.00 | yes |
| HarnessChallenge-200 | Registry-guarded GH | 200 | 0.59 | 4.82 | 1.86 | 0.05 | 0.15 | 0.11 | 1.00 | 1.00 | yes |
| HarnessChallenge-200 | LLM Tool Router | 200 | 0.65 | 2.60 | 0.04 | 0.01 | 0.35 | 0.28 | 1.00 | 1.00 | no |
| HarnessChallenge-200 | Workflow Generator | 200 | 0.83 | 3.31 | 0.10 | 0.03 | 0.17 | 0.17 | 1.00 | 1.00 | no |
| HarnessChallenge-200 | Verifier-Repair Router | 200 | 1.00 | 3.62 | 0.15 | 0.04 | 0.00 | 0.00 | 1.41 | 0.41 | no |
| HarnessChallenge-200 | ReAct Module Selector | 200 | 1.00 | 3.63 | 0.15 | 0.04 | 0.00 | 0.00 | 1.22 | 1.22 | no |
| HarnessChallenge-200 | GapHarness-Repair | 200 | 1.00 | 3.69 | 0.21 | 0.05 | 0.00 | 0.00 | 1.00 | 0.30 | yes |
