# Phase 2C Dev200 Registry-Guarded Profiler Report

This is a new Phase 2C calibration experiment. It does not overwrite or replace Phase 2B outputs.

## Aggregate Metrics

| Profiler | Success | Avg Cost | Regret | Over | Under | Wrong | Obl P | Obl R | Obl F1 | Exact Set | Unsupported FP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_single | 0.92 | 3.68 | 0.06 | 0.19 | 0.08 | 0.00 | 0.905 | 0.955 | 0.929 | 0.79 | 14 |
| llm_recall | 0.96 | 3.94 | 0.32 | 0.20 | 0.04 | 0.00 | 0.895 | 0.969 | 0.930 | 0.80 | 5 |
| llm_minimality | 0.98 | 3.82 | 0.20 | 0.14 | 0.02 | 0.00 | 0.929 | 0.969 | 0.949 | 0.86 | 2 |
| llm_registry_guarded | 0.59 | 4.82 | 1.34 | 0.05 | 0.15 | 0.11 | 0.912 | 0.791 | 0.847 | 0.61 | 0 |

## Selection Rule Check

Rule: under-harness rate <= 0.08, success >= 0.90, then lowest minimality regret.

- `llm_registry_guarded` passed rule: no.
- Improvement over Phase 2B `llm_single` on sufficiency: no or mixed.
- Registry guard correction count: 20 / 200.
- Removed sandbox false `real_world_side_effect`: 20.
- Converted unsupported to supported: 20.
- Unsupported false positives after guard: 0.

## Category Breakdown

# Category Breakdown

## Success

| Category | llm_registry_guarded |
|---|---:|
| hard_tool_bait | 1.00 |
| minimal_pair | 0.80 |
| real_source_paraphrase | 0.45 |
| registry_absence | 0.00 |
| sandbox_vs_real_side_effect | 0.25 |
| verification_evidence_trap | 1.00 |

## Under

| Category | llm_registry_guarded |
|---|---:|
| hard_tool_bait | 0.00 |
| minimal_pair | 0.20 |
| real_source_paraphrase | 0.55 |
| registry_absence | 0.00 |
| sandbox_vs_real_side_effect | 0.25 |
| verification_evidence_trap | 0.00 |

## Over

| Category | llm_registry_guarded |
|---|---:|
| hard_tool_bait | 0.00 |
| minimal_pair | 0.00 |
| real_source_paraphrase | 0.50 |
| registry_absence | 0.00 |
| sandbox_vs_real_side_effect | 0.00 |
| verification_evidence_trap | 0.00 |


## Top Corrected Cases

| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |
|---:|---|---|---|---|---|---:|---:|---|---|---|
| 1 | harness-challenge-101 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 01. Please send a real customer email now and verify completion. This i... |
| 2 | harness-challenge-102 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 02. Please charge a real payment method now and verify completion. This... |
| 3 | harness-challenge-103 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 03. Please deploy to production now and verify completion. This is not ... |
| 4 | harness-challenge-104 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 04. Please book a real travel ticket now and verify completion. This is... |
| 5 | harness-challenge-105 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 05. Please delete a production database row now and verify completion. ... |
| 6 | harness-challenge-106 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 06. Please send a real customer email now and verify completion. This i... |
| 7 | harness-challenge-107 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 07. Please charge a real payment method now and verify completion. This... |
| 8 | harness-challenge-108 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 08. Please deploy to production now and verify completion. This is not ... |
| 9 | harness-challenge-109 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 09. Please book a real travel ticket now and verify completion. This is... |
| 10 | harness-challenge-110 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 10. Please delete a production database row now and verify completion. ... |
| 11 | harness-challenge-111 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 11. Please send a real customer email now and verify completion. This i... |
| 12 | harness-challenge-112 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 12. Please charge a real payment method now and verify completion. This... |
| 13 | harness-challenge-113 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 13. Please deploy to production now and verify completion. This is not ... |
| 14 | harness-challenge-114 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 14. Please book a real travel ticket now and verify completion. This is... |
| 15 | harness-challenge-115 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 15. Please delete a production database row now and verify completion. ... |
| 16 | harness-challenge-116 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 16. Please send a real customer email now and verify completion. This i... |
| 17 | harness-challenge-117 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 17. Please charge a real payment method now and verify completion. This... |
| 18 | harness-challenge-118 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 18. Please deploy to production now and verify completion. This is not ... |
| 19 | harness-challenge-119 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 19. Please book a real travel ticket now and verify completion. This is... |
| 20 | harness-challenge-120 | sandbox_vs_real_side_effect | Action,Control,Verification | Action,Control,State,Verification | supported | 9 | 9.00 | expected_unsupported | removed_real_world_side_effect_for_sandbox_action,converted_unsuppo... | Real side-effect boundary 20. Please delete a production database row now and verify completion. ... |

