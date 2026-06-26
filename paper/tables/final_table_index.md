# Final Table Index

The main manuscript now includes seventeen main tables plus appendix tables. Captions below state what each table supports and what it does not support.

Current manuscript draft: `paper/drafts/gapharness_manuscript_v3.md` (certificate-as-contract reframe). The multi-model inter-annotator-agreement study that backs the reliability finding is reported in `outputs/iaa/iaa_report.md`.

## Table 1. GapBench-1000 Gold Compiler and Baselines

- File: `paper/tables/table1_gapbench1000_gold_revised.md`
- Supports: compiler validation under human-audited gold obligations; GapHarness matches the oracle minimal harness and separates baseline under-harnessing and over-harnessing failures.
- Does not support: open-world profiling or answer-level task solving.

## Table 2. Compiler Equivalence Replay

- File: `paper/tables/table10_compiler_equivalence_replay.md`
- Supports: the optimized compiler preserves frozen status, harness, and cost outputs while adding certificate metadata.
- Does not support: a claim that exact harness compilation is polynomial-time.

## Table 3. Synthetic Registry Scaling

- File: `paper/tables/table15_compiler_ablation_scaling.md`
- Supports: dominance pruning and branch-and-bound make exact certificate-carrying compilation practical on the redundant synthetic registries studied.
- Does not support: worst-case polynomial-time compilation or broad real-world registry scaling.

## Table 4. Mostly Non-Dominated Registry Scaling Stress

- File: `paper/tables/table16_non_dominated_scaling.md`
- Supports: a harder synthetic registry stress where dominance pruning has little help and exact search exposes exponential-boundary behavior.
- Does not support: a throughput claim for arbitrary large non-dominated registries.

## Table 5. LLM Profiler Held-Out Test800

- File: `paper/tables/table2_phase2b_llm_heldout_revised.md`
- Supports: LLM-inferred obligations outperform direct, heuristic router, and direct LLM Tool Router baselines on held-out GapBench test800.
- Does not support: fully solved LLM obligation profiling.

## Table 6. Diagnostic-Feedback Strategy Baselines

- File: `paper/tables/table13_agentic_strategy_comparison.md`
- Supports: workflow generation, verifier-repair, ReAct-style selection, and GapHarness-Repair give a feedback-assisted upper-bound comparison over the same registry/executor/verifier.
- Does not support: a claim that GapHarness is categorically better than LangGraph, AutoGen, or any framework substrate.

## Table 7. Feedback-Level Replay

- File: `paper/tables/table19_feedback_level_replay.md`
- Supports: repair performance depends on the amount of verifier feedback; weak, medium, and strong diagnostics have different coverage/cost tradeoffs.
- Does not support: a new independent LLM run; this is deterministic replay over existing routes/profiles.

## Table 8. Certificate Utility Proxy

- File: `paper/tables/table18_certificate_utility_proxy.md`
- Supports: certificate-bearing systems expose localized coverage/minimality evidence and reduce deterministic debug-work proxies.
- Does not support: completed human audit-time measurement; the human audit packet is prepared separately.

## Table 9. Cost-Scheme Sensitivity and Proxy Calibration

- File: `paper/tables/table20_cost_calibration_sensitivity.md`
- Supports: declared cost conclusions are checked under uniform, latency-proxy, token/API-proxy, and risk-weighted proxy schemes.
- Does not support: measured production latency, provider billing, or real security risk quantification.

## Table 10. Status Confusion

- File: `paper/tables/table21_status_confusion.md`
- Supports: status-level failure analysis for supported, unsupported, and clarify predictions, including where registry guard helps or hurts.
- Does not support: complete answer-level correctness analysis.

## Table 11. Profiler Error Taxonomy

- File: `paper/tables/table22_profiler_error_taxonomy.md`
- Supports: concrete error categories for LLM profiling failures on GapBench test800 and HarnessChallenge-200.
- Does not support: a final trained profiler or complete causal attribution.

## Table 12. Anti-Circularity Stress Tests

