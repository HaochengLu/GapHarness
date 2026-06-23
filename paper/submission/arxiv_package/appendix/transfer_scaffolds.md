# Appendix: Transfer and Scaffold Artifacts

## GAIA-Transfer

GAIA-Transfer v1.0 contains 200 project-owner-audited obligation-transfer rows. It is used to evaluate obligation labeling and harness selection only.

Boundary:

- It is not a full GAIA answer-level solving benchmark.
- The registry-guarded GAIA run is reported as a limitation result.

## GapBench-Natural

GapBench-Natural v1.0 contains 200 project-owner-audited naturalized prompts sampled from audited GapBench source rows.

Boundary:

- It is project-owner-audited as of 2026-06-23.
- It remains a naturalized derivative of GapBench source rows, not an independent open-world answer-correctness benchmark.

## SWE-Obligation-50

SWE-Obligation-50 v1.0 contains 50 project-owner-audited obligation-transfer rows derived from public SWE-bench Lite task descriptions and test metadata.

Boundary:

- It uses real SWE-bench Lite source rows.
- It evaluates obligation/capability coverage only.
- It is not repository checkout, patch generation, SWE-bench test execution, or pass@1.
- `swe_obligation50_llm_safe_view.jsonl` is a shortened API diagnostic view for LLM profiler/router calls, not a replacement for the project-owner-audited source view.

## Terminal-Bench-obligation50

Terminal-Bench-obligation50 is an execution-heavy obligation transfer scaffold derived from public Terminal-Bench task instructions.

Boundary:

- `gold_source` is `generated_for_human_review_pending_audit`.
- It is not human-audited gold.
- It is not a Terminal-Bench solve result.
- It should remain appendix or future-work material unless audited.
