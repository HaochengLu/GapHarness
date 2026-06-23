# LLM Tool Router Baseline

Benchmark: `benchmarks/harness_challenge/v1.0/harness_challenge200_author_reviewed.jsonl`

Subset: `all`

This baseline gives the LLM the module registry and costs, but not the obligation ontology or gold labels.

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_tool_router | 200 | 0.65 | 2.60 | 3.48 | -0.88 | 0.04 | 0.01 | 0.35 | 0.28 |

## Category Breakdown

| Category | N | Harness Success | Avg Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|
| hard_tool_bait | 30 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| minimal_pair | 50 | 0.54 | 2.30 | 0.04 | 0.46 | 0.42 |
| real_source_paraphrase | 20 | 0.35 | 4.20 | 0.00 | 0.65 | 0.00 |
| registry_absence | 30 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sandbox_vs_real_side_effect | 40 | 0.50 | 5.00 | 0.00 | 0.50 | 0.50 |
| verification_evidence_trap | 30 | 0.50 | 4.00 | 0.00 | 0.50 | 0.50 |

Harness success is obligation/capability coverage under the declared registry, not answer-level task correctness.
