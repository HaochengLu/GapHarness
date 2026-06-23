# GapBench-Natural v1.0

This package contains 200 naturalized GapBench examples.

Audit status:

- `gapbench_natural_200_human_audited.jsonl` is project-owner-audited as of 2026-06-23.
- The labels inherit from project-owner-audited GapBench v1.0 source tasks and were rechecked after naturalization.
- The earlier review-stage JSONL was superseded and is not distributed as a final artifact.
- A deterministic cleanup pass removed templated benchmark remnants such as artificial case labels, placeholder product names, and sandbox filename artifacts from the visible user queries.

Composition:

- 40 pure/direct language tasks
- 40 observation/evidence tasks
- 30 execution/computation tasks
- 30 file/workspace inspection tasks
- 20 sandbox action/permission tasks
- 20 ambiguous/unsupported tasks
- 20 mixed multi-obligation tasks

Use this dataset to test whether the obligation calculus transfers beyond templated controlled queries. It is not an open-world answer-correctness benchmark.
