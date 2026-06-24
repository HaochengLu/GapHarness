# Phase 2C Held-out Test800 Registry-Guarded Report

This test800 run is a Phase 2C registry-guarded calibration experiment. It is reported separately from the Phase 2B held-out selected-profiler result and does not overwrite the Phase 2B table.

Key question: Does registry guarding reduce unsupported false positives and improve success without causing under-harness to rise?

## Aggregate Metrics

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy | Unsupported FP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 800 | 0.20 | 0.00 | 3.69 | -3.69 | 0.00 | 0.74 | 0.00 | 0.00 | 0 |
| tool_router | 800 | 0.32 | 1.96 | 3.69 | -1.72 | 0.09 | 0.62 | 0.43 | 0.06 | 0 |
| difficulty_router | 800 | 0.41 | 3.22 | 3.69 | -0.47 | 0.26 | 0.53 | 0.15 | 0.13 | 0 |
| always_full | 800 | 0.94 | 16.00 | 3.69 | 12.31 | 0.94 | 0.00 | 0.00 | 0.51 | 0 |
| gold_oracle_gap_harness | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| oracle_minimal | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| phase2b_selected_llm_single | 800 | 0.89 | 3.59 | 3.69 | -0.09 | 0.14 | 0.09 | 0.01 | 0.05 | 56 |
| llm_registry_guarded | 800 | 0.94 | 3.98 | 3.69 | 0.30 | 0.15 | 0.03 | 0.01 | 0.05 | 12 |

## Guard Corrections

- Guard applied: 50 / 800.
- Removed sandbox false `real_world_side_effect`: 44.
- Converted unsupported to supported: 44.
- Unsupported false positives after guard: 12.

## Top Corrected Cases

| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |
|---:|---|---|---|---|---|---:|---:|---|---|---|
| 1 | ambiguous-007 | ambiguous | Action,Control,Verification | Observation,Verification | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 7: update whichever file is best and make the appropriate change. |
| 2 | ambiguous-008 | ambiguous | Action,Control,Verification | Observation | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 8: update whichever file is best and make the appropriate change. |
| 3 | ambiguous-013 | ambiguous | Action,Control,Verification | Action,Control,Observation,State,Verification | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 13: update whichever file is best and make the appropriate change. |
| 4 | ambiguous-018 | ambiguous | Action,Control,Verification | Action,Control,Observation,State,Verification | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 18: update whichever file is best and make the appropriate change. |
| 5 | ambiguous-023 | ambiguous | Action,Control,Verification | Action,Control,Observation,State,Verification | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 23: update whichever file is best and make the appropriate change. |
| 6 | ambiguous-028 | ambiguous | Action,Control,Verification | Action,Control,Observation,State,Verification | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 28: update whichever file is best and make the appropriate change. |
| 7 | complex-0039 | complex_obligation | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | supported | 14 | 1.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 7039, find a current public FAQ entry for ExampleProduct Harbor and report the... |
| 8 | complex-0040 | complex_obligation | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | supported | 12 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 7040, inspect the workspace file tasks/todo.md for ExampleProject alpha and re... |
| 9 | pair-055 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State | supported | 8 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 55, find the latest public announcement for ExampleProduct Harbor and list the... |
| 10 | pair-056 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State | supported | 7 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 56, inspect the workspace file tasks/todo.md for ExampleProject rho and report... |
| 11 | pair-070 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 5 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 70, update sandbox_config_0070.json with a mock flag enabled=true after permis... |
| 12 | pair-082 | pairwise_obligation | Action,Control,Execution,State | Action,Control,Execution,State | supported | 7 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 82, evaluate exactly (46 + 11) * 4; then write a mock deployment note to sandb... |
| 13 | pair-090 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 5 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 90, update sandbox_config_0090.json with a mock flag enabled=true after permis... |
| 14 | pair-110 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 5 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 110, update sandbox_config_0110.json with a mock flag enabled=true after permi... |
| 15 | pair-122 | pairwise_obligation | Action,Control,Execution,State | Action,Control,Execution,State | supported | 7 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 122, evaluate exactly (86 + 45) * 8; then write a mock deployment note to sand... |
| 16 | pair-125 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 6 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 125, save the decision "use minimal harness" under durable state key gapbench_... |
| 17 | pair-130 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 5 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 130, update sandbox_config_0130.json with a mock flag enabled=true after permi... |
| 18 | pair-150 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 5 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 150, update sandbox_config_0150.json with a mock flag enabled=true after permi... |
| 19 | pair-162 | pairwise_obligation | Action,Control,Execution,State | Action,Control,Execution,State | supported | 7 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 162, evaluate exactly (53 + 38) * 3; then write a mock deployment note to sand... |
| 20 | pair-165 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 6 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 165, save the decision "use minimal harness" under durable state key gapbench_... |

