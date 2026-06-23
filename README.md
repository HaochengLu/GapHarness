# GapHarness

[![CI](https://github.com/HaochengLu/GapHarness/actions/workflows/ci.yml/badge.svg)](https://github.com/HaochengLu/GapHarness/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Artifact](https://img.shields.io/badge/artifact-paper--ready-informational)](ARTIFACTS.md)

GapHarness is a research artifact for **certificate-carrying runtime harness compilation** for API-only LLM agents. It separates two decisions that are often conflated in tool routers:

1. What obligations does a user request impose?
2. Which declared runtime supports are sufficient, minimal, and auditable for those obligations?

The system compiles an obligation profile over six families, **Observation**, **Execution**, **State**, **Action**, **Control**, and **Verification**, into a lowest declared-cost module subset under a finite registry. If the declared registry cannot support the task, GapHarness returns `unsupported`, `under-covered`, or verifier-visible failure rather than silently pretending support.

> Scope: GapHarness evaluates harness coverage, registry-constrained support selection, minimality certificates, and executable sandbox traces. It does not claim open-world answer correctness, SWE-bench pass@1, or dominance over arbitrary agent frameworks.

中文说明见 [README.zh-CN.md](README.zh-CN.md).

## Paper And Artifact

- Manuscript PDF: [paper/submission/arxiv_package/gapharness_arxiv.pdf](paper/submission/arxiv_package/gapharness_arxiv.pdf)
- Manuscript source: [paper/submission/arxiv_package/gapharness_manuscript_v2.md](paper/submission/arxiv_package/gapharness_manuscript_v2.md)
- Artifact index: [ARTIFACTS.md](ARTIFACTS.md)
- Reproducibility guide: [REPRODUCIBILITY.md](REPRODUCIBILITY.md)
- Final checksums: [outputs/final/checksums.sha256](outputs/final/checksums.sha256)
- Submission package checksums: [paper/submission/arxiv_package/checksums.sha256](paper/submission/arxiv_package/checksums.sha256)

Suggested citation metadata is available in [CITATION.cff](CITATION.cff).

## Why This Exists

Modern LLM agents increasingly depend on runtime support: web retrieval, code execution, workspace state, sandbox actions, permission gates, and verification. A direct tool router can under-cover safety or verification requirements; an always-full harness can over-cover every prompt; an iterative repair loop can recover coverage but may not preserve a checkable minimality certificate.

GapHarness treats runtime support selection as a compiler problem over a declared affordance registry. The compiler returns:

- selected modules and declared cost,
- covered obligations and capabilities,
- unsatisfied dependencies or missing affordances,
- a registry-relative minimality certificate,
- verifier feedback for unsupported or under-covered cases.

## Repository Structure

```text
gapharness/                         core library
  compiler.py                       exact compiler with pruning and certificates
  registry.py                       declared module affordance registry
  profiler.py                       gold and heuristic profilers
  llm_profiler.py                   structured LLM profiler wrapper
  baselines.py                      direct, router, full, oracle baselines
  executor.py                       deterministic sandbox executor
  verifiers.py                      coverage and trace verifiers
  evaluation.py                     metrics and result aggregation
scripts/                            benchmark, experiment, and report scripts
tests/                              unit tests
benchmarks/                         frozen benchmark artifacts and manifests
outputs/final/                      final result tables, traces, and checksums
paper/submission/arxiv_package/     PDF, source, tables, figures, reports
docs/                               project notes and claim-boundary documents
```

## Benchmarks Included

| Benchmark | Purpose | Status |
| --- | --- | --- |
| GapBench-1000 | controlled obligation/capability coverage benchmark | project-owner-audited |
| GAIA Transfer-200 | obligation-transfer diagnostic from GAIA-style tasks | project-owner-audited |
| GapBench Natural-200 | naturalized prompt surface over audited labels | project-owner-audited |
| HarnessChallenge-200 | targeted boundary diagnostic | author-reviewed diagnostic |
| SWE-HarnessExec-50 | provided-patch sandbox pytest trace validation | sandbox-only executable trace |
| SWE-Obligation-50 | issue-derived obligation labeling scaffold | project-owner-audited |
| Naturalistic Holdout v0.1 | independent naturalistic candidate set | review-sheet based artifact |
| RealBoundary-100 | sandbox/mock/local vs real-world side-effect boundary diagnostic | author-seeded diagnostic |

These datasets are for runtime harness selection and coverage diagnostics. They are not answer-level task-solving benchmarks unless a task-specific grader is explicitly provided.

## Main Experimental Axes

The final artifact includes:

- deterministic compiler validation against oracle minimal harnesses,
- LLM profiling and registry-guarded profiling,
- direct, heuristic router, LLM tool router, always-full, workflow-generation, ReAct-style, verifier-repair, and GapHarness-Repair baselines,
- registry perturbation and gold-label permutation stress tests,
- tool-bait and pure-language negative controls,
- certificate utility proxies,
- feedback-level replay for weak, medium, and strong diagnostics,
- compiler ablation and synthetic registry scaling,
- status confusion and profiler error taxonomy,
- executable sandbox trace checks.

The paper's central claim is intentionally bounded: obligation-first compilation improves auditability and certificate availability for registry-constrained runtime support selection, especially compared with direct routing and uncensored tool selection. Feedback-based repair baselines can achieve high harness success on controlled diagnostics; GapHarness-Repair converts that feedback into profile constraints and recompiles a certificate-backed harness.

## Quickstart

Use Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the small seed benchmark:

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

Run deterministic final-stage checks:

```bash
pytest
python -m py_compile gapharness/*.py scripts/*.py
shasum -a 256 -c --status --strict outputs/final/checksums.sha256
shasum -a 256 -c --status --strict paper/submission/arxiv_package/checksums.sha256
```

## Reproducing Larger Experiments

Many deterministic experiments can be rerun without network access:

```bash
python -m scripts.run_phase2d_stress_tests all
python -m scripts.run_compiler_equivalence_replay
python -m scripts.run_compiler_scaling
python -m scripts.run_phase5_agentic_baselines
python -m scripts.run_phase6_reviewer_evidence
```

LLM profiler sweeps require an OpenAI-compatible API configured only through environment variables:

```bash
export GAPHARNESS_API_KEY="..."
export GAPHARNESS_BASE_URL="..."
export GAPHARNESS_MODEL="..."
python -m scripts.run_phase2b_llm_sweep dev
python -m scripts.run_phase2b_llm_sweep test
```

No API keys or provider-private endpoints are stored in this repository.

## Artifact Integrity

The final release includes checksums for reproducibility:

```bash
shasum -a 256 -c --strict outputs/final/checksums.sha256
shasum -a 256 -c --strict paper/submission/arxiv_package/checksums.sha256
```

The release was also scanned to ensure that no private API endpoint, API key, or dummy `sk-...` token pattern is present in public text artifacts.

## License

Code and documentation are released under the [MIT License](LICENSE), unless otherwise noted in a dataset manifest. Some benchmark rows are derived from or paraphrase external benchmark styles; use the manifests under [benchmarks/](benchmarks/) for provenance and scope.

