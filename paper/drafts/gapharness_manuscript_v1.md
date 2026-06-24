---
title: "GapHarness: Obligation-First Minimal Harness Synthesis for API-Only LLM Agents"
author: "Anonymous Authors"
bibliography: paper/references.bib
link-citations: true
geometry: margin=1in
fontsize: 10pt
---

# Abstract

API-only LLM agents increasingly rely on external runtimes for retrieval, code execution, state management, action, control, and verification. Existing tool routers often choose tools directly, which can conflate two separable questions: what external obligations a user query imposes, and what smallest runtime harness can satisfy those obligations. We introduce GapHarness, a research system that formulates agent harnessing as obligation inference followed by minimal runtime compilation. Given an obligation profile and a declared module registry, GapHarness compiles the lowest-cost module subset that covers required obligations and capabilities, executes a deterministic sandbox loop, and verifies sufficiency and relative minimality.

We define an obligation ontology covering Observation, Execution, State, Action, Control, and Verification, and introduce metrics for over-harnessing, under-harnessing, wrong-harnessing, minimality regret, and redundancy. On the 1000-task human-audited GapBench controlled benchmark, GapHarness matches the oracle minimal harness under gold obligations. With LLM-inferred obligations on held-out test800, GapHarness reaches 0.89 success, outperforming direct and router baselines while exposing a calibration gap. A registry-guarded profiler reduces unsupported false positives from 56 to 12 and improves held-out success to 0.94, at the cost of higher regret. Stress tests show that success depends on declared registry affordances and meaningful obligation labels; negative controls show that GapHarness avoids tool-bait over-harnessing. Transfer runs on GAIA-Transfer and GapBench-Natural identify boundary conditions rather than claiming full open-world task solving.

# 1. Introduction

LLM agents are commonly evaluated as end-to-end systems: a model receives a request, selects tools, acts in an environment, and produces an answer. This framing is useful, but it hides a smaller technical problem that appears whenever an API-only model must decide what runtime support is needed. A user request may require observation beyond the prompt, deterministic execution, durable state, sandbox action, control over risky operations, or independent verification. These are obligations, not tools.

Tool-using and reasoning-action agents have shown that external actions can improve model behavior [@yao2023react; @schick2023toolformer; @patil2023gorilla; @qin2024toolllm]. However, choosing tools is not the same as deciding which external obligations must be satisfied. A keyword-based router may over-call tools when the user explicitly requests no tools, and it may under-call tools when a warranted answer requires evidence, state, or verification that is not obvious from surface wording. Benchmarks of tool choice and tool awareness also show that deciding whether and which tools to use is itself a nontrivial capability [@huang2023metatool].

This paper studies a narrower question:

> Given a user query, an obligation profile, and a declared registry of runtime modules, can we compile the minimal harness that satisfies the external obligations required for a warranted answer or action?

GapHarness separates the problem into two stages. First, a profiler infers an obligation profile: obligations, required capabilities, output contracts, risk level, and unsupported or clarification conditions. Second, an exact compiler searches a declared module registry for the lowest-cost module subset that covers the obligations and capabilities. This separation makes failure interpretable. If a registry does not contain an affordance, the system should return unsupported rather than hallucinating support. If the profiler over- or under-infers obligations, the verifier should expose measurable over-harnessing, under-harnessing, or wrong-harnessing.

The goal is not to build another general-purpose agent framework. The goal is to make harness synthesis measurable and auditable. Minimality is relative to a declared obligation ontology, module registry, dependency model, and cost function. This is a controlled technical claim, not a claim of universal agent optimality.

## Contributions

1. We formulate agent harnessing as obligation inference plus minimal runtime compilation.
2. We implement GapHarness, an API-only compiler from obligations to minimal harness modules.
3. We introduce minimal-sufficiency metrics: over-harnessing, under-harnessing, wrong-harnessing, minimality regret, and redundancy.
4. We evaluate GapHarness on GapBench-1000, LLM-inferred profiler settings, registry-guarded calibration, transfer subsets, and anti-circularity stress tests.

# 2. Related Work

## Tool-using LLM agents

ReAct interleaves model reasoning traces with environment actions [@yao2023react]. Toolformer trains models to decide when and how to call APIs [@schick2023toolformer], while Gorilla and ToolLLM focus on API selection, API calling, and large tool-use corpora [@patil2023gorilla; @qin2024toolllm]. MetaTool asks whether models know when to use tools and which tools to choose [@huang2023metatool]. GapHarness differs by placing obligation identification before tool or module selection. The compiler does not decide that a query needs "a search tool"; it decides whether the profile imposes Observation, Verification, Execution, State, Action, or Control obligations, then compiles registry modules that cover those obligations.

