# Appendix: Reproducibility

This appendix describes how to reproduce the paper-facing artifacts without changing frozen result files. The final frozen copies live under `outputs/final/`, `paper/tables/`, `paper/figures/`, and `paper/appendix/`.

## Environment Assumptions

The repository is a Python package with dev dependencies declared in `pyproject.toml`. The supported interpreter is **Python 3.9** (pinned in `.python-version`; `requires-python = ">=3.9"`). A minimal local setup is:

```bash
python3 -m venv .venv       # python3 is 3.9.x; see .python-version
source .venv/bin/activate
pip install -e ".[dev]"
```

`pyproject.toml` declares a setuptools `[build-system]`, so `pip install -e ".[dev]"`
installs the package as `gapharness` (not `UNKNOWN-0.0.0`) and exposes the
`gapharness` console script, which maps to `gapharness.cli:main`. You can confirm
the install with:

```bash
gapharness --help                         # console script entry point
python3 -c "import importlib.metadata as m; print(m.version('gapharness'))"  # -> 0.1.0
```

The paper package was finalized on macOS with Python 3.9, `pytest`, `pandoc`, and `tectonic` available. PDF validation can use Poppler tools such as `pdfinfo` and `pdftoppm` when installed.

## Unit Tests

```bash
python3 -m pytest
# or, matching the CI/harness invocation:
python3 -m unittest discover -s tests
```

Expected current result: all unit tests pass.

## How to Verify (quick repro self-check)

A static, side-effect-free self-check confirms the reproducibility invariants
without running any experiment or touching committed artifacts:

```bash
bash scripts/check_repro.sh
```

It verifies that:

1. every benchmark input referenced by `scripts/run_phase2_gold_experiments.sh`
   exists on disk (and the stale `gapbench_natural_200_for_review.jsonl`
   reference is gone);
2. `scripts/freeze_phase2_datasets.py` writes JSON with `ensure_ascii=False`
   so a freeze re-run preserves committed UTF-8 bytes/checksums;
3. `pyproject.toml` declares a `[build-system]`, the package name `gapharness`,
   and the `gapharness -> gapharness.cli:main` console script;
4. `requires-python`, `.python-version`, and the running interpreter all agree
   on Python 3.9.

A successful run prints `ALL REPRO CHECKS PASSED` and exits `0`. The same
invariants are also asserted by `tests/test_reproducibility.py`.

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

The paper tables are stored in `paper/tables/`. Their sources are frozen in:

- `outputs/final/results_gapbench1000_all_gold.jsonl`
- `outputs/final/phase2b/results_test800_heldout_with_selected_llm.jsonl`
- `outputs/final/phase2c/test800_registry_guarded/results_test800_llm_registry_guarded.jsonl`
- `outputs/final/phase2d/`
- `outputs/final/results_gaia_transfer200_human_audited_gold.jsonl`
- `outputs/final/results_gapbench_natural200_human_audited_gold.jsonl`
- `outputs/final/results_swe_obligation50_human_audited_gold.jsonl`
- `outputs/final/swe_obligation50_diagnostic_summary.md`
- `outputs/final/harness_exec50/traces.jsonl`
- `outputs/phase5_agentic_baselines/`
- `outputs/phase6_reviewer_evidence/`

If table regeneration is needed, regenerate from frozen outputs only; do not rerun LLM calls just to rebuild formatting.

## Regenerating Figures from Frozen Outputs

Final figures are stored in `paper/figures/` and copied from `figures/final/`. If a figure file is missing, regenerate it only from frozen results or from the existing deterministic figure generator; do not add new experiments.

## Frozen Benchmark Source Copies

Benchmark source copies used by the paper are frozen in:

- `outputs/final/benchmark_sources/gapbench_1000_human_audited.jsonl`
- `outputs/final/benchmark_sources/gaia_transfer200_human_audited.jsonl`
- `outputs/final/benchmark_sources/gapbench_natural_200_human_audited.jsonl`
- `outputs/final/benchmark_sources/swe_obligation50_human_audited.jsonl`
- `outputs/final/benchmark_sources/swe_obligation50_llm_safe_view.jsonl`
- `outputs/final/benchmark_sources/terminal_obligation50_for_review.jsonl`
- `benchmarks/harness_exec/v1.1/swe_harness_exec50_cases.jsonl`
- `benchmarks/realboundary/v0.1/realboundary100_author_seeded.jsonl`
- `benchmarks/naturalistic_holdout/v0.1/naturalistic_holdout_v0.1_candidates.jsonl`

Naturalistic-Holdout v0.1 is a candidate review package, not a scored gold benchmark. It should not be used for paper scores until two independent annotators complete the review sheet, agreement metrics are reported, and disagreements are adjudicated.

