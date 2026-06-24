# Phase 2C Dev200 Registry-Guarded Profiler Report

This is a new Phase 2C calibration experiment. It does not overwrite or replace Phase 2B outputs.

## Aggregate Metrics

| Profiler | Success | Avg Cost | Regret | Over | Under | Wrong | Obl P | Obl R | Obl F1 | Exact Set | Unsupported FP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_single | 0.92 | 3.68 | 0.06 | 0.19 | 0.08 | 0.00 | 0.905 | 0.955 | 0.929 | 0.79 | 14 |
| llm_recall | 0.96 | 3.94 | 0.32 | 0.20 | 0.04 | 0.00 | 0.895 | 0.969 | 0.930 | 0.80 | 5 |
| llm_minimality | 0.98 | 3.82 | 0.20 | 0.14 | 0.02 | 0.00 | 0.929 | 0.969 | 0.949 | 0.86 | 2 |
| llm_registry_guarded | 0.97 | 4.01 | 0.40 | 0.20 | 0.03 | 0.00 | 0.905 | 0.955 | 0.929 | 0.79 | 4 |

## Selection Rule Check

Rule: under-harness rate <= 0.08, success >= 0.90, then lowest minimality regret.

- `llm_registry_guarded` passed rule: yes.
- Improvement over Phase 2B `llm_single` on sufficiency: yes.
- Registry guard correction count: 16 / 200.
- Removed sandbox false `real_world_side_effect`: 10.
- Converted unsupported to supported: 10.
- Unsupported false positives after guard: 4.

## Category Breakdown

# Category Breakdown

## Success

| Category | llm_registry_guarded |
|---|---:|
| ambiguous | 1.00 |
| complex_obligation | 1.00 |
| pairwise_obligation | 0.92 |
| pure_language_negative | 1.00 |
| single_obligation | 0.94 |
| tool_bait | 1.00 |
| triple_obligation | 1.00 |
| unsupported | 1.00 |

## Under

| Category | llm_registry_guarded |
|---|---:|
| ambiguous | 0.00 |
| complex_obligation | 0.00 |
| pairwise_obligation | 0.08 |
| pure_language_negative | 0.00 |
| single_obligation | 0.06 |
| tool_bait | 0.00 |
| triple_obligation | 0.00 |
| unsupported | 0.00 |

## Over

| Category | llm_registry_guarded |
|---|---:|
| ambiguous | 0.00 |
| complex_obligation | 0.43 |
| pairwise_obligation | 0.21 |
| pure_language_negative | 0.00 |
| single_obligation | 0.28 |
| tool_bait | 0.00 |
| triple_obligation | 0.28 |
| unsupported | 0.00 |


## Top Corrected Cases

| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |
|---:|---|---|---|---|---|---:|---:|---|---|---|
| 1 | ambiguous-001 | ambiguous | Action,Control,Verification | Control,Observation | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 1: update whichever file is best and make the appropriate change. |
| 2 | ambiguous-002 | ambiguous | Action,Control,Verification | Control,Observation | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 2: update whichever file is best and make the appropriate change. |
| 3 | ambiguous-003 | ambiguous | Action,Control,Verification | Control,Observation | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 3: update whichever file is best and make the appropriate change. |
| 4 | ambiguous-004 | ambiguous | Action,Control,Verification | Control,Observation | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 4: update whichever file is best and make the appropriate change. |
| 5 | ambiguous-005 | ambiguous | Action,Control,Verification | Control,Observation | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 5: update whichever file is best and make the appropriate change. |
| 6 | ambiguous-006 | ambiguous | Action,Control,Verification | Control,Observation | clarify | 0 | 0.00 | - | preserved_clarification_for_ambiguous_action_target | Unclear target 6: update whichever file is best and make the appropriate change. |
| 7 | pair-005 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State,Verification | supported | 10 | 2.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For case 5, find the latest public announcement for ExampleProduct 5 with sources; then create fi... |
| 8 | pair-006 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State | supported | 7 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For case 6, inspect the workspace README for ExampleProject 6; then create file sandbox_note_6.tx... |
| 9 | pair-013 | pairwise_obligation | Action,Control,Execution,State | Action,Control,Execution,State | supported | 7 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For case 13, calculate exactly 50 * 24; then create file sandbox_note_13.txt in the sandbox works... |
| 10 | pair-014 | pairwise_obligation | Action,Control,Execution,State | Action,Control,Execution,State | supported | 7 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For case 14, calculate exactly 51 * 25; then create file sandbox_note_14.txt in the sandbox works... |
| 11 | pair-019 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 5 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For case 19, create file sandbox_note_19.txt in the sandbox workspace; then apply a permission ga... |
| 12 | pair-020 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 5 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For case 20, create file sandbox_note_20.txt in the sandbox workspace; then apply a permission ga... |
| 13 | pair-035 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State | supported | 9 | 1.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 35, find the latest public announcement for ExampleProduct Lantern and list th... |
| 14 | pair-036 | pairwise_obligation | Action,Control,Observation,State | Action,Control,Observation,State | supported | 7 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 36, inspect the workspace file release_notes.md for ExampleProject rho and rep... |
| 15 | pair-050 | pairwise_obligation | Action,Control,State | Action,Control,State | supported | 5 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 50, update sandbox_config_0050.json with a mock flag enabled=true after permis... |
| 16 | single-030 | single_obligation | Action,Control,State | Action,Control,State | supported | 5 | 0.00 | - | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | For generated case 30, update sandbox_config_0030.json with a mock flag enabled=true after permis... |

