# LLM Tool Router Baseline

Benchmark: `benchmarks/gapbench/v1.0/splits/test800.jsonl`

Subset: `all`

This baseline gives the LLM the module registry and costs, but not the obligation ontology or gold labels.

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_tool_router | 800 | 0.80 | 3.51 | 3.69 | -0.18 | 0.13 | 0.12 | 0.20 | 0.17 |

## Category Breakdown

| Category | N | Harness Success | Avg Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|
| ambiguous | 24 | 0.92 | 0.00 | 0.00 | 0.00 | 0.00 |
| complex_obligation | 56 | 0.70 | 9.52 | 0.07 | 0.30 | 0.30 |
| pairwise_obligation | 208 | 0.73 | 4.06 | 0.18 | 0.27 | 0.27 |
| pure_language_negative | 80 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| single_obligation | 144 | 0.86 | 2.02 | 0.15 | 0.14 | 0.00 |
| tool_bait | 80 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| triple_obligation | 184 | 0.66 | 6.20 | 0.17 | 0.34 | 0.34 |
| unsupported | 24 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Harness success is obligation/capability coverage under the declared registry, not answer-level task correctness.
