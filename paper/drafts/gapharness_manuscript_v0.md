# GapHarness: Obligation-First Minimal Harness Synthesis for API-Only LLM Agents

## Abstract

API-only LLM agents increasingly rely on external runtimes for retrieval, code execution, state management, action, control, and verification. Existing agent routers often choose tools directly, which can conflate two separable questions: what external obligations a user query imposes, and what smallest runtime harness can satisfy those obligations. We introduce GapHarness, a research system that formulates agent harnessing as obligation inference followed by minimal runtime compilation. Given an obligation profile and a declared module registry, GapHarness compiles the lowest-cost module subset that covers required obligations and capabilities, executes a deterministic sandbox loop, and verifies sufficiency and relative minimality.

We define an obligation ontology covering Observation, Execution, State, Action, Control, and Verification, and introduce metrics for over-harnessing, under-harnessing, wrong-harnessing, minimality regret, and redundancy. On the 1000-task human-audited GapBench controlled benchmark, GapHarness matches the oracle minimal harness under gold obligations, while direct and router baselines exhibit distinct under- and over-harnessing failures. With LLM-inferred obligations on held-out test800, GapHarness reaches 0.89 success, outperforming direct and router baselines while exposing a calibration gap. A registry-guarded profiler reduces unsupported false positives from 56 to 12 and improves held-out success to 0.94, at the cost of higher minimality regret. Stress tests show that success depends on declared registry affordances and meaningful obligation labels; negative controls show that GapHarness avoids tool-bait over-harnessing. Transfer runs on GAIA-Transfer and GapBench-Natural identify boundary conditions rather than claiming full open-world task solving.

## 1. Introduction

LLM agents are usually evaluated as end-to-end systems: a model receives a request, selects tools, acts in an environment, and produces an answer. This framing is useful, but it hides a smaller technical problem that appears whenever an API-only model must decide what runtime support is needed. A user request may require observation beyond the prompt, deterministic execution, durable state, sandbox action, control over risky operations, or independent verification. These are obligations, not tools. A tool router that reacts to keywords may over-call tools when the user explicitly requests no tools, and it may under-call tools when a warranted answer requires evidence, state, or verification that is not obvious from surface wording.

This paper studies a narrower question:

> Given a user query, an obligation profile, and a declared registry of runtime modules, can we compile the minimal harness that satisfies the external obligations required for a warranted answer or action?

GapHarness separates the problem into two stages. First, a profiler infers an obligation profile: obligations, required capabilities, output contracts, risk level, and unsupported or clarification conditions. Second, an exact compiler searches a declared module registry for the lowest-cost module subset that covers the obligations and capabilities. This separation makes failure interpretable. If a registry does not contain an affordance, the system should return unsupported rather than hallucinating support. If the profiler over- or under-infers obligations, the verifier should expose measurable over-harnessing, under-harnessing, or wrong-harnessing.

The goal is not to build another general-purpose agent framework. The goal is to make harness synthesis measurable and auditable. Minimality is relative to a declared ontology, registry, dependency model, and cost function. This is a controlled technical claim, not a claim of universal agent optimality.

### Contributions

1. We formulate agent harnessing as obligation inference plus minimal runtime compilation.
2. We implement GapHarness, an API-only compiler from obligations to minimal harness modules.
3. We introduce minimal-sufficiency metrics: over-harnessing, under-harnessing, wrong-harnessing, minimality regret, and redundancy.
4. We evaluate GapHarness on GapBench-1000, LLM-inferred profiler settings, registry-guarded calibration, transfer subsets, and anti-circularity stress tests.

## 2. Related Work

This draft intentionally separates technical claims from citation completion. A final citation pass should add verified references for tool-using LLM agents, retrieval-augmented generation, code execution agents, agent benchmarks, and workflow/graph runtimes.

Relevant areas include:

- Tool-using LLM agents and reasoning-action prompting, including approaches that interleave model reasoning with external actions.
- Retrieval-augmented generation and evidence-grounded answering, which motivate Observation and Verification obligations.
- Code execution and program-aided reasoning, which motivate Execution and execution-log verification.
- Agent benchmarks such as GAIA and terminal-environment benchmarks, which expose open-world and execution-heavy task demands.
- Workflow and graph-based agent runtimes, which provide practical module orchestration but do not by themselves define minimal obligation coverage.
- Safety, control, and verification work on permissions, irreversible actions, and sandboxed execution.

