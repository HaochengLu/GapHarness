# Artifact Index

This repository is organized as a paper artifact rather than a demo-only code dump.

## Manuscript

- PDF: `paper/submission/arxiv_package/gapharness_arxiv.pdf`
- Markdown source: `paper/submission/arxiv_package/gapharness_manuscript_v2.md`
- LaTeX source: `paper/submission/arxiv_package/gapharness_manuscript_v2.tex`
- Bibliography: `paper/submission/arxiv_package/references.bib`
- Tables: `paper/submission/arxiv_package/tables/`
- Figures: `paper/submission/arxiv_package/figures/`

## Code

- Core package: `gapharness/`
- Experiment scripts: `scripts/`
- Tests: `tests/`
- Python metadata: `pyproject.toml`

## Benchmarks

- `benchmarks/gapbench/v1.0/`
- `benchmarks/gaia_transfer/v1.0/`
- `benchmarks/gapbench_natural/v1.0/`
- `benchmarks/harness_challenge/v1.0/`
- `benchmarks/harness_exec/v1.0/`
- `benchmarks/harness_exec/v1.1/`
- `benchmarks/naturalistic_holdout/v0.1/`
- `benchmarks/realboundary/v0.1/`
- `benchmarks/swe_obligation/v1.0/`
- `benchmarks/terminal_obligation/v0.1/`

Each benchmark directory includes a manifest or README documenting provenance, scope, and audit status.

## Results

- Final checksums: `outputs/final/checksums.sha256`
- Benchmark source mirrors: `outputs/final/benchmark_sources/`
- Reviewer-hardening outputs: `outputs/phase4/`
- Compiler scaling and replay: `outputs/final/compiler_scaling/`, `outputs/final/compiler_equivalence/`
- Stress tests: `outputs/final/phase2d/`
- Agentic baselines: `outputs/phase5_agentic_baselines/`
- Reviewer evidence: `outputs/phase6_reviewer_evidence/`
- Executable traces: `outputs/final/harness_exec20/`, `outputs/final/harness_exec50/`

## Integrity Checks

```bash
shasum -a 256 -c --strict outputs/final/checksums.sha256
shasum -a 256 -c --strict paper/submission/arxiv_package/checksums.sha256
```
