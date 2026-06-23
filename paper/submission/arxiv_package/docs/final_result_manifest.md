# Final Result Manifest

Freeze stage: Paper-ready reviewer hardening plus diagnostic-feedback baselines, GapHarness-Repair, targeted diagnostics, and executable traces

This manifest identifies the final result artifacts used for the v2 technical report. Harness success means obligation/capability coverage under audited expected status, not answer-level task correctness.

## Primary Results

| Artifact | Path | Identity | Paper Role | Boundary |
|---|---|---|---|---|
| GapBench-1000 all-baseline result | `outputs/final/results_gapbench1000_all_gold.jsonl` | gold compiler result | Manuscript Table 1 | controlled benchmark with audited gold obligations |
| Compiler equivalence replay | `outputs/final/compiler_equivalence/replay_report.md` | frozen exact-output replay | Manuscript Table 2/text | certificates ignored for equality |
| Synthetic registry scaling | `outputs/final/compiler_scaling/scaling_report.md` | optimized exact compiler scaling check plus mostly non-dominated stress | Manuscript Tables 3-4/text | practical redundant-registry evidence and hard-boundary stress, not polynomial-time claim |
| Compiler certificate samples | `outputs/final/compiler_certificates/certificate_samples_report.md` | certificate-carrying compiler examples | text/artifact evidence | sample certificates, not a full proof checker |
| Held-out LLM profiler | `outputs/final/phase2b/results_test800_heldout_with_selected_llm.jsonl` | LLM-inferred result | Manuscript Table 5 | calibration gap remains |
| Registry-guarded held-out | `outputs/final/phase2c/test800_registry_guarded/results_test800_llm_registry_guarded.jsonl` | post-hoc registry-boundary calibration | text/Figure 4 | not a fresh held-out discovery |
| LLM Tool Router dev200 | `outputs/phase4/llm_tool_router_dev200/results_llm_tool_router.jsonl` | direct LLM module router baseline | supporting/text | no obligation ontology in routes |
| LLM Tool Router test800 | `outputs/phase4/llm_tool_router_test800/results_llm_tool_router.jsonl` | fair LLM router baseline | Manuscript Table 5/Table 6 source | sees registry and costs, not gold labels |
| LLM Tool Router negative controls | `outputs/phase4/llm_tool_router_negative_controls/results_llm_tool_router.jsonl` | tool-bait/pure-language check | Appendix Table 18 source | negative-control subset only |
| Secondary audit | `outputs/phase4/secondary_audit_gapbench100/secondary_audit_labels.jsonl` | secondary adversarial LLM audit | Manuscript Table 16/source | not human IAA |
| Registry perturbation | `outputs/final/phase2d/registry_perturbation/results_registry_perturbation.jsonl` | registry-boundary stress test | Manuscript Table 12 source | relevant subsets per perturbation |
| Gold permutation | `outputs/final/phase2d/gold_label_permutation/results_gold_label_permutation.jsonl` | anti-circularity stress test | Manuscript Table 12 source | artificial corruption model |
| Negative controls | `outputs/final/phase2d/negative_controls/results_negative_controls.jsonl` | keyword/tool-bait analysis | Appendix Table 18 source | pure/tool-bait categories only |
| SWE-Obligation-50 gold | `outputs/final/results_swe_obligation50_human_audited_gold.jsonl` | real-source obligation-transfer diagnostic | Manuscript Table 17/text | not SWE-bench solving or pass@1 |
| SWE-Obligation-50 LLM-safe diagnostic | `outputs/final/swe_obligation50_diagnostic_summary.md` | LLM/API-safe diagnostic view | Manuscript Table 17/text | shortened view for provider filters |
| HarnessChallenge-200 gold baselines | `outputs/final/results_harness_challenge200_author_reviewed_gold.jsonl` | targeted diagnostic gold-profile result | Manuscript Table 13/text | author-reviewed targeted diagnostic, not natural-frequency evidence |
| HarnessChallenge-200 LLM profiler | `outputs/final/harness_challenge200_llm/results_dev200_llm_single.jsonl` | targeted diagnostic LLM obligation inference | Manuscript Table 13/text | exposes profiler failure modes |
| HarnessChallenge-200 registry-guarded | `outputs/final/harness_challenge200_registry_guarded/results_dev200_llm_registry_guarded.jsonl` | GapBench-calibrated guard on targeted diagnostic | Manuscript Table 13/text | boundary result; guard worsens here |
| LLM Tool Router HarnessChallenge-200 | `outputs/phase4/llm_tool_router_harness_challenge200/results_llm_tool_router.jsonl` | direct LLM module router on targeted diagnostic | Manuscript Table 13/text | same registry/cost, no obligation labels |
| Diagnostic-feedback GapBench test800 | `outputs/phase5_agentic_baselines/gapbench_test800/results_agentic_strategies.jsonl` | workflow-generator, verifier-repair, ReAct-style, and GapHarness-Repair policy baselines | Manuscript Table 6/text | feedback-assisted upper-bound comparison over shared registry/executor/verifier; not framework comparison |
| Diagnostic-feedback HarnessChallenge-200 | `outputs/phase5_agentic_baselines/harness_challenge200/results_agentic_strategies.jsonl` | targeted diagnostic feedback-assisted baselines and GapHarness-Repair | Manuscript Table 6/text | repair/ReAct/GapHarness-Repair receive verifier diagnostics after failed routes |
| Feedback-level replay | `outputs/phase6_reviewer_evidence/feedback_levels/feedback_level_report.md` | weak/medium/strong verifier-feedback replay | Manuscript Table 7/text | deterministic replay, not fresh LLM calls |
| Certificate utility proxy | `outputs/phase6_reviewer_evidence/certificate_utility/certificate_utility_report.md` | deterministic auditability/debug-work proxy plus human audit packet | Manuscript Table 8/text | not completed human timing |
| Cost-scheme sensitivity and proxy calibration | `outputs/phase6_reviewer_evidence/cost_calibration/cost_calibration_report.md` | declared/uniform/latency/token/risk proxy-cost replay | Manuscript Table 9/text | proxy costs, not provider billing |
| Status confusion | `outputs/phase6_reviewer_evidence/status_confusion/status_confusion_report.md` | supported/unsupported/clarify status analysis | Manuscript Table 10/text | status-level only |
| Profiler error taxonomy | `outputs/phase6_reviewer_evidence/profiler_error_taxonomy/profiler_error_taxonomy_report.md` | LLM profiler failure-category analysis | Manuscript Table 11/text | categories can overlap |
| RealBoundary-100 | `outputs/phase6_reviewer_evidence/realboundary100/realboundary100_report.md` | fresh author-seeded side-effect boundary holdout | text/source | not independently audited yet |
| Naturalistic-Holdout v0.1 candidates | `benchmarks/naturalistic_holdout/v0.1/naturalistic_holdout_v0.1_candidates.jsonl` | independent public GitHub issue-derived candidate review package; portable package copy at `paper/submission/arxiv_package/benchmark_sources/naturalistic_holdout_v0.1/` | text/protocol | row-level `audit_status=candidate_for_human_review_not_gold`; no scores until two-annotator audit/adjudication |
| SWE-HarnessExec-20 traces | `outputs/final/harness_exec20/traces.jsonl` | executable sandbox pytest trace validation | Manuscript Table 14/text | provided patches, not model patch generation |
| SWE-HarnessExec-20 LLM pipeline | `outputs/final/harness_exec20_llm_pipeline/traces.jsonl` | LLM-profiled executable trace validation | Manuscript Table 14/text | obvious execution-heavy fixtures; direct module routing also succeeds |
| SWE-HarnessExec-20 diagnostic-feedback traces | `outputs/phase5_agentic_baselines/harness_exec20_agentic/traces_agentic_strategies.jsonl` | executable trace validation for workflow, repair, ReAct, and GapHarness-Repair policies | Manuscript Table 14/text | homogeneous fixtures; feedback-assisted policies also succeed |
| SWE-HarnessExec-50 traces | `outputs/final/harness_exec50/traces.jsonl` | executable sandbox pytest scale-up | Manuscript Table 15/text | provided patches over generated local fixtures; not real-repo checkout or pass@1 |
| Bootstrap CIs | `outputs/final/bootstrap_ci/bootstrap_ci_report.md` | nonparametric bootstrap over rows | text/source for uncertainty claims | descriptive intervals |

