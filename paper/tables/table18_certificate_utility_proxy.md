# Certificate Availability and Objective Route Properties

De-rigged 2026-06-24. The previous version of this table reported a `Debug Work`, `Audit Acc. Proxy`, and `Missing Cause Localized` column whose values were computed as a function of certificate presence via hardcoded constants; that made the certificate 'advantage' circular and those columns have been removed. This table now reports only properties that are objectively derivable from the actual frozen route and the deterministic minimality verifier and that are NOT functions of certificate presence: harness success, whether a checkable certificate is present, and minimality (redundant modules / redundancy rate / share of routes whose modules are all necessary). The honest certificate-versus-privileged-resource-cost comparison lives in `paper/tables/table_feedback_cost.md` and `scripts/run_feedback_cost_analysis.py`. A human audit packet (review sheet) accompanies this table for follow-up manual debugging-time measurement; no human timing is reported here.

| Dataset | System | N | HS | Cert. avail. | Redundant Modules | Redundancy | All-necessary |
|---|---|---:|---:|---:|---:|---:|---:|
| GapBench test800 | LLM Tool Router | 800 | 0.80 | 0.00 | 0.00 | 0.00 | 1.00 |
| GapBench test800 | Workflow Generator | 800 | 0.77 | 0.00 | 0.00 | 0.00 | 1.00 |
| GapBench test800 | Verifier-Repair Router | 800 | 1.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| GapBench test800 | ReAct Module Selector | 800 | 1.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| GapBench test800 | GapHarness LLM | 800 | 0.89 | 1.00 | 0.00 | 0.00 | 1.00 |
| GapBench test800 | Registry-guarded GH | 800 | 0.94 | 1.00 | 0.20 | 0.05 | 0.84 |
| GapBench test800 | GapHarness-Repair | 800 | 1.00 | 1.00 | 0.19 | 0.05 | 0.85 |
| HarnessChallenge-200 | LLM Tool Router | 200 | 0.65 | 0.00 | 0.00 | 0.00 | 1.00 |
| HarnessChallenge-200 | Workflow Generator | 200 | 0.83 | 0.00 | 0.00 | 0.00 | 1.00 |
| HarnessChallenge-200 | Verifier-Repair Router | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| HarnessChallenge-200 | ReAct Module Selector | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| HarnessChallenge-200 | GapHarness LLM | 200 | 0.69 | 1.00 | 0.04 | 0.01 | 0.96 |
| HarnessChallenge-200 | Registry-guarded GH | 200 | 0.59 | 1.00 | 0.04 | 0.01 | 0.96 |
| HarnessChallenge-200 | GapHarness-Repair | 200 | 1.00 | 1.00 | 0.06 | 0.01 | 0.95 |