## Remaining Under-Harness Cases

| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |
|---:|---|---|---|---|---|---:|---:|---|---|---|
| 1 | complex-0037 | complex_obligation | Control,Execution,Observation,Verification | Control,Execution,Observation,Verification | unsupported | 0 | -8.00 | expected_supported | - | For generated case 7037, check whether ExampleProduct Flux has a recent release note and cite the... |
| 2 | pair-118 | pairwise_obligation | Control,Observation | Control,Observation | unsupported | 0 | -3.00 | expected_supported | - | For generated case 118, open the local src/main.py for ExampleProject tau and summarize its main ... |
| 3 | pair-178 | pairwise_obligation | Control,Observation | Control,Observation | unsupported | 0 | -3.00 | expected_supported | - | For generated case 178, open the local src/main.py for ExampleProject tau and summarize its main ... |
| 4 | pair-186 | pairwise_obligation | Control,State | Control,State | unsupported | 0 | -2.00 | expected_supported | - | For generated case 186, record an intermediate artifact for review batch 0186 so the next step ca... |
| 5 | pair-238 | pairwise_obligation | Control,Observation | Control,Observation | unsupported | 0 | -3.00 | expected_supported | - | For generated case 238, open the local src/main.py for ExampleProject tau and summarize its main ... |
| 6 | pair-246 | pairwise_obligation | Control,State | Control,State | unsupported | 0 | -2.00 | expected_supported | - | For generated case 246, record an intermediate artifact for review batch 0246 so the next step ca... |
| 7 | single-059 | single_obligation | Control | Control | unsupported | 0 | -1.00 | expected_supported | - | For generated case 59, block any real-world action unless the user explicitly grants permission i... |
| 8 | single-087 | single_obligation | Control | Control | unsupported | 0 | -1.00 | expected_supported | - | For generated case 87, block any real-world action unless the user explicitly grants permission i... |
| 9 | triple-089 | triple_obligation | Control,Execution,State | Control,Execution,State | unsupported | 0 | -4.00 | expected_supported | - | For generated case 89, parse the inline numbers 53, 19, 72, 7 and return their exact sum; then re... |
| 10 | triple-175 | triple_obligation | Control,Execution,Observation | Control,Execution,Observation | unsupported | 0 | -6.00 | expected_supported | - | For generated case 175, find the latest public announcement for ExampleProduct Harbor and list th... |
| 11 | triple-181 | triple_obligation | Control,Observation,State | Control,Observation,State | unsupported | 0 | -5.00 | expected_supported | - | For generated case 181, look up the current public documentation page for ExampleProduct Nimbus a... |
| 12 | triple-189 | triple_obligation | Control,Execution,State | Control,Execution,State | unsupported | 0 | -4.00 | expected_supported | - | For generated case 189, parse the inline numbers 80, 22, 2, 760 and return their exact sum; then ... |
| 13 | triple-122 | triple_obligation | Execution,Observation,State | Execution,Observation,State | supported | 6 | 1.00 | missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | For generated case 122, open the local CHANGELOG.md for ExampleProject gamma and summarize its ma... |
| 14 | triple-222 | triple_obligation | Execution,Observation,State | Execution,Observation,State | supported | 7 | 2.00 | missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | For generated case 222, open the local docs/overview.md for ExampleProject gamma and summarize it... |
| 15 | pair-141 | pairwise_obligation | Execution,State | State | supported | 1 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | - | For generated case 141, compute the exact total of [105, 14, 15, 36]; then record an intermediate... |
| 16 | pair-143 | pairwise_obligation | Control,Execution | Control | supported | 1 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | - | For generated case 143, calculate the mean of 107, 28, 235, and 26 to two decimals; then apply a ... |
| 17 | single-056 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | - | For generated case 56, compute the exact total of [93, 34, 58, 44]. |
| 18 | single-063 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | - | For generated case 63, calculate the mean of 100, 42, 184, and 33 to two decimals. |
| 19 | single-084 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | - | For generated case 84, parse the inline numbers 48, 25, 73, 200 and return their exact sum. |
| 20 | single-091 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | - | For generated case 91, compute the exact total of [55, 33, 69, 5]. |

