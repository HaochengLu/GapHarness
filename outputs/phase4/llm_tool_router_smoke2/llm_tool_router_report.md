# Phase 4 LLM Tool Router Baseline

Benchmark: `benchmarks/gapbench/v1.0/splits/test800.jsonl`

Subset: `all`

This baseline gives the LLM the module registry and costs, but not the obligation ontology or gold labels.

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_tool_router | 2 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Category Breakdown

| Category | N | Harness Success | Avg Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|
| ambiguous | 1 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| unsupported | 1 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Harness success is obligation/capability coverage under the declared registry, not answer-level task correctness.
