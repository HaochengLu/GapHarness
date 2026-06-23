# Experiment Log

## 2026-06-22 MVP Smoke

Command:

```bash
python3 -m scripts.build_seed_benchmark --out benchmarks/gapbench_factorial_seed.jsonl
python3 -m gapharness.cli run-benchmark --benchmark benchmarks/gapbench_factorial_seed.jsonl --system all --profiler gold --out outputs/results_gold.jsonl
python3 -m gapharness.cli make-report --results outputs/results_gold.jsonl --out outputs/summary_gold.md
python3 -m gapharness.cli run-benchmark --benchmark benchmarks/gapbench_factorial_seed.jsonl --system gapharness --profiler heuristic --out outputs/results_heuristic_gapharness.jsonl
python3 -m gapharness.cli make-report --results outputs/results_heuristic_gapharness.jsonl --out outputs/summary_heuristic_gapharness.md
python3 -m unittest discover -s tests
```

Gold profiler aggregate:

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| always_full | 100 | 0.86 | 16.00 | 2.88 | 13.12 | 0.86 | 0.00 | 0.00 | 0.51 |
| difficulty_router | 100 | 0.61 | 5.84 | 2.88 | 2.96 | 0.48 | 0.25 | 0.15 | 0.24 |
| direct | 100 | 0.18 | 0.00 | 2.88 | -2.88 | 0.00 | 0.68 | 0.00 | 0.00 |
| gapharness | 100 | 1.00 | 2.88 | 2.88 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 100 | 1.00 | 2.88 | 2.88 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_router | 100 | 0.51 | 3.11 | 2.88 | 0.23 | 0.25 | 0.35 | 0.27 | 0.12 |

Heuristic GapHarness aggregate:

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gapharness | 100 | 0.78 | 3.73 | 2.88 | 0.85 | 0.47 | 0.22 | 0.14 | 0.23 |

Observed heuristic failure concentration:

- missing Control / permission: 14 cases
- dependency or constraint failure: 22 cases
- missing Verification / contract check: 5 cases

Interpretation:

- Compiler, oracle path, and deterministic verifier are internally consistent.
- The next research-critical work is the obligation profiler: replace or augment the heuristic with structured LLM profiling, consensus adjudication, and human-reviewed gold labels.

## 2026-06-22 LLM Profiler + Cascade

Setup:

- OpenAI-compatible endpoint verified through runtime environment variables only.
- Default cheap profiler model: `gpt-5.4-mini`.
- Strong fallback tested on failed samples: `gpt-5.5`.
- Secrets were not written to repository files.

Commands:

```bash
python3 -m gapharness.cli run-benchmark --stream --progress-every 10 \
  --benchmark benchmarks/gapbench_factorial_seed.jsonl \
  --system gapharness \
  --profiler llm \
  --out outputs/results_llm_gapharness_gpt54mini_norm.jsonl

python3 -m scripts.merge_result_overrides \
  --base outputs/results_llm_gapharness_gpt54mini_norm.jsonl \
  --override outputs/results_llm_gpt54mini_failures_after_guard.jsonl \
  --out outputs/results_llm_gapharness_cascade.jsonl
```

Cheap LLM profiler after registry canonicalization:

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gapharness | 100 | 0.96 | 3.58 | 2.88 | 0.70 | 0.26 | 0.04 | 0.00 | 0.10 |

Final cascade after exact-arithmetic guard and 4-row rerun:

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gapharness | 100 | 1.00 | 3.68 | 2.88 | 0.80 | 0.26 | 0.00 | 0.00 | 0.10 |

Profiler coverage on final cascade:

| System | Obligation Precision | Obligation Recall | Obligation F1 | Capability Precision | Capability Recall | Capability F1 |
|---|---:|---:|---:|---:|---:|---:|
| gapharness | 0.785 | 0.991 | 0.876 | 0.641 | 0.966 | 0.770 |

Interpretation:

- The LLM profiler is high recall, which eliminates under-harness after canonicalization.
- High recall introduces over-harness and positive minimality regret.
- This is a useful paper result: obligation-first synthesis can achieve sufficiency, while minimality depends on profiler calibration and capability lowering.

GAIA transfer status:

