# Table 4. Anti-Circularity Stress Tests and Negative Controls

## Registry Perturbation

| Perturbation | Removed Module | Base Harness Success | Perturbed Harness Success | Unsupported | Under-covered | Dominant Missing |
|---|---|---:|---:|---:|---:|---|
| remove_python_executor | python_executor | 1.00 | 0.00 | 1.00 | 1.00 | execution |
| remove_source_span_checker | source_span_checker | 1.00 | 0.00 | 1.00 | 1.00 | source_spans |
| remove_permission_gate | permission_gate | 1.00 | 0.00 | 1.00 | 1.00 | permission |
| remove_sandbox_file_editor | sandbox_file_editor | 1.00 | 0.00 | 1.00 | 1.00 | diff |
| remove_web_retrieval | web_retrieval | 1.00 | 0.00 | 1.00 | 1.00 | evidence_sources |
| remove_contract_verifier | contract_verifier | 1.00 | 0.00 | 1.00 | 1.00 | contract_check |

## Gold Label Permutation

| Condition | N | Harness Success | Cost Delta | Over | Under | Wrong | Verifier Fail |
|---|---:|---:|---:|---:|---:|---:|---:|
| correct gold | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| permuted labels | 200 | 0.17 | 0.24 | 0.55 | 0.83 | 0.79 | 0.83 |

Permutation integrity: 200 / 200 corrupted profiles changed obligations or required capabilities; no-op corruptions: 0.

## Negative Controls

| Category | System | N | Harness Success | Avg Cost | Over |
|---|---|---:|---:|---:|---:|
| pure_language_negative | Direct | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | Tool Router | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | LLM Tool Router | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | Difficulty Router | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | Always-full | 100 | 1.00 | 16.00 | 1.00 |
| pure_language_negative | GapHarness gold | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | GapHarness LLM | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | Registry-guarded GapHarness | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | Direct | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | Tool Router | 100 | 1.00 | 1.26 | 0.51 |
| tool_bait | LLM Tool Router | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | Difficulty Router | 100 | 1.00 | 1.22 | 0.51 |
| tool_bait | Always-full | 100 | 1.00 | 16.00 | 1.00 |
| tool_bait | GapHarness gold | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | GapHarness LLM | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | Registry-guarded GapHarness | 100 | 1.00 | 0.00 | 0.00 |
