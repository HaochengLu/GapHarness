#!/usr/bin/env bash
set -euo pipefail

python3 -m scripts.freeze_phase2_datasets

python3 -m gapharness.cli run-benchmark \
  --benchmark benchmarks/gapbench/v1.0/gapbench_1000_human_audited.jsonl \
  --system all \
  --profiler gold \
  --out outputs/results_gapbench1000_all_gold.jsonl

python3 -m gapharness.cli make-report \
  --results outputs/results_gapbench1000_all_gold.jsonl \
  --out outputs/summary_gapbench1000_all_gold.md

python3 -m gapharness.cli run-benchmark \
  --benchmark benchmarks/gaia_transfer/v1.0/gaia_transfer200_human_audited.jsonl \
  --system gapharness \
  --profiler gold \
  --out outputs/results_gaia_transfer200_human_audited_gold.jsonl

python3 -m gapharness.cli make-report \
  --results outputs/results_gaia_transfer200_human_audited_gold.jsonl \
  --out outputs/summary_gaia_transfer200_human_audited_gold.md

python3 -m gapharness.cli run-benchmark \
  --benchmark benchmarks/gapbench_natural/v1.0/gapbench_natural_200_human_audited.jsonl \
  --system gapharness \
  --profiler gold \
  --out outputs/results_gapbench_natural200_human_audited_gold.jsonl

python3 -m gapharness.cli make-report \
  --results outputs/results_gapbench_natural200_human_audited_gold.jsonl \
  --out outputs/summary_gapbench_natural200_human_audited_gold.md

python3 -m scripts.generate_phase2_artifacts
python3 -m unittest discover -s tests