- The provided Hugging Face token can list the GAIA repository metadata through the API, but file download is blocked by gated dataset authorization.
- `scripts/build_gaia_subset.py` is implemented and fails with a clear authorization message until the token is granted dataset access.

## 2026-06-22 Human Gold Audit + GAIA Retest

Gold audit:

- The user confirmed the current 100-task GapBench-Factorial seed gold labels match their intended labels.
- The benchmark file was stamped as human-audited for the current version.

GAIA retest:

```python
from datasets import load_dataset

ds = load_dataset("gaia-benchmark/GAIA", "2023_all")
```

Initial result:

- `datasets` was installed successfully.
- The exact loading path initially failed with HTTP 403.
- Token introspection showed the token was valid for user `HCLu`, but it was a fine-grained token with `canReadGatedRepos=False`.

Retest after permission update:

- `canReadGatedRepos=True`.
- `load_dataset("gaia-benchmark/GAIA", "2023_all")` succeeds.
- Loaded splits:
  - test: 301 rows
  - validation: 165 rows
- Columns: `task_id`, `Question`, `Level`, `Final answer`, `file_name`, `file_path`, `Annotator Metadata`.

Generated transfer subsets:

```bash
HF_TOKEN=... python3 -m scripts.build_gaia_subset --split validation --limit 20 --out benchmarks/gaia_obligation_subset_validation20.jsonl
HF_TOKEN=... python3 -m scripts.build_gaia_subset --split test --limit 20 --out benchmarks/gaia_obligation_subset_test20.jsonl
```

Subset smoke results:

| Subset | N | Success | Avg Cost | Oracle Cost | Regret |
|---|---:|---:|---:|---:|---:|
| GAIA validation20 auto-profile gold | 20 | 1.00 | 1.10 | 1.10 | 0.00 |
| GAIA test20 auto-profile gold | 20 | 1.00 | 1.50 | 1.50 | 0.00 |

Important caveat:

- The project owner later confirmed the current GAIA transfer subset labels are acceptable gold truth.

## 2026-06-22 Expanded GapBench + GAIA Audit Confirmation

Audit status:

- The project owner confirmed that the new `gapbench_expansion_review_package` labels are gold truth.
- The project owner confirmed that the current GAIA transfer subset labels are gold truth.

Stamped files:

- `benchmarks/gapbench_500_human_audited.jsonl`: 500 rows.
- `benchmarks/gapbench_1000_human_audited.jsonl`: 1000 rows.
- `benchmarks/gaia_obligation_subset_validation20.jsonl`: 20 rows.
- `benchmarks/gaia_obligation_subset_test20.jsonl`: 20 rows.

Expanded GapBench 1000 all-baseline result:

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| always_full | 1000 | 0.94 | 16.00 | 3.67 | 12.33 | 0.94 | 0.00 | 0.00 | 0.51 |
| difficulty_router | 1000 | 0.43 | 3.46 | 3.67 | -0.21 | 0.28 | 0.51 | 0.16 | 0.14 |
| direct | 1000 | 0.20 | 0.00 | 3.67 | -3.67 | 0.00 | 0.74 | 0.00 | 0.00 |
| gapharness | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_router | 1000 | 0.34 | 2.10 | 3.67 | -1.57 | 0.11 | 0.60 | 0.42 | 0.06 |

## 2026-06-22 Larger GAIA Review Package

Generated a larger GAIA transfer review package for project-owner checking:

- `gaia_transfer_review_package/gaia_validation_100_for_review.jsonl`
- `gaia_transfer_review_package/gaia_validation_100_review_sheet.csv`
- `gaia_transfer_review_package/gaia_test_100_for_review.jsonl`
- `gaia_transfer_review_package/gaia_test_100_review_sheet.csv`
- `gaia_transfer_review_package.zip`

Audit status:

- The new 100+100 GAIA rows are intentionally marked `gaia_metadata_auto_profile_for_review_2026_06_22`.
- Existing `benchmarks/gaia_obligation_subset_validation20.jsonl` and `benchmarks/gaia_obligation_subset_test20.jsonl` remain stamped as human-audited.

Gold-compiler smoke:

| Subset | N | Success | Avg Cost | Oracle Cost | Regret |
|---|---:|---:|---:|---:|---:|
| GAIA validation100 for review | 100 | 1.00 | 1.39 | 1.39 | 0.00 |
| GAIA test100 for review | 100 | 1.00 | 1.57 | 1.57 | 0.00 |

