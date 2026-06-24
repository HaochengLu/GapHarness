# Canonicalize No-Lexical Ablation Report

## What was measured

We compare two evaluation pipelines built from the SAME cached raw LLM
profile (model `gpt-5.4-mini`, profiler `llm_single`, parsed with
`_profile_from_payload` BEFORE any canonicalization):

- **FULL** = `canonicalize_profile(raw, query)` -- the shipped path.
- **NO-LEXICAL** = a local registry-vocabulary normalization of the same
  raw profile with the two query-keyword obligation injections removed.

## Exactly which lexical injections were removed

NO-LEXICAL re-implements canonicalization locally (it does not modify
`gapharness/llm_profiler.py`) and removes ONLY these two query-keyword
branches, which add an obligation the LLM profiler did not assert:

1. `_query_requires_execution(text)` -> would add the `Execution`
   obligation and `execution` capability (triggers: "calculate exactly",
   "compute exactly", "run test(s)", "lint", "schema validation", or the
   arithmetic regex `\d+ [*+/%-] \d+`).
2. `_query_requires_verification(text)` -> would add the `Verification`
   obligation and `contract_check` capability (triggers: "validate",
   "contract", "verify", "with sources", "cite", "source span").

It additionally makes the one query-keyword capability *choice* keyword-free:
for an already-asserted `Observation`, FULL picks `workspace_inspection` vs
`evidence_sources` by query markers; NO-LEXICAL defaults to `evidence_sources`.

All other branches are KEPT identically because they are registry-entailment
closures gated only on an obligation the profiler already asserted (Action ->
State/Control/diff/sandbox_action/permission; Control -> permission; State ->
durable_state; Observation -> evidence source; Execution -> execution;
Verification -> matching evidence/log/diff/contract capability). The
`clarification_needed` drop is identical in both pipelines, so the only
measured difference is the lexical obligation/capability injection.

## Subset

- Source: `benchmarks/gapbench/v1.0/splits/test800.jsonl`.
- Deterministic stratified subset, seed `20260624`, up to 30 rows per category.
- N = 228 rows across 8 categories.
- Per-category counts: ambiguous=24, complex_obligation=30, pairwise_obligation=30, pure_language_negative=30, single_obligation=30, tool_bait=30, triple_obligation=30, unsupported=24.

## Results

| Pipeline | N | Harness Success | Under | Over | Obl Micro-F1 |
|---|---:|---:|---:|---:|---:|
| FULL (shipped) | 228 | 0.838 | 0.070 | 0.079 | 0.907 |
| NO-LEXICAL | 228 | 0.798 | 0.110 | 0.053 | 0.907 |
| DELTA (FULL - NO-LEXICAL) | - | +0.039 | -0.039 | +0.026 | +0.000 |

Obligation micro-counts (FULL): tp=486 fp=66 fn=34. (NO-LEXICAL): tp=486 fp=66 fn=34.

## How often the removed lexical branches fired

- Rows where FULL and NO-LEXICAL profiles differ: 12 / 228.
- Rows where FULL's lexical trigger added the `Execution` obligation: 0.
- Rows where FULL's lexical trigger added the `Verification` obligation: 0.
- Rows where FULL's lexical trigger added the `execution` capability: 0.
- Rows where FULL's lexical trigger added the `contract_check` capability: 12.
- Rows where the `Observation` capability choice differs: 0.

Mechanism note: on this subset the lexical triggers never add a brand-new
*obligation* the profiler missed (obligation micro-F1 is identical, 0.907 in
both pipelines). The entire harness-success delta comes from the
`_query_requires_verification` branch supplying the `contract_check`
*capability* on verification-flavored queries whose gold requires it; the
underlying `Verification` obligation was already asserted by the model.

## Honest interpretation

The delta is small: held-out harness coverage is largely NOT due to the lexical normalization aid. The lexical triggers move coverage by only +0.039, supporting the framing that the language model (not a keyword router) carries the obligation inference.

## Replayability

Raw profiles are cached under `outputs/ablation/raw/`. Re-running with
`--offline` is API-free and regenerates this report and the table
deterministically.
