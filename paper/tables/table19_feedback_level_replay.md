# Feedback-Level Replay

Weak feedback gives only pass/fail; medium gives missing obligation families; strong gives missing capabilities/status and is an upper bound. Cert. reports system-generated GapHarness certificates only; certificates created by replay helper code for non-GapHarness rows are stripped from those rows.

| Dataset | Feedback | System | N | HS | Cost | Excess | Over | Under | Wrong | LLM | Compiler | Verifier | Rounds | Cert. |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GapBench test800 | medium_obligation | GapHarness-Repair replay | 800 | 0.91 | 3.62 | 0.37 | 0.14 | 0.07 | 0.00 | 1.00 | 1.00 | 2.00 | 0.11 | 0.11 |
| GapBench test800 | medium_obligation | ReAct replay | 800 | 0.93 | 3.78 | 0.16 | 0.14 | 0.07 | 0.07 | 1.00 | 0.00 | 2.00 | 0.20 | 0.00 |
| GapBench test800 | medium_obligation | Router-Repair replay | 800 | 0.93 | 3.78 | 0.16 | 0.14 | 0.07 | 0.07 | 1.00 | 0.00 | 2.00 | 0.20 | 0.00 |
| GapBench test800 | strong_capability_status | GapHarness-Repair replay | 800 | 1.00 | 3.94 | 0.25 | 0.14 | 0.00 | 0.00 | 1.00 | 1.00 | 2.00 | 0.11 | 0.09 |
| GapBench test800 | strong_capability_status | ReAct replay | 800 | 1.00 | 3.82 | 0.13 | 0.12 | 0.00 | 0.00 | 1.00 | 0.00 | 2.00 | 0.20 | 0.00 |
| GapBench test800 | strong_capability_status | Router-Repair replay | 800 | 1.00 | 3.82 | 0.13 | 0.12 | 0.00 | 0.00 | 1.00 | 0.00 | 2.00 | 0.20 | 0.00 |
| GapBench test800 | weak_pass_fail | GapHarness-Repair replay | 800 | 0.89 | 3.59 | 0.37 | 0.14 | 0.09 | 0.01 | 1.00 | 1.00 | 1.00 | 0.11 | 0.00 |
| GapBench test800 | weak_pass_fail | ReAct replay | 800 | 1.00 | 5.87 | 2.18 | 0.31 | 0.00 | 0.00 | 1.00 | 0.00 | 1.00 | 0.20 | 0.00 |
| GapBench test800 | weak_pass_fail | Router-Repair replay | 800 | 1.00 | 5.87 | 2.18 | 0.31 | 0.00 | 0.00 | 1.00 | 0.00 | 1.00 | 0.20 | 0.00 |
| HarnessChallenge-200 | medium_obligation | GapHarness-Repair replay | 200 | 0.79 | 4.39 | 0.98 | 0.05 | 0.07 | 0.07 | 1.00 | 1.00 | 2.00 | 0.30 | 0.30 |
| HarnessChallenge-200 | medium_obligation | ReAct replay | 200 | 0.79 | 2.83 | 0.04 | 0.01 | 0.21 | 0.15 | 1.00 | 0.00 | 2.00 | 0.35 | 0.00 |
| HarnessChallenge-200 | medium_obligation | Router-Repair replay | 200 | 0.79 | 2.83 | 0.04 | 0.01 | 0.21 | 0.15 | 1.00 | 0.00 | 2.00 | 0.35 | 0.00 |
| HarnessChallenge-200 | strong_capability_status | GapHarness-Repair replay | 200 | 1.00 | 3.64 | 0.17 | 0.04 | 0.00 | 0.00 | 1.00 | 1.00 | 2.00 | 0.30 | 0.15 |
| HarnessChallenge-200 | strong_capability_status | ReAct replay | 200 | 1.00 | 3.52 | 0.04 | 0.01 | 0.00 | 0.00 | 1.00 | 0.00 | 2.00 | 0.35 | 0.00 |
| HarnessChallenge-200 | strong_capability_status | Router-Repair replay | 200 | 1.00 | 3.52 | 0.04 | 0.01 | 0.00 | 0.00 | 1.00 | 0.00 | 2.00 | 0.35 | 0.00 |
| HarnessChallenge-200 | weak_pass_fail | GapHarness-Repair replay | 200 | 0.69 | 3.92 | 0.96 | 0.05 | 0.15 | 0.11 | 1.00 | 1.00 | 1.00 | 0.30 | 0.00 |
| HarnessChallenge-200 | weak_pass_fail | ReAct replay | 200 | 1.00 | 6.56 | 3.08 | 0.36 | 0.00 | 0.00 | 1.00 | 0.00 | 1.00 | 0.35 | 0.00 |
| HarnessChallenge-200 | weak_pass_fail | Router-Repair replay | 200 | 1.00 | 6.56 | 3.08 | 0.36 | 0.00 | 0.00 | 1.00 | 0.00 | 1.00 | 0.35 | 0.00 |
