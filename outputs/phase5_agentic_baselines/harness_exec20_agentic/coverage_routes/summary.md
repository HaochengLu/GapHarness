# Feedback-Assisted Strategy Baselines

These are framework-independent harness-selection policies over the same declared registry, executor, and verifier. Verifier-repair, ReAct, and GapHarness-Repair receive diagnostic verifier feedback after a failed route and should be interpreted as feedback-assisted upper-bound baselines.

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong | LLM Calls | Steps | Certificate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gapharness_repair | 20 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | yes |
| react_module_selector | 20 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | no |
| verifier_repair_router | 20 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | no |
| workflow_generator | 20 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | no |

Harness success is verifier coverage, not answer-level correctness. GapHarness-Repair converts verifier diagnostics into a profile patch and recompiles with the exact compiler, preserving compiler certificates.
