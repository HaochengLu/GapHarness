# Schema

| Field | Type / Description |
|---|---|
| `category` | Dataset category. |
| `expected_failure_if_direct` | Expected failure mode for direct LLM response. |
| `expected_status` | supported / unsupported / clarify. |
| `gold_obligations` | Human-audited external obligations. |
| `gold_source` | Gold label provenance. |
| `notes` | Audit and provenance notes. |
| `oracle_minimal_harness` | Human-audited or compiled oracle minimal module set under the declared registry. |
| `query` | User-facing task query. |
| `required_capabilities` | Capabilities required from selected modules. |
| `risk_level` | low / medium / high. |
| `success_checker` | Verifier contract used for this task. |
| `tags` | Auxiliary tags. |
| `task_id` | Stable task identifier. |
