# GapHarness Final Artifact Index

This index points to the artifacts used by the current final manuscript draft, `gapharness_manuscript_v2.md`.

## Manuscript

- Final PDF: `paper/submission/arxiv_package/gapharness_arxiv.pdf`
- Markdown source: `paper/submission/arxiv_package/gapharness_manuscript_v2.md`
- Package-local Markdown source: `paper/submission/arxiv_package/gapharness_package_local.md`
- Generated LaTeX: `paper/submission/arxiv_package/gapharness_manuscript_v2.tex`
- References: `paper/submission/arxiv_package/references.bib`

Path note: root-level manifests use repository-relative paths such as `benchmarks/...` and `outputs/...`. The arXiv package includes selected portable copies under `paper/submission/arxiv_package/benchmark_sources/`, and `gapharness_package_local.md` resolves bibliography and figure paths relative to the package directory.

## Primary Results

- GapBench-1000 gold compiler: `outputs/final/results_gapbench1000_all_gold.jsonl`
- Compiler equivalence replay: `outputs/final/compiler_equivalence/replay_report.md`
- Synthetic registry scaling: `outputs/final/compiler_scaling/scaling_report.md`
- Compiler certificate samples: `outputs/final/compiler_certificates/certificate_samples_report.md`
- LLM profiler held-out test800: `outputs/final/phase2b/results_test800_heldout_with_selected_llm.jsonl`
- Registry-guarded post-hoc calibration: `outputs/final/phase2c/test800_registry_guarded/results_test800_llm_registry_guarded.jsonl`
- Diagnostic-feedback baselines and GapHarness-Repair on GapBench test800: `outputs/phase5_agentic_baselines/gapbench_test800/results_agentic_strategies.jsonl`
- Diagnostic-feedback baselines and GapHarness-Repair on HarnessChallenge-200: `outputs/phase5_agentic_baselines/harness_challenge200/results_agentic_strategies.jsonl`
- Diagnostic-feedback SWE-HarnessExec-20 traces: `outputs/phase5_agentic_baselines/harness_exec20_agentic/traces_agentic_strategies.jsonl`
- Feedback-level replay: `outputs/phase6_reviewer_evidence/feedback_levels/feedback_level_report.md`
- Certificate utility proxy and audit packet: `outputs/phase6_reviewer_evidence/certificate_utility/certificate_utility_report.md`
- Cost-scheme sensitivity and proxy calibration: `outputs/phase6_reviewer_evidence/cost_calibration/cost_calibration_report.md`
- Status confusion matrix: `outputs/phase6_reviewer_evidence/status_confusion/status_confusion_report.md`
- LLM profiler error taxonomy: `outputs/phase6_reviewer_evidence/profiler_error_taxonomy/profiler_error_taxonomy_report.md`
- RealBoundary-100 fresh author-seeded boundary diagnostic: `outputs/phase6_reviewer_evidence/realboundary100/realboundary100_report.md`
- Naturalistic-Holdout v0.1 independent candidate review package: `benchmarks/naturalistic_holdout/v0.1/`
- Naturalistic-Holdout v0.1 package copy: `paper/submission/arxiv_package/benchmark_sources/naturalistic_holdout_v0.1/`
- Stress tests and negative controls: `outputs/final/phase2d/`
- GapBench-Natural-200 project-owner-audited gold: `outputs/final/results_gapbench_natural200_human_audited_gold.jsonl`
- SWE-Obligation-50 project-owner-audited gold: `outputs/final/results_swe_obligation50_human_audited_gold.jsonl`
- SWE-Obligation-50 diagnostic summary: `outputs/final/swe_obligation50_diagnostic_summary.md`
- HarnessChallenge-200 targeted diagnostic: `outputs/final/harness_challenge200_diagnostic_report.md`
- HarnessChallenge-200 gold baselines: `outputs/final/results_harness_challenge200_author_reviewed_gold.jsonl`
- HarnessChallenge-200 LLM profiler: `outputs/final/harness_challenge200_llm/results_dev200_llm_single.jsonl`
- HarnessChallenge-200 registry-guarded profiler: `outputs/final/harness_challenge200_registry_guarded/results_dev200_llm_registry_guarded.jsonl`
- SWE-HarnessExec-20 executable traces: `outputs/final/harness_exec20/traces.jsonl`
- SWE-HarnessExec-20 LLM pipeline traces: `outputs/final/harness_exec20_llm_pipeline/traces.jsonl`
- SWE-HarnessExec-50 executable trace scale-up: `outputs/final/harness_exec50/traces.jsonl`
- Bootstrap confidence intervals: `outputs/final/bootstrap_ci/bootstrap_ci_report.md`

## Reviewer-Hardening Results

- LLM Tool Router dev200: `outputs/phase4/llm_tool_router_dev200/`
- LLM Tool Router test800: `outputs/phase4/llm_tool_router_test800/`
- LLM Tool Router negative controls: `outputs/phase4/llm_tool_router_negative_controls/`
- LLM Tool Router SWE-Obligation-50: `outputs/phase4/llm_tool_router_swe_obligation50/`
- LLM Tool Router HarnessChallenge-200: `outputs/phase4/llm_tool_router_harness_challenge200/`
- Secondary adversarial audit: `outputs/phase4/secondary_audit_gapbench100/`
- Diagnostic-feedback strategy baselines, GapHarness-Repair, and table index: `outputs/phase5_agentic_baselines/`

