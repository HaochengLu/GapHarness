# LLM Tool Router Baseline

Benchmark: `benchmarks/gapbench/v1.0/splits/dev200.jsonl`

Subset: `all`

This baseline gives the LLM the module registry and costs, but not the obligation ontology or gold labels.

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_tool_router | 200 | 0.79 | 3.35 | 3.62 | -0.27 | 0.11 | 0.11 | 0.21 | 0.20 |

## Category Breakdown

| Category | N | Harness Success | Avg Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|
| ambiguous | 6 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| complex_obligation | 14 | 0.50 | 9.21 | 0.00 | 0.50 | 0.50 |
| pairwise_obligation | 52 | 0.65 | 3.71 | 0.12 | 0.35 | 0.35 |
| pure_language_negative | 20 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| single_obligation | 36 | 0.94 | 2.25 | 0.25 | 0.06 | 0.00 |
| tool_bait | 20 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| triple_obligation | 46 | 0.65 | 5.83 | 0.15 | 0.35 | 0.35 |
| unsupported | 6 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Harness success is obligation/capability coverage under the declared registry, not answer-level task correctness.