GapHarness is complementary to these directions. It does not propose a new foundation model or a new open-world benchmark. It studies a compiler-like layer between obligation inference and runtime module selection.

## 3. Problem Formulation

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

## 4. GapHarness

GapHarness contains five components.

The profiler maps a query to an obligation profile. The current system supports gold profiles, heuristic profiles, LLM-inferred profiles, and a registry-guarded LLM profile variant. The gold profiler is used to isolate compiler behavior. The LLM profiler is used to measure practical inference quality.

The registry declares available modules. The MVP registry includes web retrieval, source-span checking, Python execution, execution-log checking, workspace inspection, state storage, sandbox file editing, permission gating, contract verification, and trace recording.

The compiler performs exact search over registry subsets and selects the lowest-cost valid harness. It returns direct-answer, supported, clarify, or unsupported harness status.

The executor is a deterministic sandbox/mock runtime. It records traces but does not perform irreversible external side effects.

The verifier checks sufficiency against benchmark gold labels and computes drop-one minimality reports.

Figure 1 shows the pipeline.

## 5. Benchmarks and Metrics

### GapBench

GapBench v1.0 is a 1000-row controlled benchmark designed to isolate obligation coverage and minimal harness compilation. It contains human-audited labels for obligations, required capabilities, oracle minimal harnesses, expected status, success checker, risk level, and provenance. The benchmark includes dev200 and test800 splits.

GapBench is controlled and factorial. It is not a complete real-world benchmark. Its purpose is to make the compiler and verifier problem measurable.

### Transfer and Review Sets

GAIA-Transfer v1.0 contains 200 GAIA-derived obligation-transfer rows. It evaluates obligation assignment and harness selection only; it is not a full GAIA answer-level benchmark.

GapBench-Natural v1.0 contains 200 naturalized prompts inherited from GapBench rows. It is a for-review artifact until naturalized prompts are audited.

Terminal-Bench-obligation50 is an execution-heavy scaffold derived from public Terminal-Bench task instructions. It is appendix material with labels pending audit, not a Terminal-Bench solving result.

### Metrics

We report success, average cost, oracle cost, minimality regret, over-harnessing, under-harnessing, wrong-harnessing, and redundancy. Success is deterministic verifier pass against expected status and gold obligation/capability coverage.

## 6. Experiments

### Gold-Obligation Compiler Evaluation

Table 1 reports GapBench-1000 under gold obligations. GapHarness reaches 1.00 success, average cost 3.67, and 0.00 regret, matching oracle minimal. Direct answering reaches 0.20 success with 0.74 under-harnessing. Always-full reaches 0.94 success but over-harnesses at 0.94 with average cost 16.00. Tool Router and Difficulty Router show mixed under- and wrong-harnessing failures.

This result validates the compiler-verifier path under human-audited obligations. It does not by itself validate open-world profiling.

### LLM-Inferred Obligation Profiling

Phase 2B evaluates whether an LLM profiler can infer obligations well enough for practical harness synthesis. On held-out test800, the selected LLM GapHarness reaches 0.89 success at 3.59 average cost, outperforming direct, tool-router, and difficulty-router baselines. It remains below the gold oracle, with under-harnessing at 0.09.

This shows that LLM-inferred obligations are useful but not fully calibrated.

### Registry-Guarded Calibration

Phase 2B exposed a systematic failure mode: sandbox/mock/local actions were sometimes lowered into unsupported `real_world_side_effect`. Phase 2C adds a deterministic registry guard that preserves real external side-effect boundaries but removes `real_world_side_effect` when the query explicitly limits action to sandbox/mock/local scope.

On held-out test800, registry guarding improves success from 0.89 to 0.94 and reduces under-harnessing from 0.09 to 0.03. Unsupported false positives fall from 56 to 12. The tradeoff is higher average cost and regret: cost rises from 3.59 to 3.98 and regret from -0.09 to 0.30. This supports a narrow calibration claim: declared registry boundaries can repair a specific profiler failure mode.

### Stress Tests

Registry perturbation removes six key modules one at a time. For each relevant 60-task subset, base registry success is 1.00 and perturbed registry success is 0.00. The dominant missing capabilities match the removed module: `execution`, `source_spans`, `permission`, `diff`, `evidence_sources`, and `contract_check`. This shows that GapHarness does not silently claim support when affordances are absent.

