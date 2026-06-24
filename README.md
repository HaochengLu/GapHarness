# GapHarness

GapHarness is a research system for **Certificate-Carrying Runtime Harness Compilation** for API-only LLM agents.

Given an obligation profile and a finite registry of modules with declared affordances and design-time costs, GapHarness compiles the lowest declared-cost module subset that satisfies the required obligations, capabilities, and dependencies, or emits an explicit, certificate-carrying refusal that names the missing affordance. The compiler is exact within the declared registry and emits a witness a third party can verify in linear time **without trusting the compiler or the LLM**. Obligation inference is separated from certified, registry-constrained support selection so the two questions can be audited independently.

It treats an agent harness as a runtime system that covers external obligations a stateless LLM cannot satisfy by itself: **Observation, Execution, State, Action, Control, Verification**.

> **Current manuscript:** `paper/drafts/gapharness_manuscript_v3.md` (built PDF: `paper/drafts/gapharness_manuscript_v3.pdf`). The earlier `gapharness_manuscript_v2.md` is preserved for history. The full reject→publishable roadmap is in `docs/PUBLICATION_PLAN.md`.

## What the paper claims (honest scope)

The contribution is a **certificate-as-contract** between profiling and execution: a decidable pre-execution typing pass emits a proof-carrying refusal/coverage witness, verifiable in linear time without trusting the compiler or the LLM. The optimizer behind it is conceded textbook weighted set cover plus monotone dependency closure — **no algorithmic claim**.

**Key results (all reproducible from this repo):**

- **Reliability study (the headline empirical result).** Three independent model families (`gpt-5.5`, `claude-opus-4-1`, `gemini-2.5-pro`) annotate against one shared neutral codebook. The supported/unsupported/clarify **status** decision reproduces — Krippendorff α = **0.91** (controlled) / **0.79** (adversarial) — as do the coarse Observation/Action/Control obligations; the finer **Execution/State/Verification** obligations do **not** reproduce on adversarial inputs (α ≤ 0.27). We therefore present the six-way obligation typing as a *proposed instrument with measured, heterogeneous reliability*, and ship the codebook + review sheet for the decisive human pass (`outputs/iaa/`, `docs/annotation_codebook.md`).
- **Compiler correctness.** By construction (Proposition 1) and corroborated by an **independently implemented** solver on **1,390 / 1,390** supported rows with **0 mismatches** (`gapharness/independent_oracle.py`) — not by an oracle the compiler generated.
- **Fail-closed safety boundary.** A scope classifier that does not invert under lexical scope-confusion: *"deploy to production from the repo and send a real email to customers"* → **unsupported** (`benchmarks/boundary_scope/v0.1/`).
- **Certificate vs coverage (honest).** Under non-leaky feedback, iterative-repair baselines reach **equal coverage without a certificate**; the checkable witness — not coverage — is the differentiator (`paper/tables/table_feedback_cost.md`).
- **Canonicalization ablation.** Removing the deterministic lexical normalization moves held-out coverage by only +0.039 with obligation micro-F1 unchanged: the model, not a keyword router, carries the inference (`paper/tables/table_canonicalize_ablation.md`).

**Not claimed:** open-world answer correctness; GAIA / Terminal-Bench / SWE-bench solving or pass@1; dominance over agent frameworks; or that the labels are independently human-audited gold (a human inter-annotator pass is the scaffolded next step, not a completed study).

## Benchmarks and artifacts

- `benchmarks/gapbench/v1.0/`: 1000-row GapBench v1.0 (single-annotator / project-owner labels), with manifest, schema, audit log, and dev200/test800 splits.
- `benchmarks/gaia_transfer/v1.0/`: 200-row GAIA obligation-transfer set (single-annotator labels; obligation-transfer only, not GAIA answer solving).
- `benchmarks/boundary_scope/v0.1/`: 32-row (16 pairs) adversarial scope-confusion minimal-pair set for the fail-closed classifier.
- `benchmarks/disguised_refusal/v0.1/`: 63-row disguised-unsupported + clarify set used in the reliability study.
- `benchmarks/gapbench_natural/v1.0/`, `benchmarks/terminal_obligation/v0.1/`, `benchmarks/harness_exec/v1.1/`: naturalized, terminal-transfer, and SWE-HarnessExec scaffolds (boundary diagnostics; see manuscript for scope caveats).
- `outputs/iaa/`: the inter-annotator reliability study — report, metrics, 549 cached raw annotations (API-free replay), and the human review sheet.
- `outputs/final/feedback_cost/`, `outputs/ablation/`: honest feedback-cost analysis and the canonicalization ablation.
- `paper/figures/figure5-7*`: reliability (headline), certificate-vs-coverage, and ablation figures (`scripts/generate_v3_figures.py`).
- `outputs/final/checksums.sha256`: checksum manifest for the frozen artifact set.

