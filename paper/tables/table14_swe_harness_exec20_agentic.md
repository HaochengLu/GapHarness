# Table 14. SWE-HarnessExec-20 Feedback-Assisted Baselines

Executable trace validation uses provided patches. It is not model patch generation or SWE-bench pass@1.

| System | N | Coverage HS | Trace Success | Cost | Missing Module Rate | LLM Calls | Steps | Certificate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| GapHarness LLM | 20 | 1.00 | 1.00 | 12.00 | 0.00 | 1.00 | 1.00 | yes |
| Registry-guarded GH | 20 | 1.00 | 1.00 | 12.00 | 0.00 | 1.00 | 1.00 | yes |
| LLM Tool Router | 20 | 1.00 | 1.00 | 12.00 | 0.00 | 1.00 | 1.00 | no |
| Workflow Generator | 20 | 1.00 | 1.00 | 12.00 | 0.00 | 1.00 | 1.00 | no |
| Verifier-Repair Router | 20 | 1.00 | 1.00 | 12.00 | 0.00 | 1.00 | 0.00 | no |
| ReAct Module Selector | 20 | 1.00 | 1.00 | 12.00 | 0.00 | 1.00 | 1.00 | no |
| GapHarness-Repair | 20 | 1.00 | 1.00 | 12.00 | 0.00 | 1.00 | 0.00 | yes |
