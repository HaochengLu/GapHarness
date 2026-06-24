# GapHarness Paper MVP Results

## What Is Reproducible Now

- Frozen 1000-task GapBench v1.0 benchmark, human-audited and confirmed by the project owner.
- Frozen 200-task GAIA-Transfer v1.0 benchmark, human-audited and confirmed by the project owner.
- 200-task GapBench-Natural v1.0 draft package for human review.
- Exact minimal compiler over a declared registry.
- Direct / Tool Router / Always-full / Difficulty Router / Oracle Minimal baselines.
- Deterministic sufficiency verifier.
- Drop-one minimality verifier.
- LLM profiler using an OpenAI-compatible API endpoint.
- Streaming, resumable JSONL experiment runner.
- Regeneratable paper tables and SVG figures.

## Gold Profiler Baseline

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| always_full | 100 | 0.86 | 16.00 | 2.88 | 13.12 | 0.86 | 0.00 | 0.00 | 0.51 |
| difficulty_router | 100 | 0.61 | 5.84 | 2.88 | 2.96 | 0.48 | 0.25 | 0.15 | 0.24 |
| direct | 100 | 0.18 | 0.00 | 2.88 | -2.88 | 0.00 | 0.68 | 0.00 | 0.00 |
| gapharness | 100 | 1.00 | 2.88 | 2.88 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 100 | 1.00 | 2.88 | 2.88 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_router | 100 | 0.51 | 3.11 | 2.88 | 0.23 | 0.25 | 0.35 | 0.27 | 0.12 |

## Expanded GapBench 1000

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| always_full | 1000 | 0.94 | 16.00 | 3.67 | 12.33 | 0.94 | 0.00 | 0.00 | 0.51 |
| difficulty_router | 1000 | 0.43 | 3.46 | 3.67 | -0.21 | 0.28 | 0.51 | 0.16 | 0.14 |
| direct | 1000 | 0.20 | 0.00 | 3.67 | -3.67 | 0.00 | 0.74 | 0.00 | 0.00 |
| gapharness | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_router | 1000 | 0.34 | 2.10 | 3.67 | -1.57 | 0.11 | 0.60 | 0.42 | 0.06 |

Phase 2 table and figure outputs:

- `outputs/phase2/table1_gapbench1000_gold.md`
- `outputs/phase2/table2_transfer_and_review_smokes.md`
- `outputs/phase2/table3_category_breakdown.md`
- `outputs/phase2/failure_mode_summary.md`
- `figures/phase2/cost_success_frontier.svg`
- `figures/phase2/over_under_wrong_bars.svg`
- `figures/phase2/regret_distribution.svg`
- `figures/phase2/drop_one_necessity.svg`

## LLM Profiler Cascade

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gapharness | 100 | 1.00 | 3.68 | 2.88 | 0.80 | 0.26 | 0.00 | 0.00 | 0.10 |

Profiler coverage:

| Obligation Precision | Obligation Recall | Obligation F1 | Capability Precision | Capability Recall | Capability F1 |
|---:|---:|---:|---:|---:|---:|
| 0.785 | 0.991 | 0.876 | 0.641 | 0.966 | 0.770 |

## Takeaway

The MVP supports the central technical-report claim: compiling from obligations can cleanly separate insufficiency from over-harnessing. The gold profiler proves the compiler/verifier path; the LLM profiler shows the real calibration tradeoff. Current LLM profiling reaches full sufficiency on the 100-task seed after canonicalization, but pays a measurable minimality cost.

## Phase 2B LLM Profiler Calibration

Dev200 profilers:

| Profiler | Success | Avg Cost | Regret | Over | Under | Wrong | Obl F1 | Exact Set |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_single | 0.92 | 3.68 | 0.06 | 0.19 | 0.08 | 0.00 | 0.929 | 0.79 |
| llm_recall | 0.96 | 3.94 | 0.32 | 0.20 | 0.04 | 0.00 | 0.930 | 0.80 |
| llm_minimality | 0.98 | 3.82 | 0.20 | 0.14 | 0.02 | 0.00 | 0.949 | 0.86 |

The pre-registered selection rule chose `llm_single`: it satisfied the sufficiency guard and had the lowest minimality regret among passing profilers.

Held-out test800:

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 800 | 0.20 | 0.00 | 3.69 | -3.69 | 0.00 | 0.74 | 0.00 | 0.00 |
| tool_router | 800 | 0.32 | 1.96 | 3.69 | -1.72 | 0.09 | 0.62 | 0.43 | 0.06 |
| difficulty_router | 800 | 0.41 | 3.22 | 3.69 | -0.47 | 0.26 | 0.53 | 0.15 | 0.13 |
| always_full | 800 | 0.94 | 16.00 | 3.69 | 12.31 | 0.94 | 0.00 | 0.00 | 0.51 |
| gold_oracle_gap_harness | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| selected_llm_gap_harness | 800 | 0.89 | 3.59 | 3.69 | -0.09 | 0.14 | 0.09 | 0.01 | 0.05 |

Phase 2B artifacts:

- `outputs/phase2b/phase2b_summary.md`
- `outputs/phase2b/table1_profiler_summary.md`
- `outputs/phase2b/table2_obligation_level_f1.md`
- `outputs/phase2b/table3_category_breakdown.md`
- `outputs/phase2b/table4_top_error_cases.md`
- `outputs/phase2b/heldout_test800_report.md`