## Revised Paper Tables

- Manuscript Table 1, GapBench-1000 gold compiler: `paper/tables/table1_gapbench1000_gold_revised.md`
- Manuscript Table 2, compiler equivalence replay: `paper/tables/table10_compiler_equivalence_replay.md`
- Manuscript Table 3, synthetic registry scaling: `paper/tables/table15_compiler_ablation_scaling.md`
- Manuscript Table 4, mostly non-dominated registry scaling stress: `paper/tables/table16_non_dominated_scaling.md`
- Manuscript Table 5, held-out LLM profiler: `paper/tables/table2_phase2b_llm_heldout_revised.md`
- Manuscript Table 6, diagnostic-feedback strategy baselines: `paper/tables/table13_agentic_strategy_comparison.md`
- Manuscript Table 7, feedback-level replay: `paper/tables/table19_feedback_level_replay.md`
- Manuscript Table 8, certificate utility proxy: `paper/tables/table18_certificate_utility_proxy.md`
- Manuscript Table 9, cost-scheme sensitivity: `paper/tables/table20_cost_calibration_sensitivity.md`
- Manuscript Table 10, status confusion: `paper/tables/table21_status_confusion.md`
- Manuscript Table 11, profiler error taxonomy: `paper/tables/table22_profiler_error_taxonomy.md`
- Manuscript Table 12, anti-circularity stress tests and negative controls: `paper/tables/table4_phase2d_stress_tests_revised.md`
- Manuscript Table 13, HarnessChallenge-200 targeted diagnostic: `paper/tables/table9_harness_challenge200.md`
- Manuscript Table 14, SWE-HarnessExec-20 executable trace validation: `paper/tables/table14_swe_harness_exec20_agentic.md`
- Manuscript Table 15, SWE-HarnessExec-50 scale-up: `paper/tables/table17_swe_harness_exec50_scaleup.md`
- Manuscript Table 16, secondary adversarial audit: `paper/tables/table7_secondary_audit.md`
- Manuscript Table 17, external-validity and boundary diagnostics: `paper/tables/table5_boundary_diagnostics_revised.md`
- Appendix Table 18, negative controls: source rows in `outputs/final/phase2d/negative_controls/`
- Appendix Table 19, related work comparison: `paper/tables/related_work_comparison_table.md`
- Legacy/supporting table files not directly numbered in the current manuscript: `paper/tables/table3_phase2c_registry_guarded_revised.md`, `paper/tables/table6_llm_tool_router_baseline.md`, `paper/tables/table8_cost_sensitivity.md`, `paper/tables/table11_compiler_scaling.md`, `paper/tables/table12_swe_harness_exec20_llm_pipeline.md`

## Revised Paper Figures

- Figure 1, pipeline: `paper/figures/figure1_pipeline_print.png`
- Figure 2, cost-success frontier: `paper/figures/figure2_cost_success_frontier_revised_crop.png`
- Figure 3, grouped over/under/wrong bars: `paper/figures/figure3_grouped_over_under_wrong_crop.png`
- Figure 4, registry guard post-hoc calibration: `paper/figures/figure4_registry_guard_paper_crop.png`

## Claim Boundaries

- Harness success is obligation/capability coverage, not answer-level semantic correctness.
- Registry guarding is post-hoc registry-boundary calibration, not a fresh held-out discovery.
- GAIA-Transfer is a boundary diagnostic, not full GAIA solving.
- Terminal-Bench-obligation50 is an appendix scaffold, not Terminal-Bench solving.
- GapBench-Natural-200 is project-owner-audited but GapBench-derived.
- SWE-Obligation-50 is real-source obligation transfer, not SWE-bench patch solving/pass@1.
- HarnessChallenge-200 is a targeted diagnostic benchmark, not a natural-frequency estimate.
- RealBoundary-100 is fresh relative to the registry guard but author-seeded and review-pending.
- Naturalistic-Holdout v0.1 is a 200-row public GitHub issue candidate package independent of GapBench; rows carry `audit_status=candidate_for_human_review_not_gold` and are not gold until two-annotator audit, agreement metrics, and adjudication are complete.
- Certificate utility results are deterministic proxies plus a prepared audit packet, not completed human timing.
- Feedback-level replay is deterministic replay over existing routes/profiles, not a fresh LLM run.
- SWE-HarnessExec-20 is sandboxed executable trace validation with provided patches, not model patch generation or SWE-bench pass@1.
- SWE-HarnessExec-50 is the same provided-patch sandbox trace validation at a larger fixture count, not real-repository checkout or SWE-bench pass@1.
- Diagnostic-feedback baselines compare policies over a shared registry/executor/verifier, not framework substrates such as LangGraph or AutoGen.
- Verifier-repair and ReAct-style baselines receive verifier diagnostics after failed routes; their high coverage is a feedback-loop result, not a one-shot minimality certificate.
- GapHarness-Repair uses verifier diagnostics to patch profiles and recompile, preserving certificates; it is still a feedback-assisted upper-bound variant.
- Compiler scaling shows practical benefit on redundant synthetic registries; the non-dominated stress documents that exact compilation remains exponential in the worst case.
