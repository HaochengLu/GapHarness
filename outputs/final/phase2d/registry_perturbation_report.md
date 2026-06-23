# Phase 2D Stress Test 1: Registry Perturbation

Registry perturbation verifies that GapHarness does not silently hallucinate support when required affordances are absent; it degrades into unsupported or under-covered status.

| Perturbation | Removed Module | Condition | N | Success | Unsupported | Under-covered | Verifier Fail | Boundary Failure | Dominant Missing Capabilities |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| remove_python_executor | python_executor | base_registry | 60 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | - |
| remove_python_executor | python_executor | perturbed_registry | 60 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | execution:60 |
| remove_source_span_checker | source_span_checker | base_registry | 60 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | - |
| remove_source_span_checker | source_span_checker | perturbed_registry | 60 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | source_spans:60 |
| remove_permission_gate | permission_gate | base_registry | 60 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | - |
| remove_permission_gate | permission_gate | perturbed_registry | 60 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | permission:60 |
| remove_sandbox_file_editor | sandbox_file_editor | base_registry | 60 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | - |
| remove_sandbox_file_editor | sandbox_file_editor | perturbed_registry | 60 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | diff:60 |
| remove_web_retrieval | web_retrieval | base_registry | 60 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | - |
| remove_web_retrieval | web_retrieval | perturbed_registry | 60 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | evidence_sources:60 |
| remove_contract_verifier | contract_verifier | base_registry | 60 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | - |
| remove_contract_verifier | contract_verifier | perturbed_registry | 60 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | contract_check:60 |

## Example Failures

| Perturbation | Task | Status | Missing Capabilities | Verifier Failures | Query |
|---|---|---|---|---|---|
| remove_python_executor | single-004 | unsupported | execution | expected_supported | For case 4, calculate exactly 41 * 15. |
| remove_python_executor | single-005 | unsupported | execution | expected_supported | For case 5, calculate exactly 42 * 16. |
| remove_python_executor | single-006 | unsupported | execution | expected_supported | For case 6, calculate exactly 43 * 17. |
| remove_python_executor | pair-001 | unsupported | execution | expected_supported | For case 1, find the latest public announcement for ExampleProduct 1 with sources; then calculate exactly 38 * 12. |
| remove_python_executor | pair-002 | unsupported | execution | expected_supported | For case 2, inspect the workspace README for ExampleProject 2; then calculate exactly 39 * 13. |
| remove_source_span_checker | pair-009 | unsupported | source_spans | expected_supported | For case 9, find the latest public announcement for ExampleProduct 9 with sources; then validate the final answer aga... |
| remove_source_span_checker | pair-010 | unsupported | source_spans | expected_supported | For case 10, find the latest public announcement for ExampleProduct 10 with sources; then validate the final answer a... |
| remove_source_span_checker | triple-004 | unsupported | source_spans | expected_supported | For case 4, find the latest public announcement for ExampleProduct 4 with sources; then calculate exactly 41 * 15; th... |
| remove_source_span_checker | triple-007 | unsupported | source_spans | expected_supported | For case 7, find the latest public announcement for ExampleProduct 7 with sources; then create a durable checklist ch... |
| remove_source_span_checker | triple-009 | unsupported | source_spans | expected_supported | For case 9, find the latest public announcement for ExampleProduct 9 with sources; then create file sandbox_note_9.tx... |
| remove_permission_gate | single-010 | unsupported | permission | expected_supported | For case 10, create file sandbox_note_10.txt in the sandbox workspace; then apply a permission gate before any risky ... |
| remove_permission_gate | single-011 | unsupported | permission | expected_supported | For case 11, create file sandbox_note_11.txt in the sandbox workspace; then apply a permission gate before any risky ... |
| remove_permission_gate | single-012 | unsupported | permission | expected_supported | For case 12, create file sandbox_note_12.txt in the sandbox workspace; then apply a permission gate before any risky ... |
| remove_permission_gate | single-013 | unsupported | permission | expected_supported | For case 13, apply a permission gate before any risky step. |
| remove_permission_gate | single-014 | unsupported | permission | expected_supported | For case 14, apply a permission gate before any risky step. |
| remove_sandbox_file_editor | single-010 | unsupported | diff | expected_supported | For case 10, create file sandbox_note_10.txt in the sandbox workspace; then apply a permission gate before any risky ... |
| remove_sandbox_file_editor | single-011 | unsupported | diff | expected_supported | For case 11, create file sandbox_note_11.txt in the sandbox workspace; then apply a permission gate before any risky ... |
| remove_sandbox_file_editor | single-012 | unsupported | diff | expected_supported | For case 12, create file sandbox_note_12.txt in the sandbox workspace; then apply a permission gate before any risky ... |
| remove_sandbox_file_editor | pair-005 | unsupported | diff | expected_supported | For case 5, find the latest public announcement for ExampleProduct 5 with sources; then create file sandbox_note_5.tx... |
| remove_sandbox_file_editor | pair-006 | unsupported | diff | expected_supported | For case 6, inspect the workspace README for ExampleProject 6; then create file sandbox_note_6.txt in the sandbox wor... |
| remove_web_retrieval | single-001 | unsupported | evidence_sources | expected_supported | For case 1, find the latest public announcement for ExampleProduct 1 with sources. |
| remove_web_retrieval | single-003 | unsupported | evidence_sources | expected_supported | For case 3, find the latest public announcement for ExampleProduct 3 with sources. |
| remove_web_retrieval | pair-001 | unsupported | evidence_sources | expected_supported | For case 1, find the latest public announcement for ExampleProduct 1 with sources; then calculate exactly 38 * 12. |
| remove_web_retrieval | pair-003 | unsupported | evidence_sources | expected_supported | For case 3, find the latest public announcement for ExampleProduct 3 with sources; then create a durable checklist ch... |
| remove_web_retrieval | pair-005 | unsupported | evidence_sources | expected_supported | For case 5, find the latest public announcement for ExampleProduct 5 with sources; then create file sandbox_note_5.tx... |
| remove_contract_verifier | single-016 | unsupported | contract_check | expected_supported | For case 16, validate the final answer against the requested contract. |
| remove_contract_verifier | single-017 | unsupported | contract_check | expected_supported | For case 17, validate the final answer against the requested contract. |
| remove_contract_verifier | single-018 | unsupported | contract_check | expected_supported | For case 18, validate the final answer against the requested contract. |
| remove_contract_verifier | pair-009 | unsupported | contract_check | expected_supported | For case 9, find the latest public announcement for ExampleProduct 9 with sources; then validate the final answer aga... |
| remove_contract_verifier | pair-010 | unsupported | contract_check | expected_supported | For case 10, find the latest public announcement for ExampleProduct 10 with sources; then validate the final answer a... |