## Boundary Sources

| Source | Path | Identity | Boundary |
|---|---|---|---|
| GapBench-1000 | `outputs/final/benchmark_sources/gapbench_1000_human_audited.jsonl` | controlled audited benchmark | primary compiler benchmark |
| GAIA-Transfer-200 | `outputs/final/benchmark_sources/gaia_transfer200_human_audited.jsonl` | transfer labels | obligation-transfer only |
| GapBench-Natural-200 | `outputs/final/benchmark_sources/gapbench_natural_200_human_audited.jsonl` | project-owner-audited naturalized source | GapBench-derived |
| SWE-Obligation-50 | `outputs/final/benchmark_sources/swe_obligation50_human_audited.jsonl` | real-source SWE-bench Lite obligation-transfer source | not patch solving |
| SWE-Obligation-50 LLM-safe view | `outputs/final/benchmark_sources/swe_obligation50_llm_safe_view.jsonl` | shortened diagnostic view shared by LLM systems | source labels come from the original project-owner-audited view; not a replacement for gold source labels |
| Terminal-Bench-obligation50 | `outputs/final/benchmark_sources/terminal_obligation50_for_review.jsonl` | terminal-style scaffold | not Terminal-Bench solving |
| HarnessChallenge-200 | `benchmarks/harness_challenge/v1.0/harness_challenge200_author_reviewed.jsonl` | targeted diagnostic benchmark | not natural distribution; independent human audit not claimed |
| RealBoundary-100 | `benchmarks/realboundary/v0.1/realboundary100_author_seeded.jsonl` | fresh boundary holdout package | author-seeded and review-pending |
| Naturalistic-Holdout v0.1 | `benchmarks/naturalistic_holdout/v0.1/naturalistic_holdout_v0.1_candidates.jsonl` | 200 public GitHub issue candidate rows plus review sheet | independent of GapBench but not human-audited gold |
| Naturalistic-Holdout v0.1 package copy | `paper/submission/arxiv_package/benchmark_sources/naturalistic_holdout_v0.1/` | portable package copy with candidates, review sheet, schema, manifest, README, and redaction scan | package-local copy, not an additional benchmark |
| SWE-HarnessExec-20 | `benchmarks/harness_exec/v1.0/swe_harness_exec20_cases.jsonl` | sandbox executable fixtures | not SWE-bench checkout or pass@1 |
| SWE-HarnessExec-50 | `benchmarks/harness_exec/v1.1/swe_harness_exec50_cases.jsonl` | sandbox executable scale-up fixtures | not SWE-bench checkout or pass@1 |

