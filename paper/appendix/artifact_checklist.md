# Artifact Checklist

## Benchmark Files

- GapBench-1000 frozen source: `outputs/final/benchmark_sources/gapbench_1000_human_audited.jsonl`
- GAIA-Transfer-200 frozen source: `outputs/final/benchmark_sources/gaia_transfer200_human_audited.jsonl`
- GapBench-Natural-200 frozen source: `outputs/final/benchmark_sources/gapbench_natural_200_human_audited.jsonl`
- SWE-Obligation-50 frozen source: `outputs/final/benchmark_sources/swe_obligation50_human_audited.jsonl`
- SWE-Obligation-50 LLM-safe diagnostic view: `outputs/final/benchmark_sources/swe_obligation50_llm_safe_view.jsonl`
- Terminal-Bench-obligation50 frozen source: `outputs/final/benchmark_sources/terminal_obligation50_for_review.jsonl`
- SWE-HarnessExec-50 sandbox source: `benchmarks/harness_exec/v1.1/swe_harness_exec50_cases.jsonl`
- RealBoundary-100 author-seeded source: `benchmarks/realboundary/v0.1/realboundary100_author_seeded.jsonl`
- Naturalistic-Holdout v0.1 candidate package: `benchmarks/naturalistic_holdout/v0.1/naturalistic_holdout_v0.1_candidates.jsonl`
- Naturalistic-Holdout v0.1 redaction scan summary: `benchmarks/naturalistic_holdout/v0.1/redaction_scan_summary.md`

## Output Result Files

- GapBench-1000 gold result: `outputs/final/results_gapbench1000_all_gold.jsonl`
- GAIA-Transfer gold smoke result: `outputs/final/results_gaia_transfer200_human_audited_gold.jsonl`
- GapBench-Natural project-owner-audited gold result: `outputs/final/results_gapbench_natural200_human_audited_gold.jsonl`
- SWE-Obligation-50 project-owner-audited gold result: `outputs/final/results_swe_obligation50_human_audited_gold.jsonl`
- SWE-Obligation-50 diagnostic summary: `outputs/final/swe_obligation50_diagnostic_summary.md`
- SWE-HarnessExec-50 trace scale-up: `outputs/final/harness_exec50/traces.jsonl`
- LLM profiler outputs: `outputs/final/phase2b/`
- Registry-guarded outputs: `outputs/final/phase2c/`
- Stress-test outputs: `outputs/final/phase2d/`
- Diagnostic-feedback strategy outputs: `outputs/phase5_agentic_baselines/`
- Phase 6 reviewer-evidence outputs: `outputs/phase6_reviewer_evidence/`
- RealBoundary-100 author-seeded baseline output: `outputs/phase6_reviewer_evidence/realboundary100/results_realboundary100_author_seeded_baselines.jsonl`

## Figures

- Main figures: `paper/figures/figure1_pipeline.svg` through `paper/figures/figure4_registry_guard_unsupported_fp_reduction.svg`
- Frozen figure copies: `figures/final/`

## Tables

- Main tables: `paper/tables/table1_gapbench1000_gold_revised.md` through `paper/tables/table5_boundary_diagnostics_revised.md`
- SWE-HarnessExec-50 scale-up table: `paper/tables/table17_swe_harness_exec50_scaleup.md`
- Table index: `paper/tables/final_table_index.md`
- Phase 6 reviewer-evidence tables: `paper/tables/table18_certificate_utility_proxy.md` through `paper/tables/table22_profiler_error_taxonomy.md`

## Scripts

- Gold deterministic run: `scripts/run_phase2_gold_experiments.sh`
- LLM profiler and registry-guarded sweeps: `scripts/run_phase2b_llm_sweep.py`
- Stress tests: `scripts/run_phase2d_stress_tests.py`
- Phase 2 artifact generation: `scripts/generate_phase2_artifacts.py`
- Dataset freeze helpers: `scripts/freeze_phase2_datasets.py`
- SWE-Obligation-50 builder: `scripts/build_swe_obligation.py`
- GapBench-Natural audit finalizer: `scripts/finalize_gapbench_natural_audit.py`
- Diagnostic-feedback baselines and GapHarness-Repair: `scripts/run_phase5_agentic_baselines.py`
- Phase 6 reviewer-evidence replay: `scripts/run_phase6_reviewer_evidence.py`

## Test Commands

```bash
python3 -m pytest
python3 -m py_compile scripts/*.py
PYTHONPATH=. python3 scripts/run_phase6_reviewer_evidence.py all
shasum -a 256 -c outputs/final/checksums.sha256
cd paper/submission/arxiv_package && shasum -a 256 -c checksums.sha256
```

## Checksum File

- `outputs/final/checksums.sha256`
- `paper/submission/arxiv_package/checksums.sha256`

## Secret Scan Statement

Before sharing or submission, run a broad secret scan and the project-specific secret-fragment scan. No API keys, Hugging Face tokens, or private credentials should appear in manuscript, tables, figures, appendix files, submission packages, or checksums.

## Known Limitations

- GapHarness does not claim full GAIA solving.
- GapHarness does not claim Terminal-Bench solving.
- GapHarness does not claim SWE-bench patch solving or pass@1.
- SWE-HarnessExec-50 is provided-patch sandbox trace validation, not real-repository checkout or model-generated repair.
- Naturalistic-Holdout v0.1 rows carry `audit_status=candidate_for_human_review_not_gold`; the owner-confirmed review sheet package is not a scored benchmark until two-annotator labels, agreement metrics, and adjudication are complete.
- RealBoundary-100 rows carry `audit_status=author_seeded_for_fresh_holdout_review`; it is a fresh boundary diagnostic, not an independently audited external benchmark.
- The executor is a deterministic sandbox/mock runtime and does not perform irreversible external actions.
- GapBench-1000 is controlled and factorial, not a complete open-world benchmark.
- The LLM profiler is not fully calibrated.
- Minimality is relative to the declared obligation ontology, module registry, dependency model, and cost function.
