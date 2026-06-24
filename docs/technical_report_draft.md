# GapHarness: Obligation-First Minimal Harness Synthesis for API-only LLM Agents

## Abstract

GapHarness studies a minimal runtime synthesis problem for API-only LLM agents. Given a user query, a base model, and a declared registry of runtime modules, the system infers the external obligations required for a warranted answer or action, compiles the lowest-cost module subset that covers those obligations, executes the resulting loop in a sandbox runtime, and verifies both sufficiency and relative minimality through deterministic traces and drop-one ablations.

We introduce an obligation ontology covering Observation, Execution, State, Action, Control, and Verification. On a 1000-task project-owner-reviewed controlled benchmark (single-annotator (project-owner) labels; inter-annotator agreement reported on an independent subset), GapHarness matches an oracle minimal harness under gold labels while common routing baselines either under-harness or over-harness. A 200-task GAIA transfer set and a 200-task naturalized review set provide the first path toward validating the ontology beyond templated controlled tasks.

## Core Claim

The project does not claim globally optimal harnessing. It claims relative minimality under a declared obligation ontology, module registry, dependency model, and cost function. If no registry subset covers the required obligations and capabilities, the system returns unsupported or clarification-needed rather than fabricating completion.

## Obligation Ontology

- Observation: external information beyond model parameters or prompt context.
- Execution: deterministic computation, code execution, testing, or validation.
- State: durable task state, workspace state, or intermediate artifacts.
- Action: sandboxed external-world mutation in the MVP.
- Control: cross-cutting constraint that becomes explicit when risk, permissions, budget, privacy, or irreversible action is present.
- Verification: independent contract, evidence, execution, or diff checking.

## System

```text
User Query
 -> Obligation Profiler
 -> Obligation Vector + Required Capabilities + Output Contract
 -> Module Registry Lookup
 -> Exact Minimal Harness Compiler
 -> Sandbox Executor
 -> Trace Recorder
 -> Contract / Evidence / Execution / Minimality Verifiers
 -> Experiment Report
```

## First MVP

The first runnable MVP includes:

- deterministic gold and heuristic profilers
- exact set-cover compiler over a 10-module registry
- sandbox executor with JSONL traces
- deterministic sufficiency verifier
- drop-one minimality verifier
- 1000-task GapBench-Factorial benchmark, project-owner-reviewed (single-annotator (project-owner) labels; inter-annotator agreement reported on an independent subset)
- Direct, Tool Router, Always-full, Difficulty Router, Oracle Minimal baselines
- frozen GapBench v1.0 and GAIA-Transfer v1.0 manifests, schemas, audit logs, and reproducible result tables
- a draft GapBench-Natural-200 review package for testing natural user phrasing

## Current MVP Results

On the 100-task synthetic seed benchmark, the gold profiler path makes GapHarness match the oracle minimal harness exactly: 1.00 success, 2.88 average cost, and 0.00 excess cost. Direct LLM reaches only 0.18 success, while Always-full reaches 0.86 success but with 16.00 average cost and 0.86 over-harness rate.

The LLM profiler cascade reaches 1.00 success after registry canonicalization, with 3.68 average cost and 0.80 excess cost. This demonstrates the expected tradeoff: a high-recall obligation profiler eliminates under-harnessing but introduces over-harnessing unless calibrated for minimality.

On the expanded 1000-task project-owner-reviewed GapBench, GapHarness again matches Oracle Minimal exactly under the gold profiler: 1.00 success, 3.67 average cost, and 0.00 cost delta. Direct LLM reaches 0.20 success; Tool Router reaches 0.34 success with 0.60 under-harness rate; Always-full reaches 0.94 success but pays 16.00 average cost and 0.94 over-harness rate.

The current Phase 2 artifacts include paper-ready tables in `outputs/phase2/` and SVG figures in `figures/phase2/`. Table 1 reports the controlled GapBench-1000 results, Table 2 reports GAIA/Natural smoke evaluations, and Table 3 reports controlled category breakdowns.

