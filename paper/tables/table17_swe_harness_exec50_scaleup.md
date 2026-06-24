# Table 17. SWE-HarnessExec-50 Scale-Up

This table extends the executable trace check from 20 to 50 sandbox fixtures. It validates provided-patch pytest traces only; it is not SWE-bench pass@1 or model patch generation.

| System | N | Coverage HS | Trace Success | Cost | Pre-test Failed | Post-test Passed | Missing Module Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct | 50 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| Tool Router | 50 | 0.00 | 0.00 | 4.00 | 0.00 | 0.00 | 1.00 |
| Difficulty Router | 50 | 0.00 | 0.00 | 6.00 | 0.00 | 0.00 | 1.00 |
| Always-full | 50 | 1.00 | 1.00 | 16.00 | 1.00 | 1.00 | 0.00 |
| GapHarness gold | 50 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |
| Oracle minimal | 50 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |
