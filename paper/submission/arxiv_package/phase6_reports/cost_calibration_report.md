# Cost Calibration and Sensitivity

Declared costs are not measured prices; this table checks whether the conclusions are stable under simple alternative cost schemes.

## Module Calibration

| Module | Declared | Latency ms | Tokens | API Proxy | Risk Class |
|---|---:|---:|---:|---:|---|
| web_retrieval | 3 | 750 | 850 | 5 | external evidence |
| source_span_checker | 1 | 80 | 120 | 1 | verification |
| python_executor | 2 | 250 | 80 | 1 | sandbox execution |
| execution_log_checker | 1 | 60 | 80 | 1 | verification |
| file_state_reader | 2 | 120 | 250 | 1 | workspace observation |
| state_store | 1 | 30 | 50 | 1 | state |
| sandbox_file_editor | 4 | 200 | 300 | 1 | sandbox action |
| permission_gate | 1 | 40 | 80 | 1 | control |
| contract_verifier | 1 | 80 | 180 | 1 | verification |

## Sensitivity

| Scheme | System | N | HS | Cost | Delta | Excess | Over |
|---|---|---:|---:|---:|---:|---:|---:|
| declared | GapHarness LLM | 800 | 0.89 | 3.59 | -0.09 | 0.37 | 0.16 |
| declared | Registry-guarded GH | 800 | 0.94 | 3.98 | 0.30 | 0.38 | 0.17 |
| declared | LLM Tool Router | 800 | 0.80 | 3.51 | -0.18 | 0.13 | 0.12 |
| declared | Workflow Generator | 800 | 0.77 | 3.37 | -0.31 | 0.11 | 0.10 |
| declared | Verifier-Repair Router | 800 | 1.00 | 3.85 | 0.16 | 0.16 | 0.14 |
| declared | ReAct Module Selector | 800 | 1.00 | 3.90 | 0.21 | 0.21 | 0.20 |
| declared | GapHarness-Repair | 800 | 1.00 | 3.96 | 0.28 | 0.28 | 0.15 |
| uniform | GapHarness LLM | 800 | 0.89 | 2.10 | 0.03 | 0.26 | 0.16 |
| uniform | Registry-guarded GH | 800 | 0.94 | 2.28 | 0.22 | 0.27 | 0.17 |
| uniform | LLM Tool Router | 800 | 0.80 | 2.02 | -0.05 | 0.13 | 0.12 |
| uniform | Workflow Generator | 800 | 0.77 | 1.92 | -0.15 | 0.11 | 0.10 |
| uniform | Verifier-Repair Router | 800 | 1.00 | 2.22 | 0.16 | 0.16 | 0.14 |
| uniform | ReAct Module Selector | 800 | 1.00 | 2.28 | 0.21 | 0.21 | 0.20 |
| uniform | GapHarness-Repair | 800 | 1.00 | 2.28 | 0.21 | 0.21 | 0.15 |
| latency_proxy | GapHarness LLM | 800 | 0.89 | 4.73 | -0.05 | 0.47 | 0.16 |
| latency_proxy | Registry-guarded GH | 800 | 0.94 | 5.15 | 0.36 | 0.48 | 0.17 |
| latency_proxy | LLM Tool Router | 800 | 0.80 | 4.48 | -0.31 | 0.13 | 0.12 |
| latency_proxy | Workflow Generator | 800 | 0.77 | 4.32 | -0.47 | 0.11 | 0.10 |
| latency_proxy | Verifier-Repair Router | 800 | 1.00 | 4.95 | 0.16 | 0.16 | 0.14 |
| latency_proxy | ReAct Module Selector | 800 | 1.00 | 5.00 | 0.21 | 0.21 | 0.20 |
| latency_proxy | GapHarness-Repair | 800 | 1.00 | 5.15 | 0.36 | 0.36 | 0.15 |
| risk_weighted | GapHarness LLM | 800 | 0.89 | 4.96 | -0.07 | 0.56 | 0.16 |
| risk_weighted | Registry-guarded GH | 800 | 0.94 | 5.50 | 0.47 | 0.59 | 0.17 |
| risk_weighted | LLM Tool Router | 800 | 0.80 | 4.77 | -0.26 | 0.23 | 0.12 |
| risk_weighted | Workflow Generator | 800 | 0.77 | 4.57 | -0.46 | 0.19 | 0.10 |
| risk_weighted | Verifier-Repair Router | 800 | 1.00 | 5.31 | 0.28 | 0.28 | 0.14 |
| risk_weighted | ReAct Module Selector | 800 | 1.00 | 5.37 | 0.34 | 0.34 | 0.20 |
| risk_weighted | GapHarness-Repair | 800 | 1.00 | 5.46 | 0.44 | 0.44 | 0.15 |
| token_api_proxy | GapHarness LLM | 800 | 0.89 | 4.35 | -0.05 | 0.46 | 0.16 |
| token_api_proxy | Registry-guarded GH | 800 | 0.94 | 4.78 | 0.38 | 0.47 | 0.17 |
| token_api_proxy | LLM Tool Router | 800 | 0.80 | 4.16 | -0.25 | 0.13 | 0.12 |
| token_api_proxy | Workflow Generator | 800 | 0.77 | 3.99 | -0.41 | 0.11 | 0.10 |
| token_api_proxy | Verifier-Repair Router | 800 | 1.00 | 4.56 | 0.16 | 0.16 | 0.14 |
| token_api_proxy | ReAct Module Selector | 800 | 1.00 | 4.61 | 0.21 | 0.21 | 0.20 |
| token_api_proxy | GapHarness-Repair | 800 | 1.00 | 4.74 | 0.34 | 0.34 | 0.15 |