## GAIA Transfer Smoke

GAIA now loads with:

```python
from datasets import load_dataset

ds = load_dataset("gaia-benchmark/GAIA", "2023_all")
```

Observed splits:

- test: 301 rows
- validation: 165 rows

Generated human-audited transfer subsets:

- `benchmarks/gaia_validation_100_human_audited.jsonl`
- `benchmarks/gaia_test_100_human_audited.jsonl`
- `benchmarks/gaia_transfer_200_human_audited.jsonl`

The project owner reviewed the GAIA validation100/test100 labels (single annotator).

Gold-compiler smoke:

| Subset | N | Success | Avg Cost | Oracle Cost | Regret |
|---|---:|---:|---:|---:|---:|
| GAIA transfer200 human-audited | 200 | 1.00 | 1.48 | 1.48 | 0.00 |

## GapBench-Natural Review Package

Generated review assets:

- `benchmarks/gapbench_natural/v1.0/gapbench_natural_200_for_review.jsonl`
- `benchmarks/gapbench_natural/v1.0/gapbench_natural_200_review_sheet.csv`
- `benchmarks/gapbench_natural/v1.0/manifest.json`
- `benchmarks/gapbench_natural/v1.0/README.md`

Audit status: for review. The labels are inherited from human-audited GapBench v1.0 source tasks, but the naturalized user-facing queries should be reviewed before final paper claims.

Gold-compiler smoke:

| Subset | N | Success | Avg Cost | Oracle Cost | Regret |
|---|---:|---:|---:|---:|---:|
| GapBench-Natural-200 for review | 200 | 1.00 | 2.83 | 2.83 | 0.00 |

## Phase 2C Registry-Guarded Calibration

Phase 2C evaluates a deterministic registry guard over the Phase 2B `llm_single` profiler output. The guard corrects sandbox/mock/local actions that were incorrectly lowered into unsupported `real_world_side_effect`.

Dev200:

| Profiler | N | Success | Avg Cost | Regret | Over | Under | Unsupported FP |
|---|---:|---:|---:|---:|---:|---:|---:|
| Phase 2B `llm_single` | 200 | 0.92 | 3.68 | 0.06 | 0.19 | 0.08 | 14 |
| Phase 2C `llm_registry_guarded` | 200 | 0.97 | 4.02 | 0.40 | 0.20 | 0.03 | 4 |

Held-out test800:

| System | N | Success | Avg Cost | Regret | Over | Under | Unsupported FP |
|---|---:|---:|---:|---:|---:|---:|---:|
| Phase 2B selected `llm_single` | 800 | 0.89 | 3.59 | -0.09 | 0.14 | 0.09 | 56 |
| Phase 2C `llm_registry_guarded` | 800 | 0.94 | 3.98 | 0.30 | 0.15 | 0.03 | 12 |

GAIA-Transfer registry-guarded run is a limitation result, not an answer-level GAIA claim: success 0.56, over-harness 0.89, under-harness 0.44, guard applied 0 / 200.

## Phase 2D Stress Tests

### Registry Perturbation

| Perturbation | Removed Module | Base Success | Perturbed Success | Unsupported | Under-covered | Dominant Missing |
|---|---|---:|---:|---:|---:|---|
| remove_python_executor | python_executor | 1.00 | 0.00 | 1.00 | 1.00 | execution |
| remove_source_span_checker | source_span_checker | 1.00 | 0.00 | 1.00 | 1.00 | source_spans |
| remove_permission_gate | permission_gate | 1.00 | 0.00 | 1.00 | 1.00 | permission |
| remove_sandbox_file_editor | sandbox_file_editor | 1.00 | 0.00 | 1.00 | 1.00 | diff |
| remove_web_retrieval | web_retrieval | 1.00 | 0.00 | 1.00 | 1.00 | evidence_sources |
| remove_contract_verifier | contract_verifier | 1.00 | 0.00 | 1.00 | 1.00 | contract_check |

### Gold Label Permutation

| Condition | N | Success | Regret | Over | Under | Wrong | Verifier Fail |
|---|---:|---:|---:|---:|---:|---:|---:|
| correct gold | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| permuted labels | 200 | 0.17 | 0.24 | 0.55 | 0.83 | 0.79 | 0.83 |

Permutation integrity: 200 / 200 corrupted profiles changed obligations or required capabilities; no-op corruptions: 0.

### Negative Controls

| Category | System | N | Success | Avg Cost | Over |
|---|---|---:|---:|---:|---:|
| pure_language_negative | GapHarness gold | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | GapHarness LLM | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | Registry-guarded GapHarness | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | Always-full | 100 | 1.00 | 16.00 | 1.00 |
| tool_bait | GapHarness gold | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | GapHarness LLM | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | Registry-guarded GapHarness | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | Tool Router | 100 | 1.00 | 1.26 | 0.51 |
| tool_bait | Difficulty Router | 100 | 1.00 | 1.22 | 0.51 |
| tool_bait | Always-full | 100 | 1.00 | 16.00 | 1.00 |

Interpretation boundary: registry perturbation is an affordance-boundary stress test, gold-label permutation is an anti-circularity test, and negative controls test obligation sensitivity rather than open-world answer correctness.