## Deterministic Gold Experiments

The provided-patch executable trace scale-up can be regenerated without API calls:

```bash
PYTHONPATH=. python3 scripts/run_harness_exec20.py --suite-size 50 --benchmark-dir benchmarks/harness_exec/v1.1 --out-dir outputs/final/harness_exec50 --audit-date 2026-06-23
```

The deterministic gold experiments can be rerun with:

```bash
bash scripts/run_phase2_gold_experiments.sh
```

This script reads only committed `*_human_audited.jsonl` benchmark inputs:

- `benchmarks/gapbench/v1.0/gapbench_1000_human_audited.jsonl`
- `benchmarks/gaia_transfer/v1.0/gaia_transfer200_human_audited.jsonl`
- `benchmarks/gapbench_natural/v1.0/gapbench_natural_200_human_audited.jsonl`

Primary deterministic outputs:

- `outputs/results_gapbench1000_all_gold.jsonl`
- `outputs/summary_gapbench1000_all_gold.md`
- `outputs/results_gaia_transfer200_human_audited_gold.jsonl`
- `outputs/results_gapbench_natural200_human_audited_gold.jsonl`
- `outputs/phase2/`
- `figures/phase2/`

The first step of the script, `python3 -m scripts.freeze_phase2_datasets`, writes
all JSONL/JSON with `ensure_ascii=False`. This preserves raw UTF-8 bytes (for
example the U+2019 right single quotation mark in GAIA queries), so a freeze
re-run reproduces the committed files byte-for-byte and the GAIA checksums stay
valid instead of diverging to `\uXXXX` escapes.

## LLM Profiler Experiments

LLM profiler sweeps require API credentials and should pass keys only through environment variables. Do not write API keys to repository files, command history intended for sharing, or paper artifacts.

```bash
python3 -m scripts.run_phase2b_llm_sweep dev
python3 -m scripts.run_phase2b_llm_sweep test
```

These commands can consume API budget. They should not be run by default when validating the final paper package, because frozen LLM outputs already exist under `outputs/final/phase2b/` and `outputs/final/phase2c/`.

## Registry-Guarded Calibration

GapBench dev/test registry-guarded runs reuse frozen base-profiler caches where available and apply deterministic registry guarding:

```bash
python3 -m scripts.run_phase2b_llm_sweep phase2c-dev
python3 -m scripts.run_phase2b_llm_sweep phase2c-test
python3 -m scripts.run_phase2b_llm_sweep phase2c-gaia
python3 -m scripts.run_phase2b_llm_sweep terminal-scaffold
python3 -m scripts.run_phase2b_llm_sweep terminal-smoke20
```

The GAIA registry-guarded output is a limitation result, not a full GAIA solving result.

## Stress Tests

Stress tests are deterministic over existing benchmark labels:

```bash
python3 -m scripts.run_phase2d_stress_tests all
```

Main outputs:

- `outputs/phase2d/registry_perturbation_report.md`
- `outputs/phase2d/gold_label_permutation_report.md`
- `outputs/phase2d/negative_control_analysis_report.md`

## Phase 6 Reviewer-Evidence Replay

Phase 6 reviewer-hardening evidence is deterministic over existing routes, profiles, and registry declarations:

```bash
PYTHONPATH=. python3 scripts/run_phase6_reviewer_evidence.py all
```

Main outputs:

- `outputs/phase6_reviewer_evidence/certificate_utility/certificate_utility_report.md`
- `outputs/phase6_reviewer_evidence/certificate_utility/certificate_audit_packet_review_sheet.csv`
- `outputs/phase6_reviewer_evidence/feedback_levels/feedback_level_report.md`
- `outputs/phase6_reviewer_evidence/cost_calibration/cost_calibration_report.md`
- `outputs/phase6_reviewer_evidence/status_confusion/status_confusion_report.md`
- `outputs/phase6_reviewer_evidence/profiler_error_taxonomy/profiler_error_taxonomy_report.md`
- `outputs/phase6_reviewer_evidence/realboundary100/realboundary100_report.md`

Certificate utility outputs are deterministic proxies plus an audit packet; they do not report completed human timing. Feedback-level replay is not a fresh LLM run.

## Secret Scan Before Release

Run a broad local scan before sharing artifacts:

```bash
rg -n "sk-|hf_|api[_-]?key|token|secret" .
```

Also run the project-specific fragment scan used during finalization. Do not print or store real secrets in reports.

## What Not To Run By Default

Do not rerun LLM profiler sweeps, GAIA transfer profiling, or any API-backed experiment unless intentionally refreshing frozen results. The final package is designed to validate from frozen outputs, unit tests, checksums, and static paper artifacts.
