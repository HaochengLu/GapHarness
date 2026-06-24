# Final Result Manifest

Freeze stage: Superseded Phase 3 workshop package; current final package is `paper/submission/arxiv_package`

This manifest is retained for provenance of the older 8-page workshop package. The current final technical-report package is `paper/submission/arxiv_package`; use `docs/final_result_manifest.md` for the authoritative result identity and boundary manifest.

## Primary Results

| Artifact | Frozen Path | Identity | Paper Role | Boundary |
|---|---|---|---|---|
| GapBench-1000 all-baseline result | `outputs/final/results_gapbench1000_all_gold.jsonl` | gold compiler result | Table 1 | controlled benchmark with project-owner-audited gold obligations |
| GapBench-1000 summary | `outputs/final/summary_gapbench1000_all_gold.md` | gold compiler summary | Table 1 source | not an open-world answer benchmark |
| Phase 2B held-out LLM profiler | `outputs/final/phase2b/results_test800_heldout_with_selected_llm.jsonl` | LLM-inferred result | Table 2 | selected `llm_single`, calibration gap remains |
| Phase 2C registry-guarded held-out | `outputs/final/phase2c/test800_registry_guarded/results_test800_llm_registry_guarded.jsonl` | registry-guarded calibration result | Table 3 | sufficiency-oriented calibration, cost/regret increase |
| Phase 2D registry perturbation | `outputs/final/phase2d/registry_perturbation/results_registry_perturbation.jsonl` | stress-test result | Table 4 | relevant first-N 60-task subsets per perturbation |
| Phase 2D gold permutation | `outputs/final/phase2d/gold_label_permutation/results_gold_label_permutation.jsonl` | anti-circularity stress-test result | Table 4 | artificial corruption model, 200/200 profiles changed |
| Phase 2D negative controls | `outputs/final/phase2d/negative_controls/results_negative_controls.jsonl` | negative-control result | Table 4 | pure/tool-bait categories only |

## Frozen Benchmark Sources

| Source | Frozen Path | Identity | Boundary |
|---|---|---|---|
| GapBench-1000 | `outputs/final/benchmark_sources/gapbench_1000_human_audited.jsonl` | project-owner-audited controlled benchmark | primary compiler benchmark |
| GAIA-Transfer-200 | `outputs/final/benchmark_sources/gaia_transfer200_human_audited.jsonl` | project-owner-audited transfer labels | obligation-transfer only |
| GapBench-Natural-200 | `outputs/final/benchmark_sources/gapbench_natural_200_human_audited.jsonl` | project-owner-audited naturalized source | GapBench-derived, not an independent naturalistic benchmark |
| Terminal-Bench-obligation50 | `outputs/final/benchmark_sources/terminal_obligation50_for_review.jsonl` | execution-heavy transfer scaffold | labels pending audit, not Terminal-Bench solving |

## Transfer and Boundary Results

| Artifact | Frozen Path | Identity | Paper Role | Boundary |
|---|---|---|---|---|
| GAIA-Transfer gold smoke | `outputs/final/results_gaia_transfer200_human_audited_gold.jsonl` | transfer-only gold compiler smoke | Table 5 | obligation labels only, not GAIA answer solving |
| GAIA registry-guarded | `outputs/final/phase2c/gaia_transfer_registry_guarded/results_gaia_transfer_llm_registry_guarded.jsonl` | limitation result | Table 5 | not a claim of full GAIA solving |
| GapBench-Natural project-owner-audited result | `outputs/final/results_gapbench_natural200_human_audited_gold.jsonl` | project-owner-audited naturalized result | Table 5 | GapBench-derived, not independent naturalistic evidence |
| Terminal-Bench-obligation50 | `outputs/final/terminal_obligation50_for_review.jsonl` | appendix transfer scaffold | Appendix | labels pending human audit, not Terminal-Bench solving |

## Final Tables

- `paper/tables/table1_gapbench1000_gold.md`
- `paper/tables/table2_phase2b_llm_heldout.md`
- `paper/tables/table3_phase2c_registry_guarded.md`
- `paper/tables/table4_phase2d_stress_tests.md`
- `paper/tables/table5_transfer_boundary.md`

## Final Figures

- `paper/figures/figure1_pipeline.svg`
- `paper/figures/figure2_cost_success_frontier.svg`
- `paper/figures/figure3_over_under_wrong_bars.svg`
- `paper/figures/figure4_registry_guard_unsupported_fp_reduction.svg`

## Appendix Artifacts

- `paper/appendix/reproducibility.md`
- `paper/appendix/stress_test_details.md`
- `paper/appendix/transfer_scaffolds.md`

## Non-Claims

- GapHarness does not claim full GAIA solving.
- GapHarness does not claim Terminal-Bench solving.
- GapHarness does not execute arbitrary real-world side effects.
- GapBench is a controlled factorial benchmark, not a complete real-world benchmark.