## Remaining Over-Harness Cases

| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |
|---:|---|---|---|---|---|---:|---:|---|---|---|
| 1 | single-169 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | - | For generated case 169, save the decision "use minimal harness" under durable state key gapbench_... |
| 2 | single-148 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | - | For generated case 148, create a durable checklist checkpoint named checkpoint_0148 with three su... |
| 3 | single-134 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | - | For generated case 134, record an intermediate artifact for review batch 0134 so the next step ca... |
| 4 | single-127 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | - | For generated case 127, maintain a task-state record with status pending_review for item 0127. |
| 5 | single-120 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | - | For generated case 120, create a durable checklist checkpoint named checkpoint_0120 with three su... |
| 6 | single-078 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | - | For generated case 78, record an intermediate artifact for review batch 0078 so the next step can... |
| 7 | triple-072 | triple_obligation | Execution,Observation,State | Execution,Observation,State | supported | 9 | 4.00 | - | - | For generated case 72, inspect the workspace file release_notes.md for ExampleProject nu and repo... |
| 8 | single-132 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | - | For generated case 132, inspect the workspace file release_notes.md for ExampleProject nu and rep... |
| 9 | single-125 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | - | For generated case 125, read requirements.txt in the sandbox workspace for ExampleProject zeta an... |
| 10 | single-111 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | - | For generated case 111, check the workspace artifact config.yaml for ExampleProject mu before ans... |
| 11 | single-083 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | - | For generated case 83, check the workspace artifact src/config.ts for ExampleProject delta before... |
| 12 | single-076 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | - | For generated case 76, inspect the workspace file package.json for ExampleProject rho and report ... |
| 13 | single-072 | single_obligation | Action,Control,State | Action,Control,State,Verification | supported | 9 | 4.00 | - | - | For generated case 72, create file sandbox_note_0072.txt in the sandbox workspace and require a p... |
| 14 | single-069 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | - | For generated case 69, read data/sample.csv in the sandbox workspace for ExampleProject kappa and... |
| 15 | single-065 | single_obligation | Action,Control,State | Action,Control,State,Verification | supported | 9 | 4.00 | - | - | For generated case 65, append one line to sandbox_log_0065.txt in the sandbox workspace after pas... |
| 16 | single-062 | single_obligation | Observation | Observation | supported | 6 | 4.00 | - | - | For generated case 62, open the local CHANGELOG.md for ExampleProject gamma and summarize its mai... |
| 17 | single-055 | single_obligation | Observation | Observation | supported | 6 | 4.00 | - | - | For generated case 55, check the workspace artifact docs/api.md for ExampleProject pi before answ... |
| 18 | triple-223 | triple_obligation | Action,Control,Execution,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 13 | 3.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 223, retrieve the most recent public pricing or plan information for ExamplePr... |
| 19 | triple-148 | triple_obligation | Action,Control,Execution,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 13 | 3.00 | - | - | For generated case 148, retrieve the most recent public pricing or plan information for ExamplePr... |
| 20 | triple-123 | triple_obligation | Action,Control,Execution,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 13 | 3.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 123, retrieve the most recent public pricing or plan information for ExamplePr... |

Interpretation boundary: this is held-out obligation/harness coverage, not full open-world answer-level accuracy.
