# LLM Tool Router Baseline

Benchmark: `benchmarks/swe_obligation/v1.0/swe_obligation50_llm_safe_view.jsonl`

Subset: `all`

This baseline gives the LLM the module registry and costs, but not the obligation ontology or gold labels.

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_tool_router | 50 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Category Breakdown

| Category | N | Harness Success | Avg Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|
| swe_obligation_transfer | 50 | 1.00 | 12.00 | 0.00 | 0.00 | 0.00 |

Harness success is obligation/capability coverage under the declared registry, not answer-level task correctness.
