# Compiler Certificate Samples

These samples show checkable compiler certificates across supported, direct, unsupported, and perturbed-registry cases.

| Type | Task | Status | Cost | Modules | Missing Capabilities | Algorithm | Nodes |
|---|---|---|---:|---|---|---|---:|
| gapbench_supported | single-001 | supported | 3 | web_retrieval | - | dominance_pruned_branch_and_bound | 597 |
| gapbench_supported | single-002 | supported | 2 | file_state_reader | - | dominance_pruned_branch_and_bound | 65 |
| gapbench_supported | single-003 | supported | 3 | web_retrieval | - | dominance_pruned_branch_and_bound | 597 |
| gapbench_supported | single-004 | supported | 2 | python_executor | - | dominance_pruned_branch_and_bound | 61 |
| gapbench_supported | single-005 | supported | 2 | python_executor | - | dominance_pruned_branch_and_bound | 61 |
| gapbench_direct | pure-001 | supported | 0 | - | - | dominance_pruned_branch_and_bound | 0 |
| gapbench_direct | pure-002 | supported | 0 | - | - | dominance_pruned_branch_and_bound | 0 |
| gapbench_direct | pure-003 | supported | 0 | - | - | dominance_pruned_branch_and_bound | 0 |
| gapbench_direct | pure-004 | supported | 0 | - | - | dominance_pruned_branch_and_bound | 0 |
| gapbench_direct | pure-005 | supported | 0 | - | - | dominance_pruned_branch_and_bound | 0 |
| challenge_unsupported | harness-challenge-101 | unsupported | 0 | - | external_email_send,real_world_side_effect | dominance_pruned_branch_and_bound | 1 |
| challenge_unsupported | harness-challenge-102 | unsupported | 0 | - | payment_capture,real_world_side_effect | dominance_pruned_branch_and_bound | 1 |
| challenge_unsupported | harness-challenge-103 | unsupported | 0 | - | production_deploy,real_world_side_effect | dominance_pruned_branch_and_bound | 1 |
| challenge_unsupported | harness-challenge-104 | unsupported | 0 | - | real_world_side_effect,ticket_purchase | dominance_pruned_branch_and_bound | 1 |
| challenge_unsupported | harness-challenge-105 | unsupported | 0 | - | production_database_write,real_world_side_effect | dominance_pruned_branch_and_bound | 1 |
| perturb_remove_python_executor | harness-challenge-004 | unsupported | 0 | - | execution | dominance_pruned_branch_and_bound | 1 |
| perturb_remove_python_executor | harness-challenge-008 | unsupported | 0 | - | execution | dominance_pruned_branch_and_bound | 1 |
| perturb_remove_python_executor | harness-challenge-012 | unsupported | 0 | - | execution | dominance_pruned_branch_and_bound | 1 |
| perturb_remove_python_executor | harness-challenge-016 | unsupported | 0 | - | execution | dominance_pruned_branch_and_bound | 1 |
| perturb_remove_python_executor | harness-challenge-020 | unsupported | 0 | - | execution | dominance_pruned_branch_and_bound | 1 |
