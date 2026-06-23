# Feedback-Assisted Strategy Baselines

These are framework-independent harness-selection policies over the same declared registry, executor, and verifier. Verifier-repair, ReAct, and GapHarness-Repair receive diagnostic verifier feedback after a failed route and should be interpreted as feedback-assisted upper-bound baselines.

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong | LLM Calls | Steps | Certificate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gapharness_repair | 800 | 1.00 | 3.96 | 3.69 | 0.28 | 0.28 | 0.15 | 0.00 | 0.00 | 1.00 | 0.11 | yes |
| react_module_selector | 800 | 1.00 | 3.90 | 3.69 | 0.21 | 0.21 | 0.20 | 0.00 | 0.00 | 1.08 | 1.08 | no |
| verifier_repair_router | 800 | 1.00 | 3.85 | 3.69 | 0.16 | 0.16 | 0.14 | 0.00 | 0.00 | 1.20 | 0.20 | no |
| workflow_generator | 800 | 0.77 | 3.37 | 3.69 | -0.32 | 0.11 | 0.10 | 0.23 | 0.18 | 1.00 | 1.00 | no |

Harness success is verifier coverage, not answer-level correctness. GapHarness-Repair converts verifier diagnostics into a profile patch and recompiles with the exact compiler, preserving compiler certificates.