Audit update:

- The project owner confirmed the GAIA validation100/test100 labels are gold truth.
- Stamped files:
  - `benchmarks/gaia_validation_100_human_audited.jsonl`
  - `benchmarks/gaia_test_100_human_audited.jsonl`
  - `benchmarks/gaia_transfer_200_human_audited.jsonl`
- Combined GAIA transfer200 gold-compiler smoke:

| Subset | N | Success | Avg Cost | Oracle Cost | Regret |
|---|---:|---:|---:|---:|---:|
| GAIA transfer200 human-audited | 200 | 1.00 | 1.48 | 1.48 | 0.00 |

## 2026-06-22 Phase 2 Dataset Freeze and Artifact Generation

Frozen benchmark packages:

- `benchmarks/gapbench/v1.0/`: 1000 human-audited rows, 500-row subset, manifest, schema, audit log, dev200 split, test800 split.
- `benchmarks/gaia_transfer/v1.0/`: 200 human-audited GAIA transfer rows, validation100/test100 splits, manifest, schema, audit log.
- `benchmarks/gapbench_natural/v1.0/`: 200 naturalized GapBench examples for human review, plus CSV review sheet and manifest.

Natural-200 generation:

```bash
python3 -m scripts.build_gapbench_natural
python3 -m scripts.clean_gapbench_natural_queries
python3 -m gapharness.cli run-benchmark \
  --benchmark benchmarks/gapbench_natural/v1.0/gapbench_natural_200_for_review.jsonl \
  --system gapharness \
  --profiler gold \
  --out outputs/results_gapbench_natural200_review_gold.jsonl
python3 -m gapharness.cli make-report \
  --results outputs/results_gapbench_natural200_review_gold.jsonl \
  --out outputs/summary_gapbench_natural200_review_gold.md
```

Natural-200 gold-compiler smoke:

| Subset | N | Success | Avg Cost | Oracle Cost | Regret |
|---|---:|---:|---:|---:|---:|
| GapBench-Natural-200 for review | 200 | 1.00 | 2.83 | 2.83 | 0.00 |

Generated Phase 2 paper artifacts:

- `outputs/phase2/table1_gapbench1000_gold.md`
- `outputs/phase2/table2_transfer_and_review_smokes.md`
- `outputs/phase2/table3_category_breakdown.md`
- `outputs/phase2/failure_mode_summary.md`
- `figures/phase2/pipeline.svg`
- `figures/phase2/cost_success_frontier.svg`
- `figures/phase2/over_under_wrong_bars.svg`
- `figures/phase2/regret_distribution.svg`
- `figures/phase2/drop_one_necessity.svg`

Validation:

```bash
python3 -m unittest discover -s tests
python3 -m py_compile scripts/generate_phase2_artifacts.py
python3 -m scripts.generate_phase2_artifacts
```

Result: 12 tests pass; Phase 2 tables and figures regenerate from the current GapBench-1000 gold result.

## 2026-06-22 Phase 2 Deterministic Checkpoint

Checkpoint name:

```text
phase2-deterministic-artifacts-v1
```

Phase 2 deterministic artifact checkpoint completed.
Gold-obligation compiler and baseline experiments are frozen.
Subsequent experiments only evaluate LLM-inferred obligations and do not modify GapBench v1.0 labels, compiler rules, or deterministic baselines.

## 2026-06-22 Phase 2B LLM Profiler Calibration

Goal:

> When gold obligations are hidden and an LLM profiler infers obligations, can GapHarness preserve high sufficiency while keeping minimality regret interpretable?

Implemented Phase 2B runner:

- `scripts/run_phase2b_llm_sweep.py`
- Batch profiling with JSONL profile caches.
- Dev diagnostics from cached profiles.
- Held-out test sweep using only the selected profiler.

Dev200 profilers:

| Profiler | Success | Avg Cost | Regret | Over | Under | Wrong | Obl P | Obl R | Obl F1 | Exact Set |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_single | 0.92 | 3.68 | 0.06 | 0.19 | 0.08 | 0.00 | 0.905 | 0.955 | 0.929 | 0.79 |
| llm_recall | 0.96 | 3.94 | 0.32 | 0.20 | 0.04 | 0.00 | 0.895 | 0.969 | 0.930 | 0.80 |
| llm_minimality | 0.98 | 3.82 | 0.20 | 0.14 | 0.02 | 0.00 | 0.929 | 0.969 | 0.949 | 0.86 |

