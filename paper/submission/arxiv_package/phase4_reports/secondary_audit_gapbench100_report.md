# Secondary Adversarial Label Audit

This is a secondary LLM audit over a stratified GapBench-100 sample. It is not inter-annotator agreement and should not be described as an independent human audit.

| Metric | Value |
|---|---:|
| N | 100 |
| Obligation exact-set agreement | 0.65 |
| Obligation micro-F1 | 0.878 |
| Capability micro-F1 | 0.814 |
| Expected-status agreement | 0.87 |
| Oracle harness exact agreement | 0.75 |

## Disagreement Samples

| Task | Category | Gold obligations | Audit obligations | Gold caps | Audit caps |
|---|---|---|---|---|---|
| ambiguous-001 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-003 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-004 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-005 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-008 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-009 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-011 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-013 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-016 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-018 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-019 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-023 | ambiguous | Action,Control,Verification | Control | contract_check,diff,permission | - |
| ambiguous-030 | ambiguous | Action,Control,Verification | Action,Control | contract_check,diff,permission | permission,real_world_side_effect |
| complex-0005 | complex_obligation | Action,Control,Observation,State,Verification | Action,Control,Observation,State,Verification | contract_check,diff,durable_state,evidence_sources,permission,source_spans | diff,durable_state,evidence_sources,permission,sandbox_action,source_spans |
| complex-0009 | complex_obligation | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | contract_check,diff,durable_state,evidence_sources,execution,permission,source_spans | diff,durable_state,evidence_sources,execution,permission,sandbox_action,source_spans |
| complex-0020 | complex_obligation | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,State,Verification | contract_check,diff,durable_state,execution,execution_log,permission,workspace_inspection | contract_check,diff,durable_state,execution,execution_log,permission,sandbox_action,workspace_inspection |
| complex-0025 | complex_obligation | Action,Control,Observation,State,Verification | Action,Control,Observation,State,Verification | contract_check,diff,durable_state,evidence_sources,permission,source_spans | diff,durable_state,evidence_sources,permission,sandbox_action,source_spans |
| complex-0034 | complex_obligation | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,Verification | contract_check,diff,execution,execution_log,permission,workspace_inspection | contract_check,diff,execution,execution_log,permission,sandbox_action,workspace_inspection |
| complex-0056 | complex_obligation | Action,Control,Observation,State,Verification | Action,Control,Observation,State,Verification | contract_check,diff,durable_state,permission,workspace_inspection | contract_check,diff,durable_state,permission,sandbox_action,workspace_inspection |
| complex-0063 | complex_obligation | Action,Control,Execution,Observation,State,Verification | Action,Control,Execution,Observation,Verification | contract_check,diff,evidence_sources,execution,permission,source_spans | diff,evidence_sources,execution,permission,sandbox_action,source_spans |
