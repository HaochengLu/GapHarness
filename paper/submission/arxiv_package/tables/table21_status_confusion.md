# Status Confusion Matrix

| Dataset | System | Expected | Predicted | N | Rate |
|---|---|---|---|---:|---:|
| GapBench test800 | GapHarness LLM | supported | supported | 696 | 0.93 |
| GapBench test800 | GapHarness LLM | supported | unsupported | 56 | 0.07 |
| GapBench test800 | GapHarness LLM | unsupported | unsupported | 24 | 1.00 |
| GapBench test800 | GapHarness LLM | clarify | supported | 14 | 0.58 |
| GapBench test800 | GapHarness LLM | clarify | unsupported | 4 | 0.17 |
| GapBench test800 | GapHarness LLM | clarify | clarify | 6 | 0.25 |
| GapBench test800 | Registry-guarded GH | supported | supported | 740 | 0.98 |
| GapBench test800 | Registry-guarded GH | supported | unsupported | 12 | 0.02 |
| GapBench test800 | Registry-guarded GH | unsupported | unsupported | 24 | 1.00 |
| GapBench test800 | Registry-guarded GH | clarify | supported | 14 | 0.58 |
| GapBench test800 | Registry-guarded GH | clarify | unsupported | 4 | 0.17 |
| GapBench test800 | Registry-guarded GH | clarify | clarify | 6 | 0.25 |
| GapBench test800 | LLM Tool Router | supported | supported | 752 | 1.00 |
| GapBench test800 | LLM Tool Router | unsupported | unsupported | 24 | 1.00 |
| GapBench test800 | LLM Tool Router | clarify | unsupported | 2 | 0.08 |
| GapBench test800 | LLM Tool Router | clarify | clarify | 22 | 0.92 |
| HarnessChallenge-200 | GapHarness LLM | supported | supported | 150 | 1.00 |
| HarnessChallenge-200 | GapHarness LLM | unsupported | supported | 30 | 0.60 |
| HarnessChallenge-200 | GapHarness LLM | unsupported | unsupported | 20 | 0.40 |
| HarnessChallenge-200 | Registry-guarded GH | supported | supported | 150 | 1.00 |
| HarnessChallenge-200 | Registry-guarded GH | unsupported | supported | 50 | 1.00 |
| HarnessChallenge-200 | LLM Tool Router | supported | supported | 135 | 0.90 |
| HarnessChallenge-200 | LLM Tool Router | supported | unsupported | 2 | 0.01 |
| HarnessChallenge-200 | LLM Tool Router | supported | clarify | 13 | 0.09 |
| HarnessChallenge-200 | LLM Tool Router | unsupported | unsupported | 50 | 1.00 |
