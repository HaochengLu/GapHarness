# Artifact Checklist

## Benchmark Files

- GapBench-1000 frozen source: `outputs/final/benchmark_sources/gapbench_1000_human_audited.jsonl`
- GAIA-Transfer-200 frozen source: `outputs/final/benchmark_sources/gaia_transfer200_human_audited.jsonl`
- GapBench-Natural-200 project-owner-audited source: `outputs/final/benchmark_sources/gapbench_natural_200_human_audited.jsonl`
- Terminal-Bench-obligation50 frozen source: `outputs/final/benchmark_sources/terminal_obligation50_for_review.jsonl`

## Output Result Files

- GapBench-1000 gold result: `outputs/final/results_gapbench1000_all_gold.jsonl`
- GAIA-Transfer gold smoke result: `outputs/final/results_gaia_transfer200_human_audited_gold.jsonl`
- GapBench-Natural project-owner-audited result result: `outputs/final/results_gapbench_natural200_human_audited_gold.jsonl`
- Phase 2B LLM profiler outputs: `outputs/final/phase2b/`
- Phase 2C registry-guarded outputs: `outputs/final/phase2c/`
- Phase 2D stress-test outputs: `outputs/final/phase2d/`

## Figures

- Main figures: `paper/figures/figure1_pipeline.svg` through `paper/figures/figure4_registry_guard_unsupported_fp_reduction.svg`
- Frozen figure copies: `figures/final/`

## Tables

- Main tables: `paper/tables/table1_gapbench1000_gold.md` through `paper/tables/table5_transfer_boundary.md`
- Table index: `paper/tables/final_table_index.md`

## Scripts

- Gold deterministic run: `scripts/run_phase2_gold_experiments.sh`
- Phase 2B / 2C profiler sweeps: `scripts/run_phase2b_llm_sweep.py`
- Phase 2D stress tests: `scripts/run_phase2d_stress_tests.py`
- Phase 2 artifact generation: `scripts/generate_phase2_artifacts.py`
- Dataset freeze helpers: `scripts/freeze_phase2_datasets.py`

## Test Commands

```bash
python3 -m pytest
python3 -m py_compile scripts/*.py
shasum -a 256 -c outputs/final/checksums.sha256
```

## Checksum File

- `outputs/final/checksums.sha256`

## Secret Scan Statement

Before sharing or submission, run a broad secret scan and the project-specific secret-fragment scan. No API keys, Hugging Face tokens, or private credentials should appear in manuscript, tables, figures, appendix files, submission packages, or checksums.

## Known Limitations

- GapHarness does not claim full GAIA solving.
- GapHarness does not claim Terminal-Bench solving.
- The executor is a deterministic sandbox/mock runtime and does not perform irreversible external actions.
- GapBench-1000 is controlled and factorial, not a complete open-world benchmark.
- The LLM profiler is not fully calibrated.
- Minimality is relative to the declared obligation ontology, module registry, dependency model, and cost function.

