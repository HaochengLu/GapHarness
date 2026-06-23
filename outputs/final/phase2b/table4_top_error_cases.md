# Table 4. Dev200 Top Error Cases

## llm_single

### Under-harness

| Rank | Task | Category | Gold | Predicted | Status | Cost | Regret | Failures | Query |
|---:|---|---|---|---|---|---:|---:|---|---|
| 1 | single-028 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | For generated case 28, calculate the mean of 65, 43, 34, and 108 to two decimals. |
| 2 | single-021 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | For generated case 21, compute the exact total of [58, 35, 90, 10]. |
| 3 | pair-046 | pairwise_obligation | Control,State | Control,State | unsupported | 0 | -2.00 | expected_supported | For generated case 46, record an intermediate artifact for review batch 0046 so the nex... |
| 4 | pair-038 | pairwise_obligation | Control,Observation | Control,Observation | unsupported | 0 | -3.00 | expected_supported | For generated case 38, open the local CHANGELOG.md for ExampleProject tau and summarize... |
| 5 | pair-016 | pairwise_obligation | Control,Execution | Control,Execution | unsupported | 0 | -3.00 | expected_supported | For case 16, calculate exactly 53 * 27; then apply a permission gate before any risky s... |
| 6 | pair-015 | pairwise_obligation | Control,Execution | Control,Execution | unsupported | 0 | -3.00 | expected_supported | For case 15, calculate exactly 52 * 26; then apply a permission gate before any risky s... |
| 7 | single-030 | single_obligation | Action,Control,State | Action,Control,State | unsupported | 0 | -5.00 | expected_supported | For generated case 30, update sandbox_config_0030.json with a mock flag enabled=true af... |
| 8 | pair-050 | pairwise_obligation | Action,Control,State | Action,Control,State | unsupported | 0 | -5.00 | expected_supported | For generated case 50, update sandbox_config_0050.json with a mock flag enabled=true af... |
| 9 | pair-020 | pairwise_obligation | Action,Control,State | Action,Control,State | unsupported | 0 | -5.00 | expected_supported | For case 20, create file sandbox_note_20.txt in the sandbox workspace; then apply a per... |
| 10 | pair-019 | pairwise_obligation | Action,Control,State | Action,Control,State | unsupported | 0 | -5.00 | expected_supported | For case 19, create file sandbox_note_19.txt in the sandbox workspace; then apply a per... |
| 11 | pair-036 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State | unsupported | 0 | -7.00 | expected_supported | For generated case 36, inspect the workspace file release_notes.md for ExampleProject r... |
| 12 | pair-014 | pairwise_obligation | Action,Control,Execution,State | Action,Control,Execution,State | unsupported | 0 | -7.00 | expected_supported | For case 14, calculate exactly 51 * 25; then create file sandbox_note_14.txt in the san... |
| 13 | pair-013 | pairwise_obligation | Action,Control,Execution,State | Action,Control,Execution,State | unsupported | 0 | -7.00 | expected_supported | For case 13, calculate exactly 50 * 24; then create file sandbox_note_13.txt in the san... |
| 14 | pair-006 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State | unsupported | 0 | -7.00 | expected_supported | For case 6, inspect the workspace README for ExampleProject 6; then create file sandbox... |
| 15 | pair-035 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State | unsupported | 0 | -8.00 | expected_supported | For generated case 35, find the latest public announcement for ExampleProduct Lantern a... |
| 16 | pair-005 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State,Verification | unsupported | 0 | -8.00 | expected_supported | For case 5, find the latest public announcement for ExampleProduct 5 with sources; then... |

### Over-harness