## Final Manuscript Artifacts

- `paper/drafts/gapharness_manuscript_v2.md`
- `paper/drafts/gapharness_manuscript_v2.tex`
- `paper/drafts/gapharness_manuscript_v2.pdf`
- `paper/submission/arxiv_package/gapharness_arxiv.pdf`
- `paper/submission/arxiv_package/gapharness_package_local.md`

## Final Tables

- `paper/tables/table1_gapbench1000_gold_revised.md`
- `paper/tables/table2_phase2b_llm_heldout_revised.md`
- `paper/tables/table3_phase2c_registry_guarded_revised.md`
- `paper/tables/table4_phase2d_stress_tests_revised.md`
- `paper/tables/table5_boundary_diagnostics_revised.md`
- `paper/tables/table6_llm_tool_router_baseline.md`
- `paper/tables/table7_secondary_audit.md`
- `paper/tables/table8_cost_sensitivity.md`
- `paper/tables/table9_harness_challenge200.md`
- `paper/tables/table10_compiler_equivalence_replay.md`
- `paper/tables/table11_compiler_scaling.md`
- `paper/tables/table12_swe_harness_exec20_llm_pipeline.md`
- `paper/tables/table13_agentic_strategy_comparison.md`
- `paper/tables/table14_swe_harness_exec20_agentic.md`
- `paper/tables/table15_compiler_ablation_scaling.md`
- `paper/tables/table16_non_dominated_scaling.md`
- `paper/tables/table17_swe_harness_exec50_scaleup.md`
- `paper/tables/table18_certificate_utility_proxy.md`
- `paper/tables/table19_feedback_level_replay.md`
- `paper/tables/table20_cost_calibration_sensitivity.md`
- `paper/tables/table21_status_confusion.md`
- `paper/tables/table22_profiler_error_taxonomy.md`
- `paper/tables/related_work_comparison_table.md`

## Final Figures

- `paper/figures/figure1_pipeline_print.png`
- `paper/figures/figure2_cost_success_frontier_revised_crop.png`
- `paper/figures/figure3_grouped_over_under_wrong_crop.png`
- `paper/figures/figure4_registry_guard_paper_crop.png`

## Non-Claims

- GapHarness does not claim full GAIA solving.
- GapHarness does not claim Terminal-Bench solving.
- GapHarness does not execute arbitrary real-world side effects.
- Registry guarding is post-hoc registry-boundary calibration.
- GapBench is controlled and factorial, not a complete real-world benchmark.
- SWE-Obligation-50 is obligation-transfer only, not SWE-bench solving or patch-level correctness.
- HarnessChallenge-200 is targeted diagnostic evidence, not a natural-frequency benchmark.
- RealBoundary-100 is fresh relative to the registry guard but author-seeded and review-pending.
- Naturalistic-Holdout v0.1 is independent of GapBench and has a review sheet plus row-level candidate audit status, but it is a candidate package until two-annotator labels, agreement metrics, and adjudication are complete.
- Certificate utility results are deterministic proxies plus a human audit packet, not completed human timing.
- Feedback-level replay is deterministic replay over existing routes/profiles, not fresh LLM calls.
- SWE-HarnessExec-20 validates sandbox trace execution with provided patches, not model-generated repairs or SWE-bench pass@1.
- SWE-HarnessExec-50 scales the same provided-patch sandbox trace validation; it is not real-repository checkout, model-generated repair, or SWE-bench pass@1.
- Diagnostic-feedback baseline results compare harness-selection policies over a shared substrate; they do not support a claim that GapHarness is categorically better than LangGraph, AutoGen, or any framework.
- Verifier-repair and ReAct-style baselines use verifier diagnostics after failed routes and do not emit GapHarness-style registry-relative minimality certificates.
- GapHarness-Repair preserves certificates by converting verifier diagnostics into profile patches and recompiling, but it is a feedback-assisted upper-bound variant rather than a one-shot profiler result.
- Compiler replay/scaling validates optimizer behavior under frozen profiles and synthetic registries, not end-user task utility; the mostly non-dominated stress confirms exact search remains exponential in harder registries.
