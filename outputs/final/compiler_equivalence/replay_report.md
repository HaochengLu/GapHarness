# Compiler Equivalence Replay

Replay checks whether the optimized exact compiler preserves frozen harness outputs. Certificates are new metadata and are ignored for equality.

Only rows where the compiler is genuinely re-invoked (a stored profiler profile, or a `gapharness` system re-profiled from gold) count toward compiler equivalence. Reconstructed baseline rows and router rows never call `compile_minimal_harness` and are labelled and excluded from the equivalence N.

## Honest coverage

| Replay kind | Rows | Counts toward equivalence? |
|---|---:|---|
| compiler_reinvoked | 4020 | yes |
| reconstructed_baseline | 10100 | no (baseline policy) |
| router_skipped | 200 | no (router, compiler skipped) |
| missing_file | 0 | no |

**Honest compiler-equivalence N = 4020** (rows where the compiler was genuinely re-run).

## Per-experiment (genuine compiler rows only)

Columns count only the genuinely re-invoked subset of each experiment; `Genuine N` is that subset.

| Frozen Experiment | Rows | Genuine N | Status changed | Harness changed | Cost changed | Avg Nodes | Avg Dominated |
|---|---:|---:|---:|---:|---:|---:|---:|
| gapbench1000_gold | 6000 | 1000 | 0 | 0 | 0 | 103.4 | 0.0 |
| harness_challenge_gold | 1200 | 200 | 0 | 0 | 0 | 42.4 | 0.0 |
| harness_challenge_guarded | 200 | 200 | 0 | 0 | 0 | 87.0 | 0.0 |
| harness_challenge_llm | 200 | 200 | 0 | 0 | 0 | 82.0 | 0.0 |
| harness_challenge_router | 200 | 0 | 0 | 0 | 0 | 0.0 | 0.0 |
| harness_exec20 | 120 | 20 | 0 | 0 | 0 | 21.0 | 0.0 |
| test800_llm | 5600 | 1600 | 0 | 0 | 0 | 95.8 | 0.0 |
| test800_registry_guarded | 800 | 800 | 0 | 0 | 0 | 93.2 | 0.0 |

## Dominance Track (dominance-bearing registry)

A separate registry (`gapharness.dominance_registry`) in which several modules are strictly dominated, so dominance pruning fires. Each profile is checked against an independent inline brute-force reference over the same registry.

Declared dominated pairs (dominated <- dominator): exec_slow<-exec_fast, retriever_basic<-retriever_pro, state_basic<-state_pro

| Profile | Opt status/modules/cost | Ref status/modules/cost | Match | Dominated | Nodes |
|---|---|---|---|---:|---:|
| direct_answer | supported//0 | supported//0 | ok | 0 | 0 |
| observation_only | supported/retriever_pro/3 | supported/retriever_pro/3 | ok | 3 | 15 |
| observation_fresh_index | supported/retriever_pro/3 | supported/retriever_pro/3 | ok | 3 | 15 |
| observation_plus_span_verification | supported/retriever_pro,span_verifier/4 | supported/retriever_pro,span_verifier/4 | ok | 3 | 23 |
| execution_only | supported/exec_fast/2 | supported/exec_fast/2 | ok | 3 | 7 |
| execution_plus_contract | supported/contract_verifier,exec_fast/3 | supported/contract_verifier,exec_fast/3 | ok | 3 | 5 |
| state_only | supported/state_pro/1 | supported/state_pro/1 | ok | 3 | 47 |
| full_cover | supported/contract_verifier,exec_fast,retriever_pro,state_pro/7 | supported/contract_verifier,exec_fast,retriever_pro,state_pro/7 | ok | 3 | 13 |
| clarify | clarify//0 | clarify//0 | ok | 0 | 0 |
| unsupported_capability | unsupported//0 | unsupported//0 | ok | 3 | 1 |

Mismatches vs brute force: **0**. Max dominated removed: **3**. Max search nodes: **47**.

## Changed Rows (genuine compiler rows only)

No status, module, or cost changes were observed among genuinely recompiled rows.