## Phase 2B: LLM-inferred Obligations

The deterministic results above assume gold obligations. Phase 2B asks whether an LLM profiler can infer those obligations well enough for practical harness synthesis.

We froze the deterministic checkpoint as `phase2-deterministic-artifacts-v1` before running LLM profiler experiments. Subsequent Phase 2B experiments evaluate inferred obligations only and do not modify GapBench v1.0 labels, compiler rules, or deterministic baselines.

On GapBench dev200, three profiler modes were calibrated: single-prompt, recall-biased, and minimality-biased. All three satisfied the pre-registered sufficiency guard. The primary profiler was selected by the stated rule: under-harness rate at most 0.08, success at least 0.90, then lowest excess cost. This selected `llm_single`.

On held-out test800, selected LLM GapHarness reaches 0.89 success at 3.59 average cost, compared with Direct at 0.20 success, Tool Router at 0.32 success, Difficulty Router at 0.41 success, and Always-full at 0.94 success with 16.00 average cost. This result supports the practical value of obligation-first harness synthesis, while also showing that profiler calibration remains an open limitation.

The dominant held-out failure pattern is capability lowering rather than obligation recognition alone. In several failures, the profiler predicts the appropriate high-level obligations but includes `real_world_side_effect`, which the MVP registry intentionally does not cover for sandbox/mock actions. The next calibrated profiler variant should include a registry guard that trims this capability unless the query explicitly asks for a real irreversible external action.

### Registry-Guarded Profiler Calibration

Phase 2B showed that an unguarded LLM profiler can outperform tool-router and difficulty-router baselines while remaining close to oracle cost, but it introduced a systematic calibration error: sandbox/mock actions were sometimes lowered to unsupported real-world side effects. We therefore evaluate a registry-guarded profiler that keeps the base LLM prediction but applies a deterministic guard grounded in the declared module registry and sandbox/action boundary.

This Phase 2C experiment is reported separately from the Phase 2B selected-profiler result. On GapBench dev200, `llm_registry_guarded` improves success from 0.92 to 0.97 and reduces under-harnessing from 0.08 to 0.03 relative to Phase 2B `llm_single`, while increasing average cost from 3.68 to 4.02. It therefore passes the pre-registered dev selection rule as a sufficiency-oriented calibration.

On held-out test800, the registry guard improves success from 0.89 to 0.94 and reduces under-harnessing from 0.09 to 0.03 relative to the Phase 2B selected `llm_single` result. Unsupported false positives fall from 56 to 12. The tradeoff is higher cost and regret: average cost rises from 3.59 to 3.98 and regret from -0.09 to 0.30. This supports the narrow claim that registry guarding repairs a specific sandbox/mock-action failure mode, not that it globally improves obligation inference.

On GAIA-Transfer v1.0, the same guard does not fire and does not solve the dominant transfer errors. The registry-guarded profiler reaches 0.56 harness success with high over-harness and under-harness rates. This negative transfer result suggests that GAIA failures are driven by file, multimodal, evidence, and state-boundary mismatches rather than the sandbox real-world-side-effect error seen in GapBench.

## Stress Tests and Negative Controls

### Registry Perturbation

We evaluate whether GapHarness silently claims support when the declared module registry lacks required affordances. For each perturbation, we select a relevant first-N 60-task subset and compare the base registry against a registry with one module removed: `python_executor`, `source_span_checker`, `permission_gate`, `sandbox_file_editor`, `web_retrieval`, or `contract_verifier`.

Under the base registry, all six subsets achieve 1.00 success. Under the perturbed registries, success drops to 0.00 for every perturbation, with unsupported and under-covered rates rising to 1.00. The dominant missing capabilities align with the removed affordance: `execution`, `source_spans`, `permission`, `diff`, `evidence_sources`, and `contract_check`, respectively.

Registry perturbation verifies that GapHarness does not silently hallucinate support when required affordances are absent; it degrades into unsupported or under-covered status.

### Gold Label Permutation

