# Compiler Equivalence Replay

Replay checks whether the optimized exact compiler preserves frozen harness outputs. Certificates are new metadata and are ignored for equality.

| Frozen Experiment | N | Status changed | Harness changed | Cost changed | Avg Nodes | Avg Dominated |
|---|---:|---:|---:|---:|---:|---:|
| gapbench1000_gold | 6000 | 0 | 0 | 0 | 24.4 | 0.0 |
| harness_challenge_gold | 1200 | 0 | 0 | 0 | 14.8 | 0.0 |
| harness_challenge_guarded | 200 | 0 | 0 | 0 | 87.0 | 0.0 |
| harness_challenge_llm | 200 | 0 | 0 | 0 | 82.0 | 0.0 |
| harness_challenge_router | 200 | 0 | 0 | 0 | 0.0 | 0.0 |
| harness_exec20 | 120 | 0 | 0 | 0 | 22.3 | 0.0 |
| test800_llm | 5600 | 0 | 0 | 0 | 33.0 | 0.0 |
| test800_registry_guarded | 800 | 0 | 0 | 0 | 93.2 | 0.0 |

## Changed Rows

No status, module, or cost changes were observed.
