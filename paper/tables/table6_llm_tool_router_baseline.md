# Table 6. LLM Tool Router Baseline

The LLM Tool Router sees registry modules and costs, but not obligation labels or gold labels.

| System/Subsample | N | Harness Success | Declared Cost | Oracle Declared Cost | Cost Delta | Excess Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_tool_router dev200 | 200 | 0.79 | 3.35 | 3.62 | -0.27 | 0.11 | 0.11 | 0.21 | 0.20 |
| llm_tool_router test800 | 800 | 0.80 | 3.51 | 3.69 | -0.18 | 0.13 | 0.12 | 0.20 | 0.17 |
| router pure_language_negative | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| router tool_bait | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| llm_tool_router SWE-Obligation-50 | 50 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