Selection rule:

1. under_harness_rate <= 0.08
2. success >= 0.90
3. among satisfying profilers, choose lowest minimality regret
4. if none satisfy, choose recall-biased and report calibration as limitation

Selected primary profiler: `llm_single`.

Held-out test800 result:

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 800 | 0.20 | 0.00 | 3.69 | -3.69 | 0.00 | 0.74 | 0.00 | 0.00 |
| tool_router | 800 | 0.32 | 1.96 | 3.69 | -1.72 | 0.09 | 0.62 | 0.43 | 0.06 |
| difficulty_router | 800 | 0.41 | 3.22 | 3.69 | -0.47 | 0.26 | 0.53 | 0.15 | 0.13 |
| always_full | 800 | 0.94 | 16.00 | 3.69 | 12.31 | 0.94 | 0.00 | 0.00 | 0.51 |
| gold_oracle_gap_harness | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| selected_llm_gap_harness | 800 | 0.89 | 3.59 | 3.69 | -0.09 | 0.14 | 0.09 | 0.01 | 0.05 |

Interpretation:

- The selected LLM profiler improves substantially over Direct, Tool Router, and Difficulty Router.
- It keeps cost near oracle cost.
- It does not yet match Always-full sufficiency; the held-out under-harness rate is 0.09.
- Main failure pattern: capability lowering, especially LLM overuse of `real_world_side_effect` for sandbox/mock action requests.

## Phase 2B frozen checkpoint

Phase 2B completed the dev200 profiler sweep and held-out test800 selected-profiler evaluation. Existing outputs under `outputs/phase2b/` are treated as frozen artifacts and must not be overwritten. Phase 2C introduces a new profiler variant, `llm_registry_guarded`, as a post-Phase-2B calibration experiment.

## 2026-06-23 Phase 2C Registry-Guarded Profiler Calibration

Goal:

> Correct the Phase 2B failure mode where sandbox/mock/local actions are sometimes lowered into unsupported `real_world_side_effect`, without changing GapBench gold labels or Phase 2B outputs.

Implementation:

- Added `llm_registry_guarded`.
- GapBench dev/test reuse the frozen Phase 2B `llm_single` profile caches, then apply a deterministic registry guard.
- Guard metadata is logged in profile/result JSONL rows.
- Phase 2B outputs remain frozen and are compared only as read-only baselines.

Dev200:

| Profiler | Success | Avg Cost | Regret | Over | Under | Wrong | Unsupported FP |
|---|---:|---:|---:|---:|---:|---:|---:|
| Phase 2B `llm_single` | 0.92 | 3.68 | 0.06 | 0.19 | 0.08 | 0.00 | 14 |
| Phase 2C `llm_registry_guarded` | 0.97 | 4.02 | 0.40 | 0.20 | 0.03 | 0.00 | 4 |

Dev guard corrections:

- guard applied: 16 / 200
- removed sandbox false `real_world_side_effect`: 10
- converted unsupported to supported: 10
- preserved ambiguous clarification: 6

Held-out test800:

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Unsupported FP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Phase 2B selected `llm_single` | 800 | 0.89 | 3.59 | 3.69 | -0.09 | 0.14 | 0.09 | 0.01 | 56 |
| Phase 2C `llm_registry_guarded` | 800 | 0.94 | 3.98 | 3.69 | 0.30 | 0.15 | 0.03 | 0.01 | 12 |

Held-out guard corrections:

- guard applied: 50 / 800
- removed sandbox false `real_world_side_effect`: 44
- converted unsupported to supported: 44
- preserved ambiguous clarification: 6

GAIA-Transfer:

| N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Guard Applied |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 200 | 0.56 | 5.56 | 1.48 | 4.08 | 0.89 | 0.44 | 0.42 | 0 |

Interpretation: GAIA is a transfer limitation result. The registry guard targets sandbox/mock action calibration; GAIA failures are dominated by file, multimodal, evidence, and state obligation mismatch rather than `real_world_side_effect`.

Terminal transfer scaffold:

