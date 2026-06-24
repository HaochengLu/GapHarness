# Phase 2D Stress Test 2: Gold Label Permutation

This is not a realistic corruption model. It is an anti-circularity stress test showing that the compiler is sensitive to obligation semantics.

Protocol: the compiler receives corrupted obligation profiles, while the verifier still checks against the original human-audited gold labels.

| Condition | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Verifier Fail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gapharness_correct_gold | 200 | 1.00 | 2.86 | 2.86 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| gapharness_permuted_gold_input | 200 | 0.17 | 3.10 | 2.86 | 0.24 | 0.55 | 0.83 | 0.79 | 0.83 |

Permutation integrity: 200 / 200 corrupted profiles changed obligations or required capabilities; no-op corruptions: 0.

## Corruption Actions

| Action | Count | Success | Under | Wrong |
|---|---:|---:|---:|---:|
| add_control | 24 | 1.00 | 0.00 | 0.00 |
| add_control,forced_semantic_change | 16 | 0.00 | 1.00 | 1.00 |
| delete_verification | 5 | 0.00 | 1.00 | 1.00 |
| delete_verification,avoid_empty_profile_by_adding_control | 4 | 0.00 | 1.00 | 1.00 |
| delete_verification,forced_semantic_change | 31 | 0.00 | 1.00 | 1.00 |
| drop_primary_action | 8 | 0.00 | 1.00 | 1.00 |
| drop_primary_control | 3 | 0.00 | 1.00 | 1.00 |
| drop_primary_control,avoid_empty_profile_by_adding_control,forced_semantic_change | 5 | 0.00 | 1.00 | 1.00 |
| drop_primary_execution | 3 | 0.00 | 1.00 | 1.00 |
| drop_primary_execution,avoid_empty_profile_by_adding_control | 5 | 0.00 | 1.00 | 1.00 |
| drop_primary_observation | 1 | 0.00 | 1.00 | 1.00 |
| drop_primary_observation,avoid_empty_profile_by_adding_control | 8 | 0.00 | 1.00 | 1.00 |
| drop_primary_state,avoid_empty_profile_by_adding_control | 3 | 0.00 | 1.00 | 1.00 |
| drop_primary_verification,avoid_empty_profile_by_adding_control | 4 | 0.00 | 1.00 | 1.00 |
| swap_action_state | 17 | 0.53 | 0.47 | 0.47 |
| swap_action_state,forced_semantic_change | 23 | 0.00 | 1.00 | 0.78 |
| swap_observation_execution | 21 | 0.00 | 1.00 | 1.00 |
| swap_observation_execution,forced_semantic_change | 19 | 0.00 | 1.00 | 0.79 |

## Representative Failures

| Task | Actions | Harness Status | Failures | Original Gold | Corrupted Profile | Query |
|---|---|---|---|---|---|---|
| single-001 | swap_observation_execution | supported | missing_obligations:Observation,missing_capabilities:evidence_sources,dependency_or_constraint_failure | Observation | Execution | For case 1, find the latest public announcement for ExampleProduct 1 with sources. |
| single-002 | swap_action_state,forced_semantic_change | supported | missing_obligations:Observation,missing_capabilities:workspace_inspection,dependency_or_constraint_failure | Observation | Execution | For case 2, inspect the workspace README for ExampleProject 2. |
| single-003 | delete_verification,forced_semantic_change | supported | missing_obligations:Observation,missing_capabilities:evidence_sources,dependency_or_constraint_failure | Observation | Execution | For case 3, find the latest public announcement for ExampleProduct 3 with sources. |
| single-005 | drop_primary_execution,avoid_empty_profile_by_adding_control | supported | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | Execution | Control | For case 5, calculate exactly 42 * 16. |
| single-006 | swap_observation_execution | supported | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | Execution | Observation | For case 6, calculate exactly 43 * 17. |
| single-007 | swap_action_state | supported | missing_capabilities:durable_state,dependency_or_constraint_failure | State | Action,Control | For case 7, create a durable checklist checkpoint for three subtasks. |
| single-008 | delete_verification,forced_semantic_change | supported | missing_capabilities:durable_state,dependency_or_constraint_failure | State | Action,Control | For case 8, create a durable checklist checkpoint for three subtasks. |
| single-010 | drop_primary_action | supported | missing_obligations:Action,missing_capabilities:diff,dependency_or_constraint_failure | Action,Control,State | Control,State | For case 10, create file sandbox_note_10.txt in the sandbox workspace; then apply a permission ga... |
| single-011 | swap_observation_execution,forced_semantic_change | supported | missing_obligations:Action,missing_capabilities:diff,dependency_or_constraint_failure | Action,Control,State | Control,State | For case 11, create file sandbox_note_11.txt in the sandbox workspace; then apply a permission ga... |
| single-013 | delete_verification,forced_semantic_change | supported | missing_obligations:Control,missing_capabilities:permission,dependency_or_constraint_failure | Control | Execution | For case 13, apply a permission gate before any risky step. |
| single-014 | add_control,forced_semantic_change | supported | missing_obligations:Control,missing_capabilities:permission,dependency_or_constraint_failure | Control | Execution | For case 14, apply a permission gate before any risky step. |
| single-015 | drop_primary_control,avoid_empty_profile_by_adding_control,forced_semantic_change | supported | missing_obligations:Control,missing_capabilities:permission,dependency_or_constraint_failure | Control | Execution | For case 15, apply a permission gate before any risky step. |
| single-016 | swap_observation_execution,forced_semantic_change | supported | missing_obligations:Verification,missing_capabilities:contract_check,dependency_or_constraint_failure | Verification |  | For case 16, validate the final answer against the requested contract. |
| single-017 | swap_action_state,forced_semantic_change | supported | missing_obligations:Verification,missing_capabilities:contract_check,dependency_or_constraint_failure | Verification |  | For case 17, validate the final answer against the requested contract. |
| single-018 | delete_verification,avoid_empty_profile_by_adding_control | supported | missing_obligations:Verification,missing_capabilities:contract_check,dependency_or_constraint_failure | Verification | Control | For case 18, validate the final answer against the requested contract. |
| pair-002 | drop_primary_execution | supported | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | Execution,Observation | Observation | For case 2, inspect the workspace README for ExampleProject 2; then calculate exactly 39 * 13. |
| pair-003 | swap_observation_execution | supported | missing_obligations:Observation,missing_capabilities:evidence_sources,dependency_or_constraint_failure | Observation,State | Execution,State | For case 3, find the latest public announcement for ExampleProduct 3 with sources; then create a ... |
| pair-004 | swap_action_state | supported | missing_capabilities:durable_state,dependency_or_constraint_failure | Observation,State | Action,Control,Observation | For case 4, inspect the workspace README for ExampleProject 4; then create a durable checklist ch... |
| pair-005 | delete_verification,forced_semantic_change | supported | missing_obligations:Observation,missing_capabilities:evidence_sources,dependency_or_constraint_failure | Action,Control,Observation,State | Action,Control,Execution,State | For case 5, find the latest public announcement for ExampleProduct 5 with sources; then create fi... |
| pair-006 | add_control,forced_semantic_change | supported | missing_obligations:Observation,missing_capabilities:workspace_inspection,dependency_or_constraint_failure | Action,Control,Observation,State | Action,Control,Execution,State | For case 6, inspect the workspace README for ExampleProject 6; then create file sandbox_note_6.tx... |
