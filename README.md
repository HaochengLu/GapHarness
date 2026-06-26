# GapHarness

**Certificate-Carrying Runtime Harness Compilation for API-Only LLM Agents** — and an honest reliability study of the obligation instrument it depends on.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Tests](https://img.shields.io/badge/tests-129%20passing-brightgreen)
![Core deps](https://img.shields.io/badge/core%20compiler-standard%20library-lightgrey)
![Status](https://img.shields.io/badge/manuscript-v3%20(in%20preparation)-orange)

📄 **Paper:** [`paper/drafts/gapharness_manuscript_v3.pdf`](paper/drafts/gapharness_manuscript_v3.pdf) (compiled) · source [`gapharness_manuscript_v3.md`](paper/drafts/gapharness_manuscript_v3.md) · roadmap [`docs/PUBLICATION_PLAN.md`](docs/PUBLICATION_PLAN.md)

---

## The problem it solves

API-only LLM agents — no fine-tuning, just a base model plus tool/module APIs — must decide, **before acting**, what external runtime support a request needs and whether the declared runtime can supply it. Two questions are routinely conflated:

1. **Which obligations** does the request impose? (observe external evidence, execute deterministic code, keep durable state, take a real action, gate permissions, verify a contract)
2. **Which declared modules** can discharge those obligations, at what cost?

A direct tool-router picks tools but silently misses an obligation (e.g. the sandbox editor or the permission gate). An always-full harness over-provisions and blurs the safety boundary. Either way, nothing tells a third party *whether the assembled harness is actually sufficient* — or, if the task is impossible under the declared registry, *what exactly is missing*.

> Worked example: *"Using the files in this workspace, run the tests, patch only the sandbox copy, and tell me whether the fix passes — do not touch production."* A router may select a code executor but miss the workspace reader, sandbox editor, permission gate, or trace verifier. GapHarness infers all six obligations, compiles the minimal declared support set, and returns a **certificate-carrying refusal** if (say) sandbox editing or permission gating is absent.

## The approach

GapHarness recasts harnessing as a **decidable pre-execution typing pass** that *separates* the two questions:

1. **Profile** — lift a request to an obligation profile over six obligations: **Observation, Execution, State, Action, Control, Verification**.
2. **Compile** — emit the lowest declared-cost registry subset that discharges the required obligations, capabilities, and dependencies — **or** an explicit, certificate-carrying refusal naming the missing affordance.

## The guarantee (what's novel)

The output is a **proof-carrying witness** — a coverage certificate or a refusal certificate — that a third party verifies in **linear time, without trusting the compiler or the LLM**. The optimizer behind it is conceded textbook **weighted set cover + monotone dependency closure**: **no algorithmic claim**. The contribution is the **certificate-as-contract** between profiling and execution, together with an honest measurement of how reliable the obligation instrument actually is.

---

## Results at a glance

Every number below is reproducible from this repository (LLM annotations are cached for API-free replay).

| Dimension | What is measured | Result |
|---|---|---|
| **Compiler correctness** | Optimum vs an **independently implemented** min-cost solver (no shared code), on every supported row | **1,390 / 1,390 agree · 0 mismatches** |
| **Reliability — status decision** | Krippendorff's α across **3 independent model families** (supported / unsupported / clarify) | **0.91** controlled · **0.79** adversarial |
| **Reliability — coarse obligations** | α for **Observation / Action / Control** | **≥ 0.87** controlled · reproduce adversarially |
| **Reliability — fine obligations** | α for **Execution / State / Verification** on adversarial inputs | **≤ 0.27** — *do not* reproduce |
| **Fail-closed safety** | Adversarial scope-confusion minimal pairs (e.g. "deploy to production from the repo") | returns **unsupported** — does **not** invert |
| **Certificate vs coverage** | Harness success at **medium, non-leaky** feedback (GapBench test800 / HarnessChallenge-200) | **0.91 / 0.79** — equals baselines, **+ checkable witness** |
| **Canonicalization ablation** | Δ held-out coverage with lexical normalization removed; obligation micro-F1 | **+0.039** coverage · F1 **unchanged (0.907)** |
| **Engineering** | Unit tests · core compiler dependencies | **129 passing** · **standard-library only** |

**How to read the headline.** The reliability study is the central empirical result, and it is honest about its own limits: the support decision that the certificate rests on is reproducible, even adversarially, and so are the coarse obligations — but the *fine* obligations collapse to at-or-below-chance agreement on adversarial inputs. We therefore present the six-way typing as a **proposed instrument with measured, heterogeneous reliability**, and ship the codebook + review sheet ([`outputs/iaa/`](outputs/iaa/), [`docs/annotation_codebook.md`](docs/annotation_codebook.md)) for the decisive human pass.

## What is **not** claimed

- ❌ Open-world answer correctness, or GAIA / Terminal-Bench / SWE-bench solving / pass@1.
- ❌ A raw-coverage win over iterative-repair agents — under non-leaky feedback they reach **equal** coverage; the *checkable witness*, not coverage, is the differentiator.
- ❌ Human-audited multi-annotator gold labels — the benchmarks are single-annotator (project-owner) labels; inter-annotator agreement is reported on an independent subset (multi-model agreement as a **proxy**), and a human IAA pass is the scaffolded next step.
- ❌ Any new approximation or complexity result for set cover.

---

## Benchmarks & artifacts

| Path | Contents |
|---|---|
| [`benchmarks/gapbench/v1.0/`](benchmarks/gapbench/v1.0/) | **GapBench v1.0** — 1,000 tasks (single-annotator labels) with schema, manifest, audit log, and dev200 / test800 splits |
| [`benchmarks/boundary_scope/v0.1/`](benchmarks/boundary_scope/v0.1/) | 16 adversarial scope-confusion **minimal pairs** for the fail-closed classifier |
| [`benchmarks/disguised_refusal/v0.1/`](benchmarks/disguised_refusal/v0.1/) | 63 disguised-unsupported + clarify items used in the reliability study |
| [`benchmarks/gaia_transfer/v1.0/`](benchmarks/gaia_transfer/v1.0/) | 200-row GAIA **obligation-transfer** set (transfer only — not GAIA answer solving) |
| `benchmarks/{gapbench_natural,terminal_obligation,harness_exec,harness_challenge,…}/` | naturalized, Terminal-Bench-obligation50, and SWE-HarnessExec boundary-diagnostic scaffolds (see manuscript for scope caveats) |
| [`outputs/iaa/`](outputs/iaa/) | the inter-annotator reliability study — report, metrics, cached raw annotations (API-free replay), human review sheet |
| [`outputs/final/`](outputs/final/) | frozen canonical results + `checksums.sha256` manifest |
| [`outputs/ablation/`](outputs/ablation/) | canonicalization no-lexical ablation |
| [`paper/figures/figure5-7*`](paper/figures/) | reliability (headline), certificate-vs-coverage, and ablation figures (`scripts/generate_v3_figures.py`) |
| [`paper/tables/`](paper/tables/) | result tables, incl. `table_feedback_cost.md` and `table_canonicalize_ablation.md` |

## Quickstart

The core code path is **standard-library only**. Use **Python 3.9+** (pinned interpreter `3.9`; see `.python-version`).

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

Deterministic gold + verification artifacts (no API):

```bash
bash scripts/run_phase2_gold_experiments.sh
bash scripts/check_repro.sh
python3 -m scripts.verify_independent_oracle          # 1,390 / 1,390 · 0 mismatches
shasum -a 256 -c outputs/final/checksums.sha256       # verifies the frozen artifact set
```

Reliability study and ablation (LLM responses are cached for API-free replay):

```bash
python3 -m scripts.run_independent_annotators          # 3 model families -> outputs/iaa/raw/
python3 -m scripts.compute_iaa                          # Krippendorff alpha, kappa, micro-F1
python3 -m scripts.run_canonicalize_ablation --offline  # replays from cached raw profiles
python3 -m scripts.generate_v3_figures                  # regenerates figures 5-7
```

LLM sweeps from scratch require an OpenAI-compatible endpoint. Set `GAPHARNESS_API_KEY`, `GAPHARNESS_BASE_URL`, `GAPHARNESS_MODEL` (profiler `gpt-5.4-mini`, fallback `gpt-5.5`); see [`docs/reproducibility.md`](docs/reproducibility.md). **Never commit the key.**

## Safety / MVP scope

The default executor is a deterministic sandbox/mock runtime: no irreversible file edits, real API calls, emails, or deployments. The SWE-HarnessExec runner makes real local edits and runs pytest inside generated fixtures only. The certificate-carrying refusal is evaluated as a **pre-execution** witness; a live side-effect-logging executor is future work.

## Repository layout

```text
gapharness/
  schema.py             typed data model
  registry.py           module affordance registry
  profiler.py           gold and heuristic obligation profilers
  llm_profiler.py       LLM profile normalization + fail-closed scope classifier
  compiler.py           exact certificate-carrying minimal-harness compiler
  independent_oracle.py independent min-cost solver (compiler cross-check)
  dominance_registry.py dominance-bearing registry for the equivalence replay
  executor.py           deterministic sandbox/mock executor
  verifiers.py          sufficiency and minimality checks
  baselines.py          direct / tool-router / full / difficulty / oracle systems
  evaluation.py         benchmark runner and metrics
  cli.py                command-line entrypoint
benchmarks/   task sets and splits        outputs/   frozen results, IAA study, ablation
paper/        v3 manuscript + PDF,        docs/      codebook, reproducibility, plan
              figures, tables, appendix   scripts/   experiment + figure generators
tests/        129 unit tests
```

## Citation

```bibtex
@unpublished{lu2026gapharness,
  title  = {GapHarness: Certificate-Carrying Runtime Harness Compilation for
            API-Only LLM Agents, and a Reliability Study of the Obligation Instrument},
  author = {Lu, Haocheng},
  year   = {2026},
  note   = {Manuscript in preparation}
}
```

## Current research claim

GapHarness makes a **bounded systems claim** — a systems-and-measurement contribution, not an algorithm. Obligation-first compilation separates profile inference from certified, registry-constrained support selection, improving auditability and certificate availability **without** claiming raw-coverage dominance over iterative repair. The reliability study measures exactly where the obligation instrument can be trusted today (the status decision and coarse obligations, even adversarially) and where it cannot (the fine obligations, adversarially). Minimality is **relative** to a declared registry and cost model, and the system returns *unsupported* or *clarification-needed* rather than pretending completion.