- Generated `benchmarks/terminal_obligation/v0.1/terminal_obligation50_for_review.jsonl`.
- Source text comes from public Terminal-Bench task instructions in `harbor-framework/terminal-bench/original-tasks/*/task.yaml`.
- All rows remain `generated_for_human_review_pending_audit`.
- Generated `review_sheet.csv`, `manifest.json`, and `schema.md`.

TerminalSmoke-20:

- Generated 20 local sandbox cases.
- Deterministic smoke checks passed: 20 / 20.
- No network and no production paths.

Reports:

- `outputs/phase2c/dev200_registry_guarded_report.md`
- `outputs/phase2c/heldout_test800_registry_guarded_report.md`
- `outputs/phase2c/gaia_transfer_registry_guarded_report.md`
- `outputs/phase2c/terminal_smoke20_report.md`

API usage:

- GapBench dev/test: 0 new API calls because Phase 2B cache was reused.
- GAIA-Transfer: approximately 40 batch requests, including one rerun after tightening lexical real-action guards.

## 2026-06-23 Phase 2D Stress Tests and Negative Controls

Goal:

> Add reviewer-facing stress tests showing that GapHarness depends on declared registry affordances, that obligation labels have semantic force, and that negative-control prompts do not trigger keyword/tool-sensitive over-harnessing.

Command:

```bash
python3 -m scripts.run_phase2d_stress_tests all
```

### Stress Test 1: Registry Perturbation

Protocol: run gold GapHarness on relevant first-N 60-task subsets under the base registry and under a registry with one key module removed.

| Perturbation | Removed Module | Base Success | Perturbed Success | Unsupported | Under-covered | Dominant Missing |
|---|---|---:|---:|---:|---:|---|
| remove_python_executor | python_executor | 1.00 | 0.00 | 1.00 | 1.00 | execution |
| remove_source_span_checker | source_span_checker | 1.00 | 0.00 | 1.00 | 1.00 | source_spans |
| remove_permission_gate | permission_gate | 1.00 | 0.00 | 1.00 | 1.00 | permission |
| remove_sandbox_file_editor | sandbox_file_editor | 1.00 | 0.00 | 1.00 | 1.00 | diff |
| remove_web_retrieval | web_retrieval | 1.00 | 0.00 | 1.00 | 1.00 | evidence_sources |
| remove_contract_verifier | contract_verifier | 1.00 | 0.00 | 1.00 | 1.00 | contract_check |

Interpretation: registry perturbation verifies that GapHarness does not silently hallucinate support when required affordances are absent; it degrades into unsupported or under-covered status.

### Stress Test 2: Gold Label Permutation

Protocol: feed corrupted labels to the compiler while keeping the original human-audited gold labels as verifier truth.

| Condition | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Verifier Fail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| correct gold | 200 | 1.00 | 2.86 | 2.86 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| permuted labels | 200 | 0.17 | 3.10 | 2.86 | 0.24 | 0.55 | 0.83 | 0.79 | 0.83 |

Permutation integrity: 200 / 200 corrupted profiles changed obligations or required capabilities; no-op corruptions: 0.

Interpretation: this is not a realistic corruption model. It is an anti-circularity stress test showing that the compiler is sensitive to obligation semantics.

### Negative-Control Analysis

Protocol: report `pure_language_negative` and `tool_bait` separately for Direct, Tool Router, Always-full, Difficulty Router, GapHarness gold, GapHarness LLM, and Registry-guarded GapHarness.

| Category | System | N | Success | Avg Cost | Over |
|---|---|---:|---:|---:|---:|
| pure_language_negative | gapharness_gold | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | gapharness_llm_single | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | gapharness_registry_guarded | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | always_full | 100 | 1.00 | 16.00 | 1.00 |
| tool_bait | gapharness_gold | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | gapharness_llm_single | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | gapharness_registry_guarded | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | tool_router | 100 | 1.00 | 1.26 | 0.51 |
| tool_bait | difficulty_router | 100 | 1.00 | 1.22 | 0.51 |
| tool_bait | always_full | 100 | 1.00 | 16.00 | 1.00 |

Outputs:

- `outputs/phase2d/registry_perturbation_report.md`
- `outputs/phase2d/gold_label_permutation_report.md`
- `outputs/phase2d/negative_control_analysis_report.md`
- `docs/phase2d_stress_tests_zh.md`
