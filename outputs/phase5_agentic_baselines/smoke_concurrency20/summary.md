# Strong Agentic Strategy Baselines

These are framework-independent harness-selection policies over the same declared registry, executor, and verifier.

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong | LLM Calls | Steps | Certificate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| react_module_selector | 20 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | no |
| verifier_repair_router | 20 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | no |
| workflow_generator | 20 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | no |

Harness success is verifier coverage, not answer-level correctness. Verifier-repair and ReAct-style baselines receive verifier feedback after failed routes; this intentionally gives them a stronger agentic loop than one-shot routing.