## Retrieval, execution, and verification

Observation and Verification obligations are motivated by retrieval-augmented generation and provenance-aware answering [@lewis2020rag]. Execution obligations are motivated by program-aided reasoning, where a language model delegates deterministic computation to a runtime [@gao2022pal]. GapHarness treats these as module affordances that can be required, absent, or redundant. Its verifier checks whether the chosen harness covers declared obligations and capabilities; it does not claim semantic answer correctness for arbitrary open-world questions.

## Agent benchmarks and transfer settings

AgentBench evaluates LLMs as agents across interactive environments [@liu2024agentbench]. GAIA evaluates general assistant questions requiring reasoning, multimodality, web browsing, and tool use [@mialon2024gaia]. Terminal-Bench evaluates hard terminal-environment tasks [@merrill2026terminalbench]. WildToolBench and MCP-Bench emphasize realistic tool-use behavior and cross-tool coordination [@yu2026wildtoolbench; @wang2025mcpbench]. GapHarness uses GAIA-derived and terminal-derived transfer artifacts only as obligation-transfer or scaffold evidence. It does not claim full GAIA answer-level solving or Terminal-Bench solving.

## Workflow and harness systems

AutoFlow, AFlow, and WorFBench study workflow generation or workflow optimization for agentic systems [@li2024autoflow; @zhang2025aflow; @qiao2025worfbench]. Recent harness work treats the execution layer itself as an object of study, including automated code harness synthesis, natural-language harnesses, and benchmarked harness effects [@lou2026autoharness; @pan2026naturalharness; @yao2026harnessbench]. GapHarness is complementary: it studies the compiler-like layer that maps obligations to the smallest declared runtime harness rather than optimizing a complete workflow or measuring complete model-harness configurations.

# 3. Problem Formulation

Let a user query be represented by an obligation profile:

- obligations: a subset of Observation, Execution, State, Action, Control, Verification;
- required capabilities: lower-level affordances such as `evidence_sources`, `execution`, `workspace_inspection`, `durable_state`, `sandbox_action`, `permission`, `contract_check`, or `source_spans`;
- output contract and risk metadata;
- clarification or unsupported conditions.

Let a registry contain modules. Each module declares:

- obligations it provides;
- capabilities it provides;
- dependency requirements over obligations and capabilities;
- cost;
- verifier metadata.

The compiler searches for the lowest-cost subset of modules whose provided obligations and capabilities cover the profile and whose dependencies are internally satisfied. If no subset covers the profile, the compiler returns unsupported. If the profile requires clarification, the compiler returns clarify.

This setup yields three useful failure modes:

- under-harnessing: a supported task lacks required obligation or capability coverage;
- over-harnessing: the selected harness costs more than the oracle minimal harness;
- wrong-harnessing: a nonempty harness is selected but verifier failures remain.

Minimality is not absolute. It is relative to the declared registry and cost function.

# 4. GapHarness

GapHarness contains five components.

The profiler maps a query to an obligation profile. The current system supports gold profiles, heuristic profiles, LLM-inferred profiles, and a registry-guarded LLM profile variant. The gold profiler is used to isolate compiler behavior. The LLM profiler is used to measure practical inference quality.

The registry declares available modules. The MVP registry includes web retrieval, source-span checking, Python execution, execution-log checking, workspace inspection, state storage, sandbox file editing, permission gating, contract verification, and trace recording.

The compiler performs exact search over registry subsets and selects the lowest-cost valid harness. It returns direct-answer, supported, clarify, or unsupported harness status.

The executor is a deterministic sandbox/mock runtime. It records traces but does not perform irreversible external side effects.

The verifier checks sufficiency against benchmark gold labels and computes drop-one minimality reports.