## Top Remaining Under-Harness Cases

| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |
|---:|---|---|---|---|---|---:|---:|---|---|---|
| 1 | pair-015 | pairwise_obligation | Control,Execution | Control,Execution | unsupported | 0 | -3.00 | expected_supported | - | For case 15, calculate exactly 52 * 26; then apply a permission gate before any risky step. |
| 2 | pair-016 | pairwise_obligation | Control,Execution | Control,Execution | unsupported | 0 | -3.00 | expected_supported | - | For case 16, calculate exactly 53 * 27; then apply a permission gate before any risky step. |
| 3 | pair-038 | pairwise_obligation | Control,Observation | Control,Observation | unsupported | 0 | -3.00 | expected_supported | - | For generated case 38, open the local CHANGELOG.md for ExampleProject tau and summarize its main ... |
| 4 | pair-046 | pairwise_obligation | Control,State | Control,State | unsupported | 0 | -2.00 | expected_supported | - | For generated case 46, record an intermediate artifact for review batch 0046 so the next step can... |
| 5 | single-021 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | - | For generated case 21, compute the exact total of [58, 35, 90, 10]. |
| 6 | single-028 | single_obligation | Execution |  | supported | 0 | -2.00 | missing_obligations:Execution,missing_capabilities:execution,dependency_or_constraint_failure | - | For generated case 28, calculate the mean of 65, 43, 34, and 108 to two decimals. |

## Top Remaining Over-Harness Cases

| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |
|---:|---|---|---|---|---|---:|---:|---|---|---|
| 1 | triple-029 | triple_obligation | Action,Control,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 16 | 7.00 | - | - | For generated case 29, find a current public FAQ entry for ExampleProduct Flux and report the sou... |
| 2 | triple-022 | triple_obligation | Execution,Observation,State | Execution,Observation,State,Verification | supported | 10 | 5.00 | - | - | For generated case 22, open the local src/main.py for ExampleProject gamma and summarize its main... |
| 3 | single-022 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | - | For generated case 22, record an intermediate artifact for review batch 0022 so the next step can... |
| 4 | single-008 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | - | For case 8, create a durable checklist checkpoint for three subtasks. |
| 5 | single-007 | single_obligation | State | Action,Control,State | supported | 6 | 5.00 | - | - | For case 7, create a durable checklist checkpoint for three subtasks. |
| 6 | pair-052 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 9 | 5.00 | - | - | For generated case 52, inspect the workspace file package.json for ExampleProject nu and report w... |
| 7 | single-027 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | - | For generated case 27, check the workspace artifact config.yaml for ExampleProject theta before a... |
| 8 | single-020 | single_obligation | Observation | Observation,Verification | supported | 6 | 4.00 | - | - | For generated case 20, inspect the workspace file tasks/todo.md for ExampleProject alpha and repo... |
| 9 | pair-044 | pairwise_obligation | Execution,Verification | Execution,Observation,Verification | supported | 8 | 4.00 | - | - | For generated case 44, parse the inline numbers 81, 32, 13, 592 and return their exact sum; then ... |
| 10 | triple-025 | triple_obligation | Control,Execution,Observation | Control,Execution,Observation,Verification | supported | 9 | 3.00 | - | - | For generated case 25, find the latest public announcement for ExampleProduct Beacon and list the... |
| 11 | triple-023 | triple_obligation | Action,Control,Execution,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 13 | 3.00 | - | - | For generated case 23, retrieve the most recent public pricing or plan information for ExamplePro... |
| 12 | pair-001 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 8 | 3.00 | - | - | For case 1, find the latest public announcement for ExampleProduct 1 with sources; then calculate... |
| 13 | triple-033 | triple_obligation | Observation,State,Verification | Observation,State,Verification | supported | 8 | 2.00 | - | - | For generated case 33, retrieve the most recent public pricing or plan information for ExamplePro... |
| 14 | triple-031 | triple_obligation | Control,Observation,State | Control,Observation,State,Verification | supported | 7 | 2.00 | - | - | For generated case 31, look up the current public documentation page for ExampleProduct Harbor an... |
| 15 | triple-026 | triple_obligation | Control,Execution,Observation | Control,Execution,Observation,Verification | supported | 7 | 2.00 | - | - | For generated case 26, open the local CHANGELOG.md for ExampleProject eta and summarize its main ... |
| 16 | triple-024 | triple_obligation | Action,Control,Execution,Observation,State | Action,Control,Execution,Observation,State,Verification | supported | 11 | 2.00 | - | - | For generated case 24, inspect the workspace file release_notes.md for ExampleProject epsilon and... |
| 17 | triple-021 | triple_obligation | Execution,Observation,State | Execution,Observation,State,Verification | supported | 8 | 2.00 | - | - | For generated case 21, look up the current public documentation page for ExampleProduct Vector an... |
| 18 | single-003 | single_obligation | Observation | Observation,Verification | supported | 5 | 2.00 | - | - | For case 3, find the latest public announcement for ExampleProduct 3 with sources. |
| 19 | single-001 | single_obligation | Observation | Observation,Verification | supported | 5 | 2.00 | - | - | For case 1, find the latest public announcement for ExampleProduct 1 with sources. |
| 20 | pair-051 | pairwise_obligation | Execution,Observation | Execution,Observation,Verification | supported | 7 | 2.00 | - | - | For generated case 51, look up the current public documentation page for ExampleProduct Delta and... |

## Interpretation Boundary

This dev200 result is used for calibration only. Held-out test800 should be reported separately if the dev rule passes.
