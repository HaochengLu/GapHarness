# Privileged-Resource Cost of Coverage (feedback-level analysis)

Sourced entirely from cached, deterministic feedback-cost replay rows (`outputs/final/feedback_cost/feedback_cost_rows.jsonl`), themselves replayed from frozen results. No new API calls and no hardcoded certificate bonus: every column below is read off the cached rows or counted from objective per-row facts. The `Certificate` column is an OBSERVED property (GapHarness emits a system-generated, checkable witness; the baselines emit none), not an assumption about its utility.

## Headline: MEDIUM, non-leaky feedback (missing obligation family)

Medium feedback discloses only which obligation FAMILIES are missing. It does not leak the gold status or the gold required capabilities, so it is the fair operating point. At this point the baselines reach essentially the same coverage as GapHarness-Repair, so the honest claim is that **equal coverage is reachable without a certificate** -- the remaining differences are that the baselines produce no checkable witness and, on the harder HarnessChallenge split, buy their parity with more under/wrong-harness routes.

| System | Dataset | Feedback (leakage) | Harness Success | Excess cost | Over-harness | LLM calls | Verifier/repair rounds | Oracle-status accesses | Certificate |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Router-Repair | GapBench test800 | medium (missing obligation family; non-leaky) | 0.93 | 0.16 | 0.14 | 1.00 | 2.20 | 0.00 | no |
| ReAct | GapBench test800 | medium (missing obligation family; non-leaky) | 0.93 | 0.16 | 0.14 | 1.00 | 2.20 | 0.00 | no |
| GapHarness-Repair | GapBench test800 | medium (missing obligation family; non-leaky) | 0.91 | 0.37 | 0.14 | 1.00 | 2.11 | 0.00 | yes |
| Router-Repair | HarnessChallenge-200 | medium (missing obligation family; non-leaky) | 0.79 | 0.04 | 0.01 | 1.00 | 2.35 | 0.00 | no |
| ReAct | HarnessChallenge-200 | medium (missing obligation family; non-leaky) | 0.79 | 0.04 | 0.01 | 1.00 | 2.35 | 0.00 | no |
| GapHarness-Repair | HarnessChallenge-200 | medium (missing obligation family; non-leaky) | 0.79 | 0.98 | 0.05 | 1.00 | 2.31 | 0.00 | yes |

## Full grid (weak / medium / strong)

Weak (pass/fail) is non-leaky but uninformative: the baselines reach ~1.00 only by adding everything, paying a large Excess cost and still emitting no certificate. Strong (missing capability/status) LEAKS the gold status and gold required capabilities into the repair loop; the 1.00 success there is an oracle-leakage UPPER BOUND, and the `Oracle-status` column counts exactly those gold consultations.

| System | Dataset | Feedback (leakage) | Harness Success | Excess cost | Over-harness | LLM calls | Verifier/repair rounds | Oracle-status accesses | Certificate |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Router-Repair | GapBench test800 | weak (pass/fail; non-leaky) | 1.00 | 2.18 | 0.31 | 1.00 | 1.20 | 0.00 | no |
| ReAct | GapBench test800 | weak (pass/fail; non-leaky) | 1.00 | 2.18 | 0.31 | 1.00 | 1.20 | 0.00 | no |
| GapHarness-Repair | GapBench test800 | weak (pass/fail; non-leaky) | 0.89 | 0.37 | 0.14 | 1.00 | 1.11 | 0.00 | no |
| Router-Repair | GapBench test800 | medium (missing obligation family; non-leaky) | 0.93 | 0.16 | 0.14 | 1.00 | 2.20 | 0.00 | no |
| ReAct | GapBench test800 | medium (missing obligation family; non-leaky) | 0.93 | 0.16 | 0.14 | 1.00 | 2.20 | 0.00 | no |
| GapHarness-Repair | GapBench test800 | medium (missing obligation family; non-leaky) | 0.91 | 0.37 | 0.14 | 1.00 | 2.11 | 0.00 | yes |
| Router-Repair | GapBench test800 | strong (missing capability/status; oracle-leakage upper bound) | 1.00 | 0.13 | 0.12 | 1.00 | 2.20 | 0.20 | no |
| ReAct | GapBench test800 | strong (missing capability/status; oracle-leakage upper bound) | 1.00 | 0.13 | 0.12 | 1.00 | 2.20 | 0.20 | no |
| GapHarness-Repair | GapBench test800 | strong (missing capability/status; oracle-leakage upper bound) | 1.00 | 0.25 | 0.14 | 1.00 | 2.11 | 0.11 | yes |
| Router-Repair | HarnessChallenge-200 | weak (pass/fail; non-leaky) | 1.00 | 3.08 | 0.36 | 1.00 | 1.35 | 0.00 | no |
| ReAct | HarnessChallenge-200 | weak (pass/fail; non-leaky) | 1.00 | 3.08 | 0.36 | 1.00 | 1.35 | 0.00 | no |
| GapHarness-Repair | HarnessChallenge-200 | weak (pass/fail; non-leaky) | 0.69 | 0.96 | 0.05 | 1.00 | 1.30 | 0.00 | no |
| Router-Repair | HarnessChallenge-200 | medium (missing obligation family; non-leaky) | 0.79 | 0.04 | 0.01 | 1.00 | 2.35 | 0.00 | no |
| ReAct | HarnessChallenge-200 | medium (missing obligation family; non-leaky) | 0.79 | 0.04 | 0.01 | 1.00 | 2.35 | 0.00 | no |
| GapHarness-Repair | HarnessChallenge-200 | medium (missing obligation family; non-leaky) | 0.79 | 0.98 | 0.05 | 1.00 | 2.31 | 0.00 | yes |
| Router-Repair | HarnessChallenge-200 | strong (missing capability/status; oracle-leakage upper bound) | 1.00 | 0.04 | 0.01 | 1.00 | 2.35 | 0.35 | no |
| ReAct | HarnessChallenge-200 | strong (missing capability/status; oracle-leakage upper bound) | 1.00 | 0.04 | 0.01 | 1.00 | 2.35 | 0.35 | no |
| GapHarness-Repair | HarnessChallenge-200 | strong (missing capability/status; oracle-leakage upper bound) | 1.00 | 0.17 | 0.04 | 1.00 | 2.31 | 0.30 | yes |

## Honest reading

At medium, non-leaky feedback the certificate does NOT buy coverage: the baselines match GapHarness-Repair within noise on coverage (GapBench 0.93 vs 0.91; HarnessChallenge 0.79 vs 0.79). The honest conclusion is therefore the conservative one: equal coverage is reachable without a certificate. What the baselines do NOT get for free is a checkable witness -- the Certificate column is `no` for every baseline row -- and the ways they reach parity are not free either. Under weak (non-leaky) feedback they only hit ~1.00 by bulk-adding modules, paying a large excess cost (ReAct excess 2.18 on GapBench, 3.08 on HarnessChallenge). Under strong feedback they hit 1.00 only by consulting the gold status / required capabilities (oracle-status accesses 0.20 per task on GapBench), which is an oracle-leakage upper bound rather than a fair operating point. The defensible contribution is thus NOT a coverage win at medium feedback; it is that GapHarness-Repair attains the same coverage while emitting a checkable certificate and without consuming privileged oracle/verifier resources to do so.