- File: `paper/tables/table4_phase2d_stress_tests_revised.md`
- Supports: registry affordances matter, gold labels are semantically consequential, and GapHarness avoids tool-bait over-harnessing.
- Does not support: a realistic label-corruption model or complete adversarial robustness.

## Table 13. HarnessChallenge-200 Targeted Diagnostic

- File: `paper/tables/table9_harness_challenge200.md`
- Supports: targeted diagnostics expose LLM profiler, registry-boundary, and direct-routing failure modes.
- Does not support: natural-frequency estimates of real user traffic.

## Table 14. SWE-HarnessExec-20 Executable Trace Validation

- File: `paper/tables/table14_swe_harness_exec20_agentic.md`
- Supports: sandboxed patch/test traces run when required execution affordances are declared; diagnostic-feedback policies and GapHarness-Repair also succeed on homogeneous fixtures.
- Does not support: SWE-bench pass@1, model patch generation, or superiority on every execution-heavy task.

## Table 15. SWE-HarnessExec-50 Scale-Up

- File: `paper/tables/table17_swe_harness_exec50_scaleup.md`
- Supports: a larger deterministic provided-patch executable trace check over 50 sandbox fixtures, with real pre-patch failing pytest and post-patch passing pytest.
- Does not support: real repository checkout, model-generated repair, SWE-bench tests, or SWE-bench pass@1.

## Table 16. Secondary Adversarial Audit

- File: `paper/tables/table7_secondary_audit.md`
- Supports: an additional blinded LLM consistency check over a stratified GapBench-100 sample.
- Does not support: human inter-annotator agreement.

## Table 17. External-Validity and Boundary Diagnostics

- File: `paper/tables/table5_boundary_diagnostics_revised.md`
- Supports: transfer artifacts can be processed as obligation-transfer or boundary evidence.
- Does not support: full GAIA solving, Terminal-Bench solving, SWE-bench patch solving/pass@1, or open-world answer-level correctness.

## Additional Honest-Reframe Artifacts

- Privileged-resource cost-of-coverage (feedback-level) table: `paper/tables/table_feedback_cost.md`. Supports: equal coverage is reachable without a certificate under medium non-leaky feedback; the certificate, not coverage, is the differentiator. Does not support: a coverage-dominance claim, or any certificate-utility bonus (the previously rigged proxy in `table18_certificate_utility_proxy.md` is removed). Script: `scripts/run_feedback_cost_analysis.py`.
- Canonicalize no-lexical ablation: `paper/tables/table_canonicalize_ablation.md`. Status: planned future work; placeholder with no results yet. Will support: a measured statement of how much held-out coverage depends on the deterministic lexical normalizer versus the language model. Until run, coverage reflects a model-plus-normalizer pipeline.
- Multi-model inter-annotator-agreement report: `outputs/iaa/iaa_report.md` (metrics `outputs/iaa/iaa_metrics.json`). Supports: status and coarse obligations reproduce across independent model families; fine obligations do not on adversarial inputs. Does not support: a completed human IAA study (the human review sheet `outputs/iaa/human_review_sheet.csv` is scaffolded).

## Appendix Table Candidates

- `paper/tables/table3_phase2c_registry_guarded_revised.md`
- `paper/tables/table6_llm_tool_router_baseline.md`
- `paper/tables/table8_cost_sensitivity.md`
- `paper/tables/table11_compiler_scaling.md`
- `paper/tables/table12_swe_harness_exec20_llm_pipeline.md`
- `paper/tables/related_work_comparison_table.md`
- `outputs/final/compiler_certificates/certificate_samples_report.md`
- `outputs/final/phase2/table3_category_breakdown.md`
- `outputs/final/phase2b/table1_profiler_summary.md`
- `outputs/final/phase2b/table2_obligation_level_f1.md`
- `outputs/final/phase2b/table3_category_breakdown.md`
- `outputs/final/phase2b/table4_top_error_cases.md`
- `outputs/final/phase2d/registry_perturbation_report.md`
- `outputs/final/phase2d/gold_label_permutation_report.md`
- `outputs/final/phase2d/negative_control_analysis_report.md`
