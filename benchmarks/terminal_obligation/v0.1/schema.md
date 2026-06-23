# Terminal-Bench-obligation50 v0.1 Schema

This scaffold is derived from public Terminal-Bench task instructions for human review and is not human-audited gold.

Each JSONL row contains:

- `task_id`: stable id such as `terminal-obligation-001`.
- `category`: one of `execution_only`, `observation_execution`, `state_execution_verification`, `sandbox_action_control_state_verification`, `ambiguous_terminal_target`, `unsupported_real_system_mutation`.
- `query`: terminal-style user task description.
- `gold_obligations`: candidate obligations from the GapHarness ontology.
- `required_capabilities`: candidate required capabilities under the MVP registry.
- `oracle_minimal_harness`: candidate minimal module list under the MVP registry.
- `expected_status`: `supported`, `clarify`, or `unsupported`.
- `expected_failure_if_direct`: expected reason direct answering is insufficient.
- `risk_level`: `low`, `medium`, or `high`.
- `success_checker`: currently `gold_obligation_capability_coverage`.
- `tags`: search and review tags.
- `gold_source`: always `generated_for_human_review_pending_audit`.
- `source_dataset`: public dataset id used for task text extraction.
- `source_split`: source split.
- `source_task_id`: original Terminal-Bench task id.
- `source_category`: source category when available.
- `source_difficulty`: source difficulty when available.
- `source_tags`: source task tags when available.
- `notes`: audit caveat.

This benchmark is for obligation labeling and harness selection over Terminal-Bench-derived instructions, not full Terminal-Bench container solving.
