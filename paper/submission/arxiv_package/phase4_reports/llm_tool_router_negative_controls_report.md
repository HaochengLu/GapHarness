# LLM Tool Router Baseline

Benchmark: `benchmarks/gapbench/v1.0/gapbench_1000_human_audited.jsonl`

Subset: `negative`

This baseline gives the LLM the module registry and costs, but not the obligation ontology or gold labels.

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_tool_router | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Category Breakdown

| Category | N | Harness Success | Avg Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|
| pure_language_negative | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_bait | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Harness success is obligation/capability coverage under the declared registry, not answer-level task correctness.
