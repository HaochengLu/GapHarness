# SWE-Obligation-50 Diagnostic Summary

SWE-Obligation-50 is derived from public SWE-bench Lite task descriptions. It is an obligation-transfer diagnostic only, not repository checkout, patch solving, or pass@1.

## Original Human-Audited Source View

| View | System | N | Harness Success | Cost | Oracle | Cost Delta | Excess Cost | Under | Wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| original gold | direct | 50 | 0.00 | 0.00 | 12.00 | -12.00 | 0.00 | 1.00 | 0.00 |
| original gold | tool_router | 50 | 0.00 | 4.68 | 12.00 | -7.32 | 0.00 | 1.00 | 1.00 |
| original gold | difficulty_router | 50 | 1.00 | 16.00 | 12.00 | 4.00 | 4.00 | 0.00 | 0.00 |
| original gold | always_full | 50 | 1.00 | 16.00 | 12.00 | 4.00 | 4.00 | 0.00 | 0.00 |
| original gold | gapharness | 50 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| original gold | oracle_minimal | 50 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## LLM-Safe Diagnostic View

| View | System | N | Harness Success | Cost | Oracle | Cost Delta | Excess Cost | Under | Wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| llm-safe gold | direct | 50 | 0.00 | 0.00 | 12.00 | -12.00 | 0.00 | 1.00 | 0.00 |
| llm-safe gold | tool_router | 50 | 0.00 | 4.08 | 12.00 | -7.92 | 0.00 | 1.00 | 1.00 |
| llm-safe gold | difficulty_router | 50 | 0.08 | 6.80 | 12.00 | -5.20 | 0.32 | 0.92 | 0.92 |
| llm-safe gold | always_full | 50 | 1.00 | 16.00 | 12.00 | 4.00 | 4.00 | 0.00 | 0.00 |
| llm-safe gold | gapharness | 50 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| llm-safe gold | oracle_minimal | 50 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| llm-safe | GapHarness LLM | 50 | 1.00 | 12.80 | 12.00 | 0.80 | 0.80 | 0.00 | 0.00 |
| llm-safe | Registry-guarded GH | 50 | 1.00 | 12.80 | 12.00 | 0.80 | 0.80 | 0.00 | 0.00 |
| llm-safe | LLM Tool Router | 50 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 |

The LLM-safe view shortens long issue bodies to avoid provider content filters while retaining real source repo, instance id, title, and test-count metadata. The original human-audited benchmark remains `benchmarks/swe_obligation/v1.0/swe_obligation50_human_audited.jsonl`.
