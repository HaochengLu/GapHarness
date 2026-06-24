# Table 12. SWE-HarnessExec-20 LLM Pipeline

This experiment runs real sandbox files and pytest commands. It validates the harness execution loop with provided patches; it does not claim model patch generation or SWE-bench pass@1.

| System | N | Coverage HS | Trace Success | Avg Cost | Pre-test Failed | Post-test Passed | Missing Module Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| GapHarness LLM | 20 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |
| Registry-guarded GapHarness | 20 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |
| LLM Tool Router | 20 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |

This table supports an executable trace sanity check. It also shows a limitation: on obvious homogeneous execution-heavy fixtures, direct LLM module routing can match obligation-first profiling.
