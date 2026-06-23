# SWE-HarnessExec-20 Executable Trace Validation

This experiment runs real sandbox files and pytest commands. It validates the harness execution loop with provided patches; it does not claim model patch generation or SWE-bench pass@1.

| System | N | Coverage HS | Trace Success | Avg Cost | Pre-test Failed | Post-test Passed | Missing Module Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| always_full | 20 | 1.00 | 1.00 | 16.00 | 1.00 | 1.00 | 0.00 |
| difficulty_router | 20 | 0.00 | 0.00 | 6.00 | 0.00 | 0.00 | 1.00 |
| direct | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| gapharness | 20 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |
| oracle_minimal | 20 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |
| tool_router | 20 | 0.00 | 0.00 | 4.00 | 0.00 | 0.00 | 1.00 |

## Failure Interpretation

Rows that lack `file_state_reader`, `python_executor`, `execution_log_checker`, `sandbox_file_editor`, `permission_gate`, `state_store`, or `contract_verifier` stop before the executable trace. This is intentional: the experiment checks that systems without the declared affordances do not silently perform sandbox patch/test workflows.
