# Paper Claims and Boundaries

## Strong Claims Supported by Current Evidence

1. GapHarness validates obligation-first minimal harness compilation under human-audited gold obligations.
2. Under gold obligations, the compiler matches the oracle minimal harness on GapBench-1000.
3. LLM profilers improve over direct, tool-router, and difficulty-router baselines, but introduce calibration tradeoffs.
4. Registry guarding reduces a systematic unsupported false-positive failure where sandbox/mock actions are lowered into unsupported real-world side effects.
5. Registry perturbation shows success depends on declared module affordances.
6. Gold-label permutation shows obligation labels are semantically consequential rather than decorative.
7. Negative controls show GapHarness avoids tool-bait over-harnessing and is more obligation-sensitive than keyword/tool routers.

## Claims Not Supported

1. GapHarness solves full GAIA.
2. GapHarness solves Terminal-Bench.
3. GapHarness handles arbitrary real API side effects.
4. GapHarness proves all real-world tasks are covered.
5. The LLM profiler is fully calibrated.
6. GapBench is a complete real-world benchmark.

## Required Boundary Statements

- Minimality is relative to a declared obligation ontology, module registry, dependency model, and cost function.
- GAIA-Transfer evaluates obligation assignment and harness coverage only; it does not evaluate full answer-level GAIA accuracy.
- GAIA-Transfer registry-guarded run is a limitation result, not a claim of full GAIA solving.
- GapBench-Natural is a for-review smoke artifact until its naturalized prompts are audited.
- Terminal-Bench-obligation50 is an execution-heavy obligation transfer scaffold, not full Terminal-Bench solving.
- The executor is a deterministic sandbox/mock runtime and does not perform irreversible external actions.
