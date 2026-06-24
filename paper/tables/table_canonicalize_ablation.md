# Table: Canonicalize No-Lexical Ablation (GapBench test800 stratified subset)

Same raw LLM profile (model `gpt-5.4-mini`, profiler `llm_single`); two normalizations.
FULL = shipped `canonicalize_profile`. NO-LEXICAL = registry normalization
with the two query-keyword obligation injections removed (Execution and
Verification lexical triggers). DELTA = FULL - NO-LEXICAL.

| Pipeline | N | Harness Success | Under | Over | Obl Micro-P | Obl Micro-R | Obl Micro-F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| FULL (shipped) | 228 | 0.838 | 0.070 | 0.079 | 0.880 | 0.935 | 0.907 |
| NO-LEXICAL | 228 | 0.798 | 0.110 | 0.053 | 0.880 | 0.935 | 0.907 |
| DELTA (FULL - NO-LEXICAL) | - | +0.039 | -0.039 | +0.026 | +0.000 | +0.000 | +0.000 |

Interpretation boundary: held-out obligation/harness coverage on a seeded
stratified subset, not open-world answer accuracy.