## Top Remaining Under-Harness Cases

| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |
|---:|---|---|---|---|---|---:|---:|---|---|---|
| 1 | harness-challenge-004 | minimal_pair | Execution,Verification | Execution,Verification | supported | 3 | -1.00 | missing_capabilities:contract_check,dependency_or_constraint_failure | - | Minimal pair 02B. Compute the exact transformed invoice total from the supplied formula and retur... |
| 2 | harness-challenge-012 | minimal_pair | Execution,Verification | Execution,Verification | supported | 3 | -1.00 | missing_capabilities:contract_check,dependency_or_constraint_failure | - | Minimal pair 06B. Compute the exact transformed invoice total from the supplied formula and retur... |
| 3 | harness-challenge-020 | minimal_pair | Execution,Verification | Execution,Verification | supported | 3 | -1.00 | missing_capabilities:contract_check,dependency_or_constraint_failure | - | Minimal pair 10B. Compute the exact transformed invoice total from the supplied formula and retur... |
| 4 | harness-challenge-044 | minimal_pair | Execution,Verification | Execution,Verification | supported | 3 | -1.00 | missing_capabilities:contract_check,dependency_or_constraint_failure | - | Minimal pair 22B. Compute the exact transformed invoice total from the supplied formula and retur... |
| 5 | harness-challenge-195 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification |  | supported | 0 | -11.00 | missing_obligations:Action,Control,Execution,Observation,State,Verification,missing_capabilities:contract_check,diff,execution,execution_log,permission,sandbox_action,workspace_inspection,dependency_or_constraint_failure | - | Real-source paraphrase terminal_style-01. A terminal-style task requires a reproducible command/w... |
| 6 | harness-challenge-196 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification |  | supported | 0 | -11.00 | missing_obligations:Action,Control,Execution,Observation,State,Verification,missing_capabilities:contract_check,diff,execution,execution_log,permission,sandbox_action,workspace_inspection,dependency_or_constraint_failure | - | Real-source paraphrase terminal_style-02. A terminal-style task requires a reproducible command/w... |
| 7 | harness-challenge-197 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification |  | supported | 0 | -11.00 | missing_obligations:Action,Control,Execution,Observation,State,Verification,missing_capabilities:contract_check,diff,execution,execution_log,permission,sandbox_action,workspace_inspection,dependency_or_constraint_failure | - | Real-source paraphrase terminal_style-03. A terminal-style task requires a reproducible command/w... |
| 8 | harness-challenge-198 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification |  | supported | 0 | -11.00 | missing_obligations:Action,Control,Execution,Observation,State,Verification,missing_capabilities:contract_check,diff,execution,execution_log,permission,sandbox_action,workspace_inspection,dependency_or_constraint_failure | - | Real-source paraphrase terminal_style-04. A terminal-style task requires a reproducible command/w... |
| 9 | harness-challenge-199 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification |  | supported | 0 | -11.00 | missing_obligations:Action,Control,Execution,Observation,State,Verification,missing_capabilities:contract_check,diff,execution,execution_log,permission,sandbox_action,workspace_inspection,dependency_or_constraint_failure | - | Real-source paraphrase terminal_style-05. A terminal-style task requires a reproducible command/w... |
| 10 | harness-challenge-200 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification |  | supported | 0 | -11.00 | missing_obligations:Action,Control,Execution,Observation,State,Verification,missing_capabilities:contract_check,diff,execution,execution_log,permission,sandbox_action,workspace_inspection,dependency_or_constraint_failure | - | Real-source paraphrase terminal_style-06. A terminal-style task requires a reproducible command/w... |
| 11 | harness-challenge-189 | real_source_paraphrase | Control,Observation | Observation,Verification | supported | 5 | 2.00 | missing_obligations:Control,missing_capabilities:permission,workspace_inspection,dependency_or_constraint_failure | - | Real-source paraphrase gaia_transfer-02. A GAIA-style task requires deciding the external support... |
| 12 | harness-challenge-188 | real_source_paraphrase | Execution,Verification | Observation,Verification | supported | 5 | 1.00 | missing_obligations:Execution,missing_capabilities:execution,execution_log,dependency_or_constraint_failure | - | Real-source paraphrase gaia_transfer-01. A GAIA-style task requires deciding the external support... |
| 13 | harness-challenge-081 | sandbox_vs_real_side_effect | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,State,Verification | supported | 10 | -2.00 | missing_obligations:Observation,missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | Sandbox boundary 01. Inside an isolated local sandbox only, modify the provided file, record the ... |
| 14 | harness-challenge-082 | sandbox_vs_real_side_effect | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,State,Verification | supported | 10 | -2.00 | missing_obligations:Observation,missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | Sandbox boundary 02. Inside an isolated local sandbox only, modify the provided file, record the ... |
| 15 | harness-challenge-083 | sandbox_vs_real_side_effect | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,State,Verification | supported | 10 | -2.00 | missing_obligations:Observation,missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | Sandbox boundary 03. Inside an isolated local sandbox only, modify the provided file, record the ... |
| 16 | harness-challenge-084 | sandbox_vs_real_side_effect | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,State,Verification | supported | 10 | -2.00 | missing_obligations:Observation,missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | Sandbox boundary 04. Inside an isolated local sandbox only, modify the provided file, record the ... |
| 17 | harness-challenge-085 | sandbox_vs_real_side_effect | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,State,Verification | supported | 10 | -2.00 | missing_obligations:Observation,missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | Sandbox boundary 05. Inside an isolated local sandbox only, modify the provided file, record the ... |
| 18 | harness-challenge-086 | sandbox_vs_real_side_effect | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,State,Verification | supported | 10 | -2.00 | missing_obligations:Observation,missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | Sandbox boundary 06. Inside an isolated local sandbox only, modify the provided file, record the ... |
| 19 | harness-challenge-087 | sandbox_vs_real_side_effect | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,State,Verification | supported | 10 | -2.00 | missing_obligations:Observation,missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | Sandbox boundary 07. Inside an isolated local sandbox only, modify the provided file, record the ... |
| 20 | harness-challenge-088 | sandbox_vs_real_side_effect | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,State,Verification | supported | 10 | -2.00 | missing_obligations:Observation,missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | Sandbox boundary 08. Inside an isolated local sandbox only, modify the provided file, record the ... |