Gold label permutation corrupts 200 supported profiles, while the verifier still checks original human-audited labels. Correct labels yield 1.00 success. Permuted labels reduce success to 0.17, raise under-harnessing to 0.83, and raise wrong-harnessing to 0.79. The permutation generator changes obligations or required capabilities for all 200 corrupted profiles. This is an anti-circularity test, not a realistic noise model.

Negative controls evaluate pure-language and tool-bait prompts. GapHarness gold, LLM, and registry-guarded variants all achieve 1.00 success, 0.00 average cost, and 0.00 over-harnessing. Always-full over-harnesses both categories; Tool Router and Difficulty Router over-harness tool-bait prompts at 0.51.

### Transfer and Boundary Results

GAIA-Transfer gold smoke reaches 1.00 success under gold obligation labels. This confirms that the compiler can process the transfer labels, not that the system solves GAIA.

GAIA registry-guarded reaches 0.56 success with high over-harnessing and under-harnessing. This negative result is useful: the GapBench registry guard targets sandbox/mock action calibration, while GAIA failures are dominated by multimodal, file, evidence, and state-boundary mismatches.

GapBench-Natural review smoke reaches 1.00 success under inherited labels, but should not be treated as final until naturalized prompts are audited.

## 7. Analysis

The experimental story separates three layers.

First, under gold obligations, minimal harness compilation works. The compiler matches oracle minimal cost and produces interpretable failures when the registry lacks affordances.

Second, LLM profiling is the main practical bottleneck. LLM-inferred obligations outperform simple routers but can under-harness or over-harness depending on calibration. Registry guarding shows that some errors are not random; they can be tied to declared affordance boundaries.

Third, stress tests reduce circularity concerns. Registry perturbation shows the system depends on declared affordances. Label permutation shows labels carry semantic force. Negative controls show the system is not merely responding to tool-like words.

These results support a controlled claim: obligation-first minimal harness synthesis is a useful way to separate profiler errors from compiler/runtime errors.

## 8. Limitations

GapHarness does not solve full GAIA. GAIA-Transfer is obligation-transfer only and does not evaluate answer-level accuracy against GAIA final answers.

GapHarness does not solve Terminal-Bench. Terminal-Bench-obligation50 is a scaffold derived from task instructions, with labels pending audit.

The executor is a deterministic sandbox/mock runtime. It does not perform irreversible file edits, real API calls, payments, emails, deployments, or production changes.

GapBench is controlled and factorial. This is a strength for isolating compiler behavior, but it is not a substitute for large-scale naturalistic agent benchmarks.

The LLM profiler remains imperfect. Registry guarding improves one systematic failure mode, but GAIA-Transfer shows that broader transfer remains limited.

Minimality is registry-relative. Different module registries, cost functions, or dependency models would change the compiled minimal harness.

## 9. Conclusion

GapHarness reframes agent harnessing as two separable problems: identifying the external obligations imposed by a query, and compiling the smallest runtime system that satisfies those obligations. Under human-audited gold obligations, the compiler matches oracle minimal harnesses on GapBench-1000. With LLM-inferred obligations, GapHarness improves over direct and router baselines but exposes calibration tradeoffs. Registry guarding repairs a systematic unsupported false-positive failure. Stress tests show that success depends on declared registry affordances and meaningful obligation labels, while negative controls show that GapHarness avoids tool-bait over-harnessing.

The current evidence supports a workshop/arXiv technical report claim: obligation-first minimal harness synthesis provides a measurable, auditable layer for API-only LLM agents. The next step is not to claim broad open-world solving, but to expand audited transfer benchmarks and improve LLM obligation profiling under the same evidence boundaries.

## Tables and Figures

Primary tables:

- `paper/tables/table1_gapbench1000_gold.md`
- `paper/tables/table2_phase2b_llm_heldout.md`
- `paper/tables/table3_phase2c_registry_guarded.md`
- `paper/tables/table4_phase2d_stress_tests.md`
- `paper/tables/table5_transfer_boundary.md`

Primary figures:

- Figure 1: `paper/figures/figure1_pipeline.svg`
- Figure 2: `paper/figures/figure2_cost_success_frontier.svg`
- Figure 3: `paper/figures/figure3_over_under_wrong_bars.svg`
- Figure 4: `paper/figures/figure4_registry_guard_unsupported_fp_reduction.svg`

## Citation TODO

Before submission, add verified citations for tool-using LLM agents, retrieval-augmented generation, code execution agents, GAIA, Terminal-Bench, workflow/graph agent runtimes, and verification/safety work. Do not submit this draft with unverified citation placeholders.
