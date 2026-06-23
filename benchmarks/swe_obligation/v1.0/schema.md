# SWE-Obligation-50 Schema

Each JSONL row follows the GapHarness `TaskExample` schema.

- `query`: real SWE-bench Lite repository, instance, issue/task description, and test metadata wrapped as an obligation-transfer request.
- `gold_obligations`: audited obligations required by a warranted software-engineering patch workflow.
- `required_capabilities`: declared GapHarness registry capabilities needed for repository inspection, execution, sandbox action, control, state, and verification.
- `oracle_minimal_harness`: minimal declared module set under the current GapHarness registry.
- `success_checker`: always `swe_obligation_transfer_only`.
- `expected_status`: always `supported` under the current registry.

This dataset must not be used as a SWE-bench pass@1 benchmark.
