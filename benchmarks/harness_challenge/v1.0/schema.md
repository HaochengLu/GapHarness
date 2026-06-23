# HarnessChallenge-200 Schema

Each JSONL row follows `gapharness.schema.TaskExample`.

- `task_id`: stable row identifier.
- `query`: user-facing request.
- `gold_obligations`: audited obligation set.
- `required_capabilities`: registry capabilities required to satisfy the obligation profile.
- `oracle_minimal_harness`: lowest-cost declared module set under the default registry.
- `expected_status`: `supported` or `unsupported` under the declared registry.
- `category`: one of the six targeted diagnostic categories.
- `gold_source`: author-reviewed diagnostic provenance.

This schema is intentionally label-centric; it tests harness synthesis, not answer correctness.