## Quickstart

The core code path is standard-library only. Use **Python 3.9+** (the pinned interpreter is 3.9; see `.python-version`).

```bash
python3 -m scripts.build_seed_benchmark --out benchmarks/gapbench_factorial_seed.jsonl
python3 -m gapharness.cli run-benchmark --benchmark benchmarks/gapbench_factorial_seed.jsonl --system all --profiler gold --out /tmp/results_gold.jsonl
python3 -m gapharness.cli make-report --results /tmp/results_gold.jsonl --out /tmp/summary_gold.md
python3 -m unittest discover -s tests        # 129 tests
```

Editable install (gives the `gapharness` console script):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Reproduce the experiments

Deterministic gold artifacts (no API):

```bash
bash scripts/run_phase2_gold_experiments.sh
bash scripts/check_repro.sh
python3 -m scripts.verify_independent_oracle          # 1390/1390, 0 mismatches
shasum -a 256 -c outputs/final/checksums.sha256       # 2672 OK
```

LLM experiments (require an OpenAI-compatible endpoint). Set `GAPHARNESS_API_KEY`, `GAPHARNESS_BASE_URL`, and `GAPHARNESS_MODEL`; the experiments use profiler model `gpt-5.4-mini` (fallback `gpt-5.5`) — see `docs/reproducibility.md`. Never commit the key.

```bash
python3 -m scripts.run_phase2b_llm_sweep dev
python3 -m scripts.run_phase2b_llm_sweep test
python3 -m scripts.run_phase2d_stress_tests all
```

Reliability study and ablation (LLM responses are cached for API-free replay):

```bash
python3 -m scripts.run_independent_annotators          # 3 model families -> outputs/iaa/raw/
python3 -m scripts.compute_iaa                          # Krippendorff alpha, kappa, micro-F1
python3 -m scripts.run_canonicalize_ablation --offline # replays from cached raw profiles
```

## MVP scope

The default executor is a deterministic sandbox/mock runtime: no irreversible file edits, real API calls, emails, or deployments. The SWE-HarnessExec runner makes real local edits and runs pytest inside generated fixtures only. The certificate-carrying refusal is evaluated as a *pre-execution* witness; a live side-effect-logging executor is future work.

## Repository layout

```text
gapharness/
  schema.py            typed data model
  registry.py          module affordance registry
  profiler.py          gold and heuristic obligation profilers
  llm_profiler.py      LLM profile normalization + fail-closed scope classifier
  compiler.py          exact certificate-carrying minimal-harness compiler
  independent_oracle.py independent min-cost solver (compiler cross-check)
  dominance_registry.py dominance-bearing registry for the equivalence replay
  executor.py          deterministic sandbox/mock executor
  verifiers.py         sufficiency and minimality checks
  baselines.py         direct/tool-router/full/difficulty/oracle systems
  evaluation.py        benchmark runner and metrics
  cli.py               command-line entrypoint
benchmarks/  docs/  figures/  outputs/  paper/  scripts/  tests/
```

## Current research claim

GapHarness makes a bounded systems-and-measurement claim. Obligation-first compilation separates profile inference from certified, registry-constrained support selection, improving auditability and certificate availability **without** claiming raw-coverage dominance over iterative repair. The reliability study measures exactly where the obligation instrument can be trusted today (the status decision and coarse obligations, even adversarially) and where it cannot (the fine obligations, adversarially). Minimality is **relative** to a declared registry and cost model, and the system returns unsupported or clarification-needed rather than pretending completion. It does not measure open-world answer correctness, SWE-bench pass@1, or dominance over arbitrary agent frameworks.
