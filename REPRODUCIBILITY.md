# Reproducibility Guide

## Environment

Use Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Smoke Test

```bash
pytest
python -m py_compile gapharness/*.py scripts/*.py
```

## Deterministic Seed Benchmark

```bash
python -m scripts.build_seed_benchmark --out benchmarks/gapbench_factorial_seed.jsonl
python -m gapharness.cli run-benchmark \
  --benchmark benchmarks/gapbench_factorial_seed.jsonl \
  --system all \
  --profiler gold \
  --out outputs/results_seed_gold.jsonl
python -m gapharness.cli make-report \
  --results outputs/results_seed_gold.jsonl \
  --out outputs/summary_seed_gold.md
```

## Final Artifact Verification

```bash
shasum -a 256 -c --strict outputs/final/checksums.sha256
shasum -a 256 -c --strict paper/submission/arxiv_package/checksums.sha256
```

## Deterministic Experiment Families

```bash
python -m scripts.run_phase2d_stress_tests all
python -m scripts.run_compiler_equivalence_replay
python -m scripts.run_compiler_scaling
python -m scripts.run_phase5_agentic_baselines
python -m scripts.run_phase6_reviewer_evidence
```

Some scripts may rewrite files under `outputs/`. Run them on a clean branch if you want to compare regenerated artifacts against the committed release.

## LLM Profiler Experiments

LLM-based profiler sweeps require an OpenAI-compatible API. Configure it only through environment variables:

```bash
export GAPHARNESS_API_KEY="..."
export GAPHARNESS_BASE_URL="..."
export GAPHARNESS_MODEL="..."
```

Example:

```bash
python -m scripts.run_phase2b_llm_sweep dev
python -m scripts.run_phase2b_llm_sweep test
```

The committed repository does not include API keys or provider-private endpoints.

