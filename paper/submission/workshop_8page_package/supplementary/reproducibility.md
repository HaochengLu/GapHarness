# Appendix: Reproducibility

This appendix describes how to reproduce the paper-facing artifacts without changing frozen result files. The final frozen copies live under `outputs/final/`, `paper/tables/`, `paper/figures/`, and `paper/appendix/`.

## Environment Assumptions

The repository is a Python package with dev dependencies declared in `pyproject.toml`. A minimal local setup is:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The paper package was finalized on macOS with Python 3.9, `pytest`, `pandoc`, and `tectonic` available. PDF validation can use Poppler tools such as `pdfinfo` and `pdftoppm` when installed.

## Unit Tests

```bash
python3 -m pytest
```

Expected current result: all unit tests pass.

## Checksum Verification

Paper-facing frozen artifacts are checksummed in:

```text
outputs/final/checksums.sha256
```

Verify them with:

```bash
shasum -a 256 -c outputs/final/checksums.sha256
```

## Regenerating Paper Tables from Frozen Outputs

The five main paper tables are stored in `paper/tables/`. Their sources are frozen in:

- `outputs/final/results_gapbench1000_all_gold.jsonl`
- `outputs/final/phase2b/results_test800_heldout_with_selected_llm.jsonl`
- `outputs/final/phase2c/test800_registry_guarded/results_test800_llm_registry_guarded.jsonl`
- `outputs/final/phase2d/`
- `outputs/final/results_gaia_transfer200_human_audited_gold.jsonl`
- `outputs/final/results_gapbench_natural200_human_audited_gold.jsonl`

If table regeneration is needed, regenerate from frozen outputs only; do not rerun LLM calls just to rebuild formatting.

## Regenerating Figures from Frozen Outputs

Final figures are stored in `paper/figures/` and copied from `figures/final/`. If a figure file is missing, regenerate it only from frozen results or from the existing deterministic figure generator; do not add new experiments.

## Frozen Benchmark Source Copies

Benchmark source copies used by the paper are frozen in:

- `outputs/final/benchmark_sources/gapbench_1000_human_audited.jsonl`
- `outputs/final/benchmark_sources/gaia_transfer200_human_audited.jsonl`
- `outputs/final/benchmark_sources/gapbench_natural_200_human_audited.jsonl`
- `outputs/final/benchmark_sources/terminal_obligation50_for_review.jsonl`

## Deterministic Gold Experiments

The deterministic gold experiments can be rerun with:

```bash
bash scripts/run_phase2_gold_experiments.sh
```

Primary deterministic outputs:

- `outputs/results_gapbench1000_all_gold.jsonl`
- `outputs/summary_gapbench1000_all_gold.md`
- `outputs/phase2/`
- `figures/phase2/`

## LLM Profiler Experiments

LLM profiler sweeps require API credentials and should pass keys only through environment variables. Do not write API keys to repository files, command history intended for sharing, or paper artifacts.

```bash
python3 -m scripts.run_phase2b_llm_sweep dev
python3 -m scripts.run_phase2b_llm_sweep test
```

These commands can consume API budget. They should not be run by default when validating the final paper package, because frozen LLM outputs already exist under `outputs/final/phase2b/` and `outputs/final/phase2c/`.

## Registry-Guarded Calibration

GapBench dev/test registry-guarded runs reuse frozen Phase 2B profiler caches where available and apply deterministic registry guarding:

```bash
python3 -m scripts.run_phase2b_llm_sweep phase2c-dev
python3 -m scripts.run_phase2b_llm_sweep phase2c-test
python3 -m scripts.run_phase2b_llm_sweep phase2c-gaia
python3 -m scripts.run_phase2b_llm_sweep terminal-scaffold
python3 -m scripts.run_phase2b_llm_sweep terminal-smoke20
```

The GAIA registry-guarded output is a limitation result, not a full GAIA solving result.

## Stress Tests

Phase 2D stress tests are deterministic over existing benchmark labels:

```bash
python3 -m scripts.run_phase2d_stress_tests all
```

Main outputs:

- `outputs/phase2d/registry_perturbation_report.md`
- `outputs/phase2d/gold_label_permutation_report.md`
- `outputs/phase2d/negative_control_analysis_report.md`

## Secret Scan Before Release

Run a broad local scan before sharing artifacts:

```bash
rg -n "sk-|hf_|api[_-]?key|token|secret" .
```

Also run the project-specific fragment scan used during finalization. Do not print or store real secrets in reports.

## What Not To Run By Default

Do not rerun LLM profiler sweeps, GAIA transfer profiling, or any API-backed experiment unless intentionally refreshing frozen results. The final package is designed to validate from frozen outputs, unit tests, checksums, and static paper artifacts.
