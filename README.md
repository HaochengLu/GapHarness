# GapHarness

GapHarness is a research system for **Certificate-Carrying Runtime Harness Compilation** for API-only LLM agents.

Given an obligation profile and a finite registry of modules with declared affordances and design-time costs, GapHarness compiles the lowest declared-cost module subset that satisfies the required obligations, capabilities, and dependencies, or explicitly returns unsupported. The compiler is exact within the declared registry and emits certificate-carrying outputs that expose coverage, dependency satisfaction, missing affordances, and registry-relative minimality evidence. Obligation inference is separated from certified, registry-constrained support selection so the two questions can be audited independently.

The project treats an agent harness as a runtime system that covers external obligations a stateless LLM cannot satisfy by itself:

- Observation
- Execution
- State
- Action
- Control
- Verification

The first milestone is not a flashy demo. It is a small, reproducible system that can support a technical report or workshop paper:

- runnable compiler and executor
- synthetic gold benchmark seed
- baseline comparisons
- counterfactual drop-one ablation
- Markdown report generation

## Phase 2 Status

The current workspace has moved from MVP demo to a paper-ready experiment package.

- `benchmarks/gapbench/v1.0/`: frozen 1000-row GapBench v1.0, with manifest, schema, audit log, and dev200/test800 splits.
- `benchmarks/gaia_transfer/v1.0/`: frozen 200-row GAIA transfer set, with 100 validation and 100 test examples carrying single-annotator (project-owner) labels; inter-annotator agreement is reported on an independent subset.
- `benchmarks/gapbench_natural/v1.0/`: 200 naturalized GapBench examples for human review. Labels are inherited from audited GapBench v1.0, but the naturalized user queries should be reviewed before final paper claims.
- `outputs/phase2/`: paper tables derived from the GapBench-1000 gold run.
- `figures/phase2/`: lightweight SVG figures for the technical report.
- `outputs/phase2b/`: LLM profiler dev200 calibration, selected-profiler held-out test800 sweep, diagnostic tables, and cached LLM profiles.
- `outputs/phase2c/`: registry-guarded profiler calibration, held-out test800 report, GAIA transfer stress result, and Terminal-Bench-obligation50 traces.
- `outputs/phase2d/`: registry perturbation, gold-label permutation, and pure/tool-bait negative-control stress tests.
- `benchmarks/terminal_obligation/v0.1/`: Terminal-Bench instruction-derived obligation50 scaffold for human review.

## Current Paper Package

The current final technical-report package is under `paper/submission/arxiv_package/`.

- GapHarness-Repair adds verifier-guided profile patching and recompilation while preserving compiler certificates.
- Strong strategy baselines include Workflow Generator, Verifier-Repair Router, and ReAct-style Module Selector over the same declared registry/executor/verifier.
- `benchmarks/harness_exec/v1.1/` and `outputs/final/harness_exec50/` contain SWE-HarnessExec-50, a provided-patch sandbox pytest trace scale-up. It is not SWE-bench pass@1, real-repository checkout, or model-generated repair.

## Quickstart

The code path is intentionally standard-library only for the MVP, so it can run before Python 3.12 and `uv` are installed.

```bash
python3 -m scripts.build_seed_benchmark --out benchmarks/gapbench_factorial_seed.jsonl
python3 -m gapharness.cli run-benchmark --benchmark benchmarks/gapbench_factorial_seed.jsonl --system all --profiler gold --out outputs/results_gold.jsonl
python3 -m gapharness.cli make-report --results outputs/results_gold.jsonl --out outputs/summary_gold.md
python3 -m unittest discover -s tests
```

To reproduce the current Phase 2 deterministic gold artifacts:

```bash
bash scripts/run_phase2_gold_experiments.sh
```

Phase 2B LLM profiler calibration and held-out sweep:

```bash
python3 -m scripts.run_phase2b_llm_sweep dev
python3 -m scripts.run_phase2b_llm_sweep test
```

The Phase 2B commands require `GAPHARNESS_API_KEY`, `GAPHARNESS_BASE_URL`, and `GAPHARNESS_MODEL` in the runtime environment.

Phase 2C registry-guarded calibration:

```bash
python3 -m scripts.run_phase2b_llm_sweep phase2c-dev
python3 -m scripts.run_phase2b_llm_sweep phase2c-test
python3 -m scripts.run_phase2b_llm_sweep phase2c-gaia
```

Phase 2D stress tests and negative controls:

```bash
python3 -m scripts.run_phase2d_stress_tests all
```

For the paper-ready environment, use Python 3.10+ and install optional dev dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## MVP Scope

The current executor is a deterministic sandbox/mock runtime. It does not perform irreversible file edits, real API calls, emails, or deployments. This is deliberate: the first technical report should validate the obligation profiler/compiler/verifier logic before broadening the external action surface.

## Repository Layout

```text
gapharness/
  schema.py          typed data model
  registry.py        module affordance registry
  profiler.py        gold and heuristic obligation profilers
  compiler.py        exact minimal harness compiler
  executor.py        deterministic sandbox/mock executor
  verifiers.py       sufficiency and minimality checks
  baselines.py       direct/tool-router/full/difficulty/oracle systems
  evaluation.py      benchmark runner and metrics
  seed_data.py       100-task synthetic seed benchmark generator
  cli.py             command-line entrypoint
benchmarks/
docs/
figures/
outputs/
scripts/
tests/
```

## Current Research Claim

GapHarness makes a bounded systems claim: obligation-first compilation separates profile inference from certified, registry-constrained support selection, improving auditability and certificate availability without claiming raw-cost dominance over iterative repair. Minimality is **relative** to a declared registry and cost model. The system should explicitly return unsupported or clarification-needed when obligations cannot be covered instead of pretending completion. It does not measure open-world answer correctness, SWE-bench pass@1, or dominance over arbitrary agent frameworks.