![GapHarness pipeline. The figure shows the obligation profiler, declared registry, exact compiler, sandbox executor, trace recorder, and verifier path. It proves system decomposition; it does not prove open-world task solving.](paper/figures/figure1_pipeline_print.png){#fig:pipeline width=95%}

# 5. Benchmarks and Metrics

## GapBench

GapBench v1.0 is a 1000-row controlled benchmark designed to isolate obligation coverage and minimal harness compilation. It contains human-audited labels for obligations, required capabilities, oracle minimal harnesses, expected status, success checker, risk level, and provenance. The benchmark includes dev200 and test800 splits.

GapBench is controlled and factorial. It is not a complete real-world benchmark. Its purpose is to make the compiler and verifier problem measurable.

## Transfer and review sets

GAIA-Transfer v1.0 contains 200 GAIA-derived obligation-transfer rows. It evaluates obligation assignment and harness selection only; it is not a full GAIA answer-level benchmark.

GapBench-Natural v1.0 contains 200 naturalized prompts inherited from GapBench rows. It is a for-review artifact until naturalized prompts are audited.

Terminal-Bench-obligation50 is an execution-heavy scaffold derived from public Terminal-Bench task instructions. It is appendix material with labels pending audit, not a Terminal-Bench solving result.

## Metrics

We report success, average cost, oracle cost, minimality regret, over-harnessing, under-harnessing, wrong-harnessing, and redundancy. Success is deterministic verifier pass against expected status and gold obligation/capability coverage.

# 6. Experiments

## Gold-obligation compiler evaluation

Table 1 reports GapBench-1000 under gold obligations. GapHarness reaches 1.00 success, average cost 3.67, and 0.00 regret, matching oracle minimal. Direct answering reaches 0.20 success with 0.74 under-harnessing. Always-full reaches 0.94 success but over-harnesses at 0.94 with average cost 16.00. Tool Router and Difficulty Router show mixed under- and wrong-harnessing failures.

Table 1 proves that the exact compiler-verifier path matches oracle minimal harnesses under human-audited gold obligations. It does not prove open-world LLM profiling or answer-level solving.

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 1000 | 0.20 | 0.00 | 3.67 | -3.67 | 0.00 | 0.74 | 0.00 | 0.00 |
| tool_router | 1000 | 0.34 | 2.10 | 3.67 | -1.57 | 0.11 | 0.60 | 0.42 | 0.06 |
| difficulty_router | 1000 | 0.43 | 3.46 | 3.67 | -0.21 | 0.28 | 0.51 | 0.16 | 0.14 |
| always_full | 1000 | 0.94 | 16.00 | 3.67 | 12.33 | 0.94 | 0.00 | 0.00 | 0.51 |
| gapharness | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

![Cost-success frontier. The figure shows that Always-full buys high success with high cost, while gold GapHarness reaches oracle minimal cost. It does not prove that LLM profiling is fully calibrated.](paper/figures/figure2_cost_success_frontier.png){#fig:frontier width=95%}

![Over, under, and wrong harnessing rates. The figure separates baseline failure modes. It does not claim these rates transfer unchanged to all naturalistic tasks.](paper/figures/figure3_over_under_wrong_bars.png){#fig:ouw width=95%}

## LLM-inferred obligation profiling

Phase 2B evaluates whether an LLM profiler can infer obligations well enough for practical harness synthesis. On held-out test800, the selected LLM GapHarness reaches 0.89 success at 3.59 average cost, outperforming direct, tool-router, and difficulty-router baselines. It remains below the gold oracle, with under-harnessing at 0.09.

Table 2 proves that inferred obligations are useful against simple baselines. It does not prove that the profiler is fully calibrated.

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 800 | 0.20 | 0.00 | 3.69 | -3.69 | 0.00 | 0.74 | 0.00 | 0.00 |
| tool_router | 800 | 0.32 | 1.96 | 3.69 | -1.72 | 0.09 | 0.62 | 0.43 | 0.06 |
| difficulty_router | 800 | 0.41 | 3.22 | 3.69 | -0.47 | 0.26 | 0.53 | 0.15 | 0.13 |
| always_full | 800 | 0.94 | 16.00 | 3.69 | 12.31 | 0.94 | 0.00 | 0.00 | 0.51 |
| gold_oracle_gap_harness | 800 | 1.00 | 3.69 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| selected_llm_gap_harness | 800 | 0.89 | 3.59 | 3.69 | -0.09 | 0.14 | 0.09 | 0.01 | 0.05 |

## Registry-guarded calibration

Phase 2B exposed a systematic failure mode: sandbox/mock/local actions were sometimes lowered into unsupported `real_world_side_effect`. Phase 2C adds a deterministic registry guard that preserves real external side-effect boundaries but removes `real_world_side_effect` when the query explicitly limits action to sandbox/mock/local scope.

On held-out test800, registry guarding improves success from 0.89 to 0.94 and reduces under-harnessing from 0.09 to 0.03. Unsupported false positives fall from 56 to 12. The tradeoff is higher average cost and regret: cost rises from 3.59 to 3.98 and regret from -0.09 to 0.30. This supports a narrow calibration claim: declared registry boundaries can repair a specific profiler failure mode.

Table 3 and Figure 4 prove that registry guarding repairs this sandbox-action unsupported false-positive pattern. They do not prove a general solution to all profiling failures.

| Split | Profiler | N | Success | Avg Cost | Regret | Over | Under | Wrong | Unsupported FP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dev200 | Phase 2B llm_single | 200 | 0.92 | 3.68 | 0.06 | 0.19 | 0.08 | 0.00 | 14 |
| dev200 | Phase 2C registry_guarded | 200 | 0.97 | 4.02 | 0.40 | 0.20 | 0.03 | 0.00 | 4 |
| test800 | Phase 2B selected llm_single | 800 | 0.89 | 3.59 | -0.09 | 0.14 | 0.09 | 0.01 | 56 |
| test800 | Phase 2C registry_guarded | 800 | 0.94 | 3.98 | 0.30 | 0.15 | 0.03 | 0.01 | 12 |

![Registry guard correction. The figure shows reduced unsupported false positives and under-harnessing after a registry guard. It does not prove that registry guarding solves GAIA or all transfer settings.](paper/figures/figure4_registry_guard_unsupported_fp_reduction.png){#fig:guard width=90%}

## Stress tests and negative controls

Registry perturbation removes six key modules one at a time. For each relevant 60-task subset, base registry success is 1.00 and perturbed registry success is 0.00. The dominant missing capabilities match the removed module: `execution`, `source_spans`, `permission`, `diff`, `evidence_sources`, and `contract_check`. This shows that GapHarness does not silently claim support when affordances are absent.

Gold label permutation corrupts 200 supported profiles, while the verifier still checks original human-audited labels. Correct labels yield 1.00 success. Permuted labels reduce success to 0.17, raise under-harnessing to 0.83, and raise wrong-harnessing to 0.79. The permutation generator changes obligations or required capabilities for all 200 corrupted profiles. This is an anti-circularity test, not a realistic noise model.

Negative controls evaluate pure-language and tool-bait prompts. GapHarness gold, LLM, and registry-guarded variants all achieve 1.00 success, 0.00 average cost, and 0.00 over-harnessing. Always-full over-harnesses both categories; Tool Router and Difficulty Router over-harness tool-bait prompts at 0.51.

Table 4 proves three anti-circularity properties: registry affordances matter, labels matter, and tool-like words alone do not trigger GapHarness over-harnessing. It does not model all realistic label noise or all adversarial prompts.

| Removed module | Base | Perturbed | Unsupported | Under | Missing capability |
|---|---:|---:|---:|---:|---|
| python_executor | 1.00 | 0.00 | 1.00 | 1.00 | execution |
| source_span_checker | 1.00 | 0.00 | 1.00 | 1.00 | source_spans |
| permission_gate | 1.00 | 0.00 | 1.00 | 1.00 | permission |
| sandbox_file_editor | 1.00 | 0.00 | 1.00 | 1.00 | diff |
| web_retrieval | 1.00 | 0.00 | 1.00 | 1.00 | evidence_sources |
| contract_verifier | 1.00 | 0.00 | 1.00 | 1.00 | contract_check |

| Condition | N | Success | Regret | Over | Under | Wrong | Verifier Fail |
|---|---:|---:|---:|---:|---:|---:|---:|
| correct gold | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| permuted labels | 200 | 0.17 | 0.24 | 0.55 | 0.83 | 0.79 | 0.83 |

| Category | System | N | Success | Cost | Over |
|---|---|---:|---:|---:|---:|
| pure-lang | GH gold | 100 | 1.00 | 0.00 | 0.00 |
| pure-lang | GH LLM | 100 | 1.00 | 0.00 | 0.00 |
| pure-lang | GH guarded | 100 | 1.00 | 0.00 | 0.00 |
| pure-lang | Always-full | 100 | 1.00 | 16.00 | 1.00 |
| tool-bait | GH gold | 100 | 1.00 | 0.00 | 0.00 |
| tool-bait | GH LLM | 100 | 1.00 | 0.00 | 0.00 |
| tool-bait | GH guarded | 100 | 1.00 | 0.00 | 0.00 |
| tool-bait | Tool Router | 100 | 1.00 | 1.26 | 0.51 |
| tool-bait | Difficulty | 100 | 1.00 | 1.22 | 0.51 |
| tool-bait | Always-full | 100 | 1.00 | 16.00 | 1.00 |

## Transfer and boundary results

GAIA-Transfer gold smoke reaches 1.00 success under gold obligation labels. This confirms that the compiler can process the transfer labels, not that the system solves GAIA.

GAIA registry-guarded reaches 0.56 success with high over-harnessing and under-harnessing. This negative result is useful: the GapBench registry guard targets sandbox/mock action calibration, while GAIA failures are dominated by multimodal, file, evidence, and state-boundary mismatches.

GapBench-Natural review smoke reaches 1.00 success under inherited labels, but should not be treated as final until naturalized prompts are audited.

Table 5 proves that the representation can be applied to transfer artifacts and exposes boundary failures. It does not claim full GAIA solving, Terminal-Bench solving, or final natural-prompt validation.

| Result | Identity | N | Success | Cost | Oracle | Regret | Over | Under |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| GAIA-Transfer gold | transfer smoke | 200 | 1.00 | 1.48 | 1.48 | 0.00 | 0.00 | 0.00 |
| GAIA guarded | limitation | 200 | 0.56 | 5.56 | 1.48 | 4.08 | 0.89 | 0.44 |
| GapBench-Natural | review smoke | 200 | 1.00 | 2.83 | 2.83 | 0.00 | 0.00 | 0.00 |
| Terminal obligation50 | appendix scaffold | 50 | - | - | - | - | - | - |

Boundary notes: GAIA-Transfer evaluates obligation labels only, not GAIA answer solving. GAIA guarded is a limitation result dominated by multimodal, file, evidence, and state-boundary gaps. GapBench-Natural inherits labels pending natural-prompt audit. Terminal obligation50 is not a Terminal-Bench solving result.

# 7. Analysis

The experimental story separates three layers.

First, under gold obligations, minimal harness compilation works. The compiler matches oracle minimal cost and produces interpretable failures when the registry lacks affordances.

Second, LLM profiling is the main practical bottleneck. LLM-inferred obligations outperform simple routers but can under-harness or over-harness depending on calibration. Registry guarding shows that some errors are not random; they can be tied to declared affordance boundaries.

Third, stress tests reduce circularity concerns. Registry perturbation shows the system depends on declared affordances. Label permutation shows labels carry semantic force. Negative controls show the system is not merely responding to tool-like words.

These results support a controlled claim: obligation-first minimal harness synthesis is a useful way to separate profiler errors from compiler/runtime errors.

# 8. Limitations

GapHarness does not solve full GAIA. GAIA-Transfer is obligation-transfer only and does not evaluate answer-level accuracy against GAIA final answers.

GapHarness does not solve Terminal-Bench. Terminal-Bench-obligation50 is a scaffold derived from task instructions, with labels pending audit.

The executor is a deterministic sandbox/mock runtime. It does not perform irreversible file edits, real API calls, payments, emails, deployments, or production changes.

GapBench is controlled and factorial. This is a strength for isolating compiler behavior, but it is not a substitute for large-scale naturalistic agent benchmarks.

The LLM profiler remains imperfect. Registry guarding improves one systematic failure mode, but GAIA-Transfer shows that broader transfer remains limited.

Minimality is registry-relative. Different module registries, cost functions, or dependency models would change the compiled minimal harness.

# 9. Conclusion

GapHarness reframes agent harnessing as two separable problems: identifying the external obligations imposed by a query, and compiling the smallest runtime system that satisfies those obligations. Under human-audited gold obligations, the compiler matches oracle minimal harnesses on GapBench-1000. With LLM-inferred obligations, GapHarness improves over direct and router baselines but exposes calibration tradeoffs. Registry guarding repairs a systematic unsupported false-positive failure. Stress tests show that success depends on declared registry affordances and meaningful obligation labels, while negative controls show that GapHarness avoids tool-bait over-harnessing.

The current evidence supports a workshop/arXiv technical report claim: obligation-first minimal harness synthesis provides a measurable, auditable layer for API-only LLM agents. The next step is not to claim broad open-world solving, but to expand audited transfer benchmarks and improve LLM obligation profiling under the same evidence boundaries.

# References