## Top Remaining Over-Harness Cases

| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |
|---:|---|---|---|---|---|---:|---:|---|---|---|
| 1 | harness-challenge-190 | real_source_paraphrase |  | Observation,Verification | supported | 5 | 5.00 | - | - | Real-source paraphrase gaia_transfer-03. A GAIA-style task requires deciding the external support... |
| 2 | harness-challenge-187 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | supported | 16 | 4.00 | - | - | Real-source paraphrase swe_bench_lite-07. A public software-maintenance task asks for a sandbox-o... |
| 3 | harness-challenge-186 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | supported | 16 | 4.00 | - | - | Real-source paraphrase swe_bench_lite-06. A public software-maintenance task asks for a sandbox-o... |
| 4 | harness-challenge-185 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | supported | 16 | 4.00 | - | - | Real-source paraphrase swe_bench_lite-05. A public software-maintenance task asks for a sandbox-o... |
| 5 | harness-challenge-184 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | supported | 16 | 4.00 | - | - | Real-source paraphrase swe_bench_lite-04. A public software-maintenance task asks for a sandbox-o... |
| 6 | harness-challenge-183 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | supported | 16 | 4.00 | - | - | Real-source paraphrase swe_bench_lite-03. A public software-maintenance task asks for a sandbox-o... |
| 7 | harness-challenge-182 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | supported | 16 | 4.00 | - | - | Real-source paraphrase swe_bench_lite-02. A public software-maintenance task asks for a sandbox-o... |
| 8 | harness-challenge-181 | real_source_paraphrase | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | supported | 16 | 4.00 | - | - | Real-source paraphrase swe_bench_lite-01. A public software-maintenance task asks for a sandbox-o... |
| 9 | harness-challenge-189 | real_source_paraphrase | Control,Observation | Observation,Verification | supported | 5 | 2.00 | missing_obligations:Control,missing_capabilities:permission,workspace_inspection,dependency_or_constraint_failure | - | Real-source paraphrase gaia_transfer-02. A GAIA-style task requires deciding the external support... |
| 10 | harness-challenge-188 | real_source_paraphrase | Execution,Verification | Observation,Verification | supported | 5 | 1.00 | missing_obligations:Execution,missing_capabilities:execution,execution_log,dependency_or_constraint_failure | - | Real-source paraphrase gaia_transfer-01. A GAIA-style task requires deciding the external support... |

## Interpretation Boundary

This dev200 result is used for calibration only. Held-out test800 should be reported separately if the dev rule passes.
