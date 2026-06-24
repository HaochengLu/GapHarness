# Table 10. Compiler Equivalence Replay

Replay checks whether the optimized exact compiler preserves frozen harness outputs. Certificates are new metadata and are ignored for equality.

| Frozen Experiment | N | Status Changed | Harness Changed | Cost Changed | Avg Nodes | Avg Dominated |
|---|---:|---:|---:|---:|---:|---:|
| GapBench-1000 gold | 6000 | 0 | 0 | 0 | 24.4 | 0.0 |
| test800 LLM replay | 5600 | 0 | 0 | 0 | 33.0 | 0.0 |
| test800 registry-guarded | 800 | 0 | 0 | 0 | 93.2 | 0.0 |
| HarnessChallenge gold | 1200 | 0 | 0 | 0 | 14.8 | 0.0 |
| HarnessChallenge LLM/guarded/router | 600 | 0 | 0 | 0 | - | - |
| SWE-HarnessExec-20 | 120 | 0 | 0 | 0 | 22.3 | 0.0 |

This table supports extensional equivalence on frozen profiles/routes. It does not claim that certificates are independently proof-checked by an external verifier.