| Rank | Task | Category | Gold | Predicted | Status | Cost | Regret | Failures | Query |
|---:|---|---|---|---|---|---:|---:|---|---|
| 1 | triple-029 | triple_obligation | Action,Control,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 16 | 7.00 | - | For generated case 29, find a current public FAQ entry for ExampleProduct Flux and repo... |
| 2 | triple-022 | triple_obligation | Execution,Observation,State | Execution,Observation,State,Verification | supported | 10 | 5.00 | - | For generated case 22, open the local src/main.py for ExampleProject gamma and summariz... |
| 3 | single-022 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | For generated case 22, record an intermediate artifact for review batch 0022 so the nex... |
| 4 | single-008 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | For case 8, create a durable checklist checkpoint for three subtasks. |
| 5 | single-007 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | For case 7, create a durable checklist checkpoint for three subtasks. |
| 6 | pair-052 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 9 | 5.00 | - | For generated case 52, inspect the workspace file package.json for ExampleProject nu an... |
| 7 | single-027 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | For generated case 27, check the workspace artifact config.yaml for ExampleProject thet... |
| 8 | single-020 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | For generated case 20, inspect the workspace file tasks/todo.md for ExampleProject alph... |
| 9 | pair-044 | pairwise_obligation | Execution,Verification | Execution,Observation,Verification | supported | 8 | 4.00 | - | For generated case 44, parse the inline numbers 81, 32, 13, 592 and return their exact ... |
| 10 | triple-025 | triple_obligation | Control,Execution,Observation | Control,Execution,Observation,Verification | supported | 9 | 3.00 | - | For generated case 25, find the latest public announcement for ExampleProduct Beacon an... |
| 11 | triple-023 | triple_obligation | Action,Control,Execution,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 13 | 3.00 | - | For generated case 23, retrieve the most recent public pricing or plan information for ... |
| 12 | pair-001 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 8 | 3.00 | - | For case 1, find the latest public announcement for ExampleProduct 1 with sources; then... |
| 13 | triple-033 | triple_obligation | Observation,State,Verification | Observation,State,Verification | supported | 8 | 2.00 | - | For generated case 33, retrieve the most recent public pricing or plan information for ... |
| 14 | triple-031 | triple_obligation | Control,Observation,State | Control,Observation,State,Verification | supported | 7 | 2.00 | - | For generated case 31, look up the current public documentation page for ExampleProduct... |
| 15 | triple-026 | triple_obligation | Control,Execution,Observation | Control,Execution,Observation,Verification | supported | 7 | 2.00 | - | For generated case 26, open the local CHANGELOG.md for ExampleProject eta and summarize... |
| 16 | triple-024 | triple_obligation | Action,Control,Execution,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 11 | 2.00 | - | For generated case 24, inspect the workspace file release_notes.md for ExampleProject e... |
| 17 | triple-021 | triple_obligation | Execution,Observation,State | Execution,Observation,State,Verification | supported | 8 | 2.00 | - | For generated case 21, look up the current public documentation page for ExampleProduct... |
| 18 | single-003 | single_obligation | Observation | Observation,Verification | supported | 5 | 2.00 | - | For case 3, find the latest public announcement for ExampleProduct 3 with sources. |
| 19 | single-001 | single_obligation | Observation | Observation,Verification | supported | 5 | 2.00 | - | For case 1, find the latest public announcement for ExampleProduct 1 with sources. |
| 20 | pair-051 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 7 | 2.00 | - | For generated case 51, look up the current public documentation page for ExampleProduct... |

### Wrong-harness

| Rank | Task | Category | Gold | Predicted | Status | Cost | Regret | Failures | Query |
|---:|---|---|---|---|---|---:|---:|---|---|
| - | none | - | - | - | - | - | - | - | - |

## llm_recall

### Under-harness

| Rank | Task | Category | Gold | Predicted | Status | Cost | Regret | Failures | Query |
|---:|---|---|---|---|---|---:|---:|---|---|
| 1 | single-028 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | For generated case 28, calculate the mean of 65, 43, 34, and 108 to two decimals. |
| 2 | single-021 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | For generated case 21, compute the exact total of [58, 35, 90, 10]. |
| 3 | pair-038 | pairwise_obligation | Control,Observation | Control,Observation | unsupported | 0 | -3.00 | expected_supported | For generated case 38, open the local CHANGELOG.md for ExampleProject tau and summarize... |
| 4 | pair-036 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State | unsupported | 0 | -7.00 | expected_supported | For generated case 36, inspect the workspace file release_notes.md for ExampleProject r... |
| 5 | pair-006 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State,Verification | unsupported | 0 | -7.00 | expected_supported | For case 6, inspect the workspace README for ExampleProject 6; then create file sandbox... |
| 6 | pair-035 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State | unsupported | 0 | -8.00 | expected_supported | For generated case 35, find the latest public announcement for ExampleProduct Lantern a... |
| 7 | pair-005 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State,Verification | unsupported | 0 | -8.00 | expected_supported | For case 5, find the latest public announcement for ExampleProduct 5 with sources; then... |

