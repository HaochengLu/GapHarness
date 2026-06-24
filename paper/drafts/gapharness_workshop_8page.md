---
title: "GapHarness: Obligation-First Minimal Harness Synthesis for API-Only LLM Agents"
author: "Anonymous Authors"
bibliography: paper/references.bib
link-citations: true
geometry: margin=1in
fontsize: 10pt
---

# Abstract

API-only LLM agents need external runtime support for retrieval, execution, state, action, control, and verification. Tool routers often choose tools directly, conflating what a query requires with which runtime modules happen to exist. GapHarness separates these questions: it first infers external obligations, then compiles the lowest-cost declared runtime harness that covers them. On the 1000-task human-audited GapBench controlled benchmark, GapHarness matches the oracle minimal harness under gold obligations. With LLM-inferred obligations, it outperforms direct and router baselines while exposing calibration tradeoffs. Registry guarding reduces a systematic sandbox-action unsupported false-positive failure. Anti-circularity stress tests show that success depends on declared registry affordances and meaningful obligation labels.

# 1. Motivation

Tool-using LLM agents and reasoning-action systems show that external actions can improve model behavior [@yao2023react; @schick2023toolformer; @patil2023gorilla; @qin2024toolllm]. But tool choice is only one layer. A query may require observation beyond the prompt, deterministic execution, durable state, sandbox action, risk control, or independent verification. These are obligations, not tool names.

GapHarness asks a narrow systems question:

> Given a user query, an obligation profile, and a declared registry of modules, can we compile the minimal harness that satisfies the external obligations required for a warranted answer or action?

This is not another general agent framework. It is a compiler-style layer between obligation inference and runtime module selection. Minimality is relative to a declared ontology, registry, dependency model, and cost function.

# 2. Method

GapHarness uses six obligations: Observation, Execution, State, Action, Control, and Verification. A profiler emits obligations, required capabilities, output contracts, and unsupported or clarification conditions. A registry declares modules, affordances, dependencies, and cost. The compiler performs exact search over registry subsets and returns the lowest-cost subset that covers the profile. If no subset covers the profile, it returns unsupported or clarify rather than hallucinating support.

![GapHarness pipeline. The system separates obligation profiling, declared registry lookup, exact compilation, sandbox execution, tracing, and verification.](paper/figures/figure1_pipeline_print.png){width=95%}

# 3. Benchmark and Metrics

GapBench-1000 is a controlled factorial benchmark with human-audited labels for obligations, required capabilities, oracle minimal harnesses, expected status, and risk metadata. It is designed to isolate harness compilation, not to replace open-world answer-level benchmarks such as GAIA [@mialon2024gaia], AgentBench [@liu2024agentbench], Terminal-Bench [@merrill2026terminalbench], WildToolBench [@yu2026wildtoolbench], or MCP-Bench [@wang2025mcpbench].

We report success, average cost, oracle cost, minimality regret, over-harnessing, under-harnessing, wrong-harnessing, and redundancy.

# 4. Main Results

Table 1 shows the gold-obligation compiler result. It proves that the exact compiler matches oracle minimal harnesses under human-audited obligations. It does not prove open-world profiling.

| System | N | Success | Cost | Oracle | Regret | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 1000 | 0.20 | 0.00 | 3.67 | -3.67 | 0.00 | 0.74 | 0.00 |
| tool | 1000 | 0.34 | 2.10 | 3.67 | -1.57 | 0.11 | 0.60 | 0.42 |
| difficulty | 1000 | 0.43 | 3.46 | 3.67 | -0.21 | 0.28 | 0.51 | 0.16 |
| always_full | 1000 | 0.94 | 16.00 | 3.67 | 12.33 | 0.94 | 0.00 | 0.00 |
| GH-gold | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 |

# 5. LLM Profiler and Registry Guard

With LLM-inferred obligations on held-out test800, GapHarness reaches 0.89 success at 3.59 average cost, outperforming direct and router baselines. The main remaining failure is profiler calibration. Phase 2C adds a deterministic registry guard for a systematic sandbox/mock action failure where the LLM profiler lowered local sandbox actions into unsupported real-world side effects.

| Split | Profiler | N | Success | Cost | Regret | Over | Under | Unsupported FP |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| test800 | 2B | 800 | 0.89 | 3.59 | -0.09 | 0.14 | 0.09 | 56 |
| test800 | 2C guard | 800 | 0.94 | 3.98 | 0.30 | 0.15 | 0.03 | 12 |

![Registry guard correction. Registry guarding reduces unsupported false positives from 56 to 12 on held-out GapBench test800, at the cost of higher regret.](paper/figures/figure4_registry_guard_unsupported_fp_reduction.png){width=90%}

# 6. Anti-Circularity Stress Tests

Registry perturbation removes key modules one at a time. For relevant 60-task subsets, base success is 1.00 and perturbed success is 0.00 for each removed module. The dominant missing capability matches the removed affordance.

Gold label permutation corrupts 200 supported profiles while the verifier checks original labels. Correct labels yield 1.00 success. Permuted labels reduce success to 0.17 and raise under-harnessing to 0.83 and wrong-harnessing to 0.79. This is an anti-circularity stress test, not a realistic label-noise model.

Negative controls show that pure-language and tool-bait prompts do not trigger GapHarness over-harnessing. Tool Router and Difficulty Router over-harness tool-bait prompts at 0.51; Always-full over-harnesses by construction.

| Stress test | Condition | N | Main result |
|---|---|---:|---|
| Registry perturbation | six module removals | 60 each | success drops 1.00 to 0.00 |
| Gold permutation | corrupted labels | 200 | success drops 1.00 to 0.17 |
| Tool-bait negative control | GapHarness guarded | 100 | over-harness 0.00 |
| Tool-bait negative control | Tool Router | 100 | over-harness 0.51 |

# 7. Boundaries

GAIA-Transfer gold smoke reaches 1.00 success under gold obligation labels, but this is obligation-transfer only and not GAIA answer solving. GAIA registry-guarded reaches 0.56 success with high over- and under-harnessing, a useful limitation result. Terminal-Bench-obligation50 is an appendix scaffold with labels pending audit, not Terminal-Bench solving.

The executor is deterministic sandbox/mock infrastructure. It does not perform irreversible file edits, real API calls, payments, emails, deployments, or production changes. GapBench is controlled and factorial, not a complete real-world benchmark. LLM profiling remains imperfect.

# 8. Conclusion

GapHarness reframes agent harnessing as two separable problems: obligation inference and minimal runtime compilation. Under gold obligations, the compiler matches oracle minimal harnesses. Under LLM-inferred obligations, it improves over simple baselines while exposing calibration tradeoffs. Registry perturbation, label permutation, and negative controls show that the system is sensitive to registry affordances and obligation semantics rather than tool keywords alone.

# References
