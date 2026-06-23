# Paper Claims and Boundaries

## Strong Claims Supported by Current Evidence

1. GapHarness validates obligation-first minimal harness compilation under project-owner-audited gold obligations.
2. Under gold obligations, the compiler matches the oracle minimal harness on GapBench-1000.
3. LLM profilers improve over direct, deterministic routers, and the LLM Tool Router baseline on held-out harness coverage, but introduce calibration tradeoffs.
4. Registry guarding reduces a systematic unsupported false-positive failure where sandbox/mock actions are lowered into unsupported real-world side effects; this is post-hoc registry-boundary calibration.
5. Registry perturbation shows success depends on declared module affordances.
6. Gold-label permutation shows obligation labels are semantically consequential rather than decorative.
7. Negative controls show GapHarness avoids tool-bait over-harnessing and is more obligation-sensitive than keyword/tool routers.
8. Secondary adversarial audit gives an additional consistency check, but it is not human inter-annotator agreement.
9. GapBench-Natural-200 is project-owner-audited after naturalization, while still being GapBench-derived.
10. SWE-Obligation-50 provides real-source obligation-transfer evidence from SWE-bench Lite descriptions, but does not claim patch solving or pass@1.
11. Diagnostic-feedback baselines show that verifier-feedback repair and ReAct-style policies can recover coverage, while GapHarness provides one-shot registry-relative certificates when a profile is available.
12. GapHarness-Repair shows that verifier diagnostics can be converted into profile patches and recompiled, recovering coverage while preserving registry-relative certificates.
13. SWE-HarnessExec-50 provides a larger provided-patch sandbox pytest trace check, but remains fixture-based rather than real-repository checkout or SWE-bench pass@1.

## Claims Not Supported

1. GapHarness solves full GAIA.
2. GapHarness solves Terminal-Bench.
3. GapHarness handles arbitrary real API side effects.
4. GapHarness proves all real-world tasks are covered.
5. The LLM profiler is fully calibrated.
6. GapBench is a complete real-world benchmark.
7. GapHarness is categorically better than LangGraph, AutoGen, or any agent framework as a substrate.

## Required Boundary Statements

- Minimality is relative to a declared obligation ontology, module registry, dependency model, and cost function.
- Harness success is obligation/capability coverage, not answer-level correctness.
- Cost delta can be negative; excess cost is the non-negative over-cost quantity.
- Excess cost is averaged per-task positive excess, not max of aggregate mean delta.
- GAIA-Transfer evaluates obligation assignment and harness coverage only; it does not evaluate full answer-level GAIA accuracy.
- GAIA-Transfer registry-guarded run is a limitation result, not a claim of full GAIA solving.
- GapBench-Natural is project-owner-audited, but remains a naturalized derivative of GapBench source rows.
- SWE-Obligation-50 uses real SWE-bench Lite issue descriptions and test metadata, but is obligation-transfer only.
- SWE-HarnessExec-50 uses generated local fixtures with provided patches; it is not real-repository checkout, model-generated repair, or SWE-bench pass@1.
- Terminal-Bench-obligation50 is an execution-heavy obligation transfer scaffold, not full Terminal-Bench solving.
- The executor is a deterministic sandbox/mock runtime and does not perform irreversible external actions.
- Diagnostic-feedback baselines are policy baselines over the same declared registry, executor, verifier, model, and costs; they are not claims about whole frameworks.
- Verifier-repair and ReAct-style baselines receive verifier feedback after failed routes and do not emit GapHarness-style minimality certificates.
- GapHarness-Repair receives verifier diagnostics after failed one-shot compilation, so it is a feedback-assisted upper-bound variant rather than a one-shot profiler result.