### Over-harness

| Rank | Task | Category | Gold | Predicted | Status | Cost | Regret | Failures | Query |
|---:|---|---|---|---|---|---:|---:|---|---|
| 1 | single-022 | single_obligation | State | Action,Control,State,Verification | supported | 7 | 6.00 | - | For generated case 22, record an intermediate artifact for review batch 0022 so the nex... |
| 2 | pair-002 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 10 | 6.00 | - | For case 2, inspect the workspace README for ExampleProject 2; then calculate exactly 3... |
| 3 | single-036 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | For generated case 36, create a durable checklist checkpoint named checkpoint_0036 with... |
| 4 | single-029 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | For generated case 29, save the decision "use minimal harness" under durable state key ... |
| 5 | single-008 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | For case 8, create a durable checklist checkpoint for three subtasks. |
| 6 | single-007 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | For case 7, create a durable checklist checkpoint for three subtasks. |
| 7 | pair-052 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 9 | 5.00 | - | For generated case 52, inspect the workspace file package.json for ExampleProject nu an... |
| 8 | pair-008 | pairwise_obligation | Control,Observation | Control,Observation,Verification | supported | 8 | 5.00 | - | For case 8, inspect the workspace README for ExampleProject 8; then apply a permission ... |
| 9 | pair-004 | pairwise_obligation | Observation,State | Observation,State,Verification | supported | 8 | 5.00 | - | For case 4, inspect the workspace README for ExampleProject 4; then create a durable ch... |
| 10 | single-034 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | For generated case 34, open the local src/main.py for ExampleProject omicron and summar... |
| 11 | single-027 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | For generated case 27, check the workspace artifact config.yaml for ExampleProject thet... |
| 12 | single-020 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | For generated case 20, inspect the workspace file tasks/todo.md for ExampleProject alph... |
| 13 | triple-023 | triple_obligation | Action,Control,Execution,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 13 | 3.00 | - | For generated case 23, retrieve the most recent public pricing or plan information for ... |
| 14 | pair-001 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 8 | 3.00 | - | For case 1, find the latest public announcement for ExampleProduct 1 with sources; then... |
| 15 | triple-046 | triple_obligation | Execution,Observation,State | Execution,Observation,State | supported | 8 | 2.00 | - | For generated case 46, look up the current public documentation page for ExampleProduct... |
| 16 | triple-033 | triple_obligation | Observation,State,Verification | Observation,State,Verification | supported | 8 | 2.00 | - | For generated case 33, retrieve the most recent public pricing or plan information for ... |
| 17 | triple-024 | triple_obligation | Action,Control,Execution,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 11 | 2.00 | - | For generated case 24, inspect the workspace file release_notes.md for ExampleProject e... |
| 18 | triple-021 | triple_obligation | Execution,Observation,State | Execution,Observation,State | supported | 8 | 2.00 | - | For generated case 21, look up the current public documentation page for ExampleProduct... |
| 19 | single-003 | single_obligation | Observation | Observation,Verification | supported | 5 | 2.00 | - | For case 3, find the latest public announcement for ExampleProduct 3 with sources. |
| 20 | single-001 | single_obligation | Observation | Observation,Verification | supported | 5 | 2.00 | - | For case 1, find the latest public announcement for ExampleProduct 1 with sources. |

### Wrong-harness

| Rank | Task | Category | Gold | Predicted | Status | Cost | Regret | Failures | Query |
|---:|---|---|---|---|---|---:|---:|---|---|
| - | none | - | - | - | - | - | - | - | - |

## llm_minimality

### Under-harness

| Rank | Task | Category | Gold | Predicted | Status | Cost | Regret | Failures | Query |
|---:|---|---|---|---|---|---:|---:|---|---|
| 1 | single-031 | single_obligation | Control | Control | unsupported | 0 | -1.00 | expected_supported | For generated case 31, block any real-world action unless the user explicitly grants pe... |
| 2 | single-028 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | For generated case 28, calculate the mean of 65, 43, 34, and 108 to two decimals. |
| 3 | single-021 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | For generated case 21, compute the exact total of [58, 35, 90, 10]. |
| 4 | single-030 | single_obligation | Action,Control,State | Action,Control,State | unsupported | 0 | -5.00 | expected_supported | For generated case 30, update sandbox_config_0030.json with a mock flag enabled=true af... |

