# Feedback-Assisted Strategy Baselines

These are framework-independent harness-selection policies over the same declared registry, executor, and verifier. Verifier-repair, ReAct, and GapHarness-Repair receive diagnostic verifier feedback after a failed route and should be interpreted as feedback-assisted upper-bound baselines.

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong | LLM Calls | Steps | Certificate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gapharness_repair | 200 | 1.00 | 3.69 | 3.48 | 0.21 | 0.21 | 0.05 | 0.00 | 0.00 | 1.00 | 0.30 | yes |
| react_module_selector | 200 | 1.00 | 3.63 | 3.48 | 0.15 | 0.15 | 0.04 | 0.00 | 0.00 | 1.22 | 1.22 | no |
| verifier_repair_router | 200 | 1.00 | 3.62 | 3.48 | 0.15 | 0.15 | 0.04 | 0.00 | 0.00 | 1.41 | 0.41 | no |
| workflow_generator | 200 | 0.83 | 3.31 | 3.48 | -0.17 | 0.10 | 0.03 | 0.17 | 0.17 | 1.00 | 1.00 | no |

Harness success is verifier coverage, not answer-level correctness. GapHarness-Repair converts verifier diagnostics into a profile patch and recompiles with the exact compiler, preserving compiler certificates.