We test whether GapBench labels have semantic force by corrupting a 200-task subset of supported examples. This is not a realistic corruption model. It is an anti-circularity stress test: corrupted obligation profiles are fed to the compiler, while the verifier still checks against the original project-owner-reviewed labels.

Correct gold labels yield 1.00 success and 0.00 cost delta. The permutation generator changes obligations or required capabilities for all 200 corrupted profiles. Corrupted labels reduce success to 0.17, raise under-harness to 0.83, raise wrong-harness to 0.79, and raise over-harness to 0.55. Thus, arbitrary obligation labels do not pass through the compiler-verifier stack unchanged; errors in obligation semantics produce measurable failures.

### Tool-Bait and Pure-Language Negative Controls

We separately evaluate `pure_language_negative` and `tool_bait` categories. Direct, GapHarness gold, LLM GapHarness, and registry-guarded GapHarness all achieve 1.00 success with 0.00 average cost and 0.00 over-harness on both categories. Always-full over-harnesses both categories at 1.00 with cost 16.00. Tool Router and Difficulty Router over-harness tool-bait prompts at 0.51 because they react to tool-like keywords despite the task explicitly requiring no external tool use.

These negative controls support the claim that GapHarness is obligation-sensitive rather than keyword/tool-sensitive.

## Benchmark Assets

GapBench v1.0 is a 1000-row controlled benchmark designed to isolate obligation coverage and minimal harness compilation. It includes dev200 and test800 splits, a manifest, a schema description, and an audit log. The labels are single-annotator (project-owner) labels reviewed on 2026-06-22; inter-annotator agreement is reported on an independent subset.

GAIA-Transfer v1.0 contains 200 GAIA-derived rows, with 100 validation and 100 test examples. It is intended as an obligation-transfer benchmark over real assistant queries, not as a claim of full GAIA answer-level accuracy. The transfer labels are single-annotator (project-owner) labels reviewed on 2026-06-22; inter-annotator agreement is reported on an independent subset.

GapBench-Natural v1.0 draft contains 200 naturalized prompts sampled from audited GapBench source rows. It is currently for human review. The inherited labels should not be treated as final paper claims until the naturalized wording is audited.

## Evaluation Metrics

- Task success
- Cost-normalized success, approximated in MVP by success over declared runtime cost
- Over-harness rate
- Under-harness rate
- Wrong-harness rate
- Cost delta (excess cost)
- Counterfactual module necessity
- Redundancy

## Planned Experiments

1. GapBench v1.0 gold-label controlled evaluation. Current status: complete for deterministic gold compiler and baselines.
2. GAIA-Transfer v1.0 obligation-transfer evaluation. Current status: complete for deterministic gold compiler smoke.
3. GapBench-Natural-200 human review and post-audit evaluation. Current status: review package generated.
4. LLM profiler calibration on GapBench dev200, followed by final reporting on test800. Current status: complete for `llm_single`, `llm_recall`, and `llm_minimality` dev calibration and selected `llm_single` held-out test800 sweep.
5. WildToolBench subset as a second transfer setting.
6. Terminal-Bench subset for terminal-heavy execution/state/verification cases.

## Limitations

The current code supports deterministic gold, heuristic, and LLM structured-output profilers, but the full Phase 2 LLM profiler dev/test sweep is still pending. The executor is a sandbox/mock runtime and does not perform irreversible external actions.

The main current limitation is that gold-label compiler results isolate the harness synthesis problem but do not by themselves measure open-world answer correctness. GAIA transfer labels evaluate obligation assignment and harness coverage, while answer-level GAIA accuracy would require separate answer generation and judging. The Natural-200 set is also not final until the visible user queries are audited.

## GAIA Transfer Status

GAIA `2023_all` now loads locally through Hugging Face Datasets. The repository contains a 200-row project-owner-reviewed transfer subset: 100 validation examples and 100 test examples. These transfer labels are single-annotator (project-owner) labels; inter-annotator agreement is reported on an independent subset. GapHarness reaches 1.00 success and 0.00 cost delta on this transfer subset under the gold profiler.