### Over-harness

| Rank | Task | Category | Gold | Predicted | Status | Cost | Regret | Failures | Query |
|---:|---|---|---|---|---|---:|---:|---|---|
| 1 | single-008 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | For case 8, create a durable checklist checkpoint for three subtasks. |
| 2 | single-007 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | For case 7, create a durable checklist checkpoint for three subtasks. |
| 3 | single-034 | single_obligation | Observation | Observation | supported | 6 | 4.00 | - | For generated case 34, open the local src/main.py for ExampleProject omicron and summar... |
| 4 | pair-001 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 8 | 3.00 | - | For case 1, find the latest public announcement for ExampleProduct 1 with sources; then... |
| 5 | triple-033 | triple_obligation | Observation,State,Verification | Observation,State,Verification | supported | 8 | 2.00 | - | For generated case 33, retrieve the most recent public pricing or plan information for ... |
| 6 | triple-021 | triple_obligation | Execution,Observation,State | Execution,Observation,State | supported | 8 | 2.00 | - | For generated case 21, look up the current public documentation page for ExampleProduct... |
| 7 | single-003 | single_obligation | Observation | Observation,Verification | supported | 5 | 2.00 | - | For case 3, find the latest public announcement for ExampleProduct 3 with sources. |
| 8 | single-001 | single_obligation | Observation | Observation,Verification | supported | 5 | 2.00 | - | For case 1, find the latest public announcement for ExampleProduct 1 with sources. |
| 9 | pair-051 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 7 | 2.00 | - | For generated case 51, look up the current public documentation page for ExampleProduct... |
| 10 | pair-037 | pairwise_obligation | Control,Observation | Control,Observation,Verification | supported | 6 | 2.00 | - | For generated case 37, check whether ExampleProduct Nimbus has a recent release note an... |
| 11 | pair-007 | pairwise_obligation | Control,Observation | Control,Observation,Verification | supported | 6 | 2.00 | - | For case 7, find the latest public announcement for ExampleProduct 7 with sources; then... |
| 12 | pair-005 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State,Verification | supported | 10 | 2.00 | - | For case 5, find the latest public announcement for ExampleProduct 5 with sources; then... |
| 13 | pair-003 | pairwise_obligation | Observation,State | Observation,State,Verification | supported | 6 | 2.00 | - | For case 3, find the latest public announcement for ExampleProduct 3 with sources; then... |
| 14 | triple-027 | triple_obligation | Execution,Observation,Verification | Execution,Observation,Verification | supported | 8 | 1.00 | - | For generated case 27, check whether ExampleProduct Delta has a recent release note and... |
| 15 | triple-002 | triple_obligation | Action,Control,Execution,Observation,State | Action,Control,Execution,Observation,State | supported | 10 | 1.00 | - | For case 2, inspect the workspace README for ExampleProject 2; then calculate exactly 3... |
| 16 | single-033 | single_obligation | Observation | Observation,Verification | supported | 4 | 1.00 | - | For generated case 33, retrieve the most recent public pricing or plan information for ... |
| 17 | single-026 | single_obligation | Observation | Observation,Verification | supported | 4 | 1.00 | - | For generated case 26, look up the current public documentation page for ExampleProduct... |
| 18 | single-019 | single_obligation | Observation | Observation,Verification | supported | 4 | 1.00 | - | For generated case 19, find a current public FAQ entry for ExampleProduct Terra and rep... |
| 19 | pair-020 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 6 | 1.00 | - | For case 20, create file sandbox_note_20.txt in the sandbox workspace; then apply a per... |
| 20 | pair-019 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 6 | 1.00 | - | For case 19, create file sandbox_note_19.txt in the sandbox workspace; then apply a per... |

### Wrong-harness

| Rank | Task | Category | Gold | Predicted | Status | Cost | Regret | Failures | Query |
|---:|---|---|---|---|---|---:|---:|---|---|
| - | none | - | - | - | - | - | - | - | - |
