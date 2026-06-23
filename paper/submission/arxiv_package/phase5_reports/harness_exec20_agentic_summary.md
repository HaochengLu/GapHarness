# SWE-HarnessExec-20 Executable Trace Validation

This experiment runs real sandbox files and pytest commands. It validates the harness execution loop with provided patches; it does not claim model patch generation or SWE-bench pass@1.

| System | N | Coverage HS | Trace Success | Avg Cost | Pre-test Failed | Post-test Passed | Missing Module Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| gapharness_repair | 20 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |
| react_module_selector | 20 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |
| verifier_repair_router | 20 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |
| workflow_generator | 20 | 1.00 | 1.00 | 12.00 | 1.00 | 1.00 | 0.00 |

## Failure Interpretation

Rows that lack `file_state_reader`, `python_executor`, `execution_log_checker`, `sandbox_file_editor`, `permission_gate`, `state_store`, or `contract_verifier` stop before the executable trace. This is intentional: the experiment checks that systems without the declared affordances do not silently perform sandbox patch/test workflows.

## Agentic Cost

| System | LLM Calls | Steps | Certificate |
|---|---:|---:|---|
| gapharness_repair | 1.00 | 0.00 | yes |
| react_module_selector | 1.00 | 1.00 | no |
| verifier_repair_router | 1.00 | 0.00 | no |
| workflow_generator | 1.00 | 1.00 | no |
