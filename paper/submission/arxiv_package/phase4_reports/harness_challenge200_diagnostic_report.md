# HarnessChallenge-200 Targeted Diagnostic Report

HarnessChallenge-200 is a targeted diagnostic benchmark. It is not a natural-frequency benchmark and does not measure final answer correctness.

## Aggregate Results

| System | N | HS | Cost | Delta | Excess | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Direct | 200 | 0.28 | 0.00 | -3.48 | 0.00 | 0.00 | 0.47 | 0.00 |
| Tool Router | 200 | 0.29 | 2.60 | -0.87 | 1.21 | 0.29 | 0.46 | 0.31 |
| Difficulty Router | 200 | 0.33 | 4.64 | 1.17 | 2.85 | 0.33 | 0.42 | 0.21 |
| Always-full | 200 | 0.75 | 16.00 | 12.53 | 12.53 | 0.75 | 0.00 | 0.00 |
| LLM Tool Router | 200 | 0.65 | 2.60 | -0.88 | 0.04 | 0.01 | 0.35 | 0.28 |
| GapHarness gold | 200 | 1.00 | 3.48 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GapHarness LLM | 200 | 0.69 | 3.92 | 0.45 | 0.96 | 0.05 | 0.15 | 0.11 |
| Registry-guarded GH | 200 | 0.59 | 4.82 | 1.34 | 1.86 | 0.05 | 0.15 | 0.11 |
| Oracle minimal | 200 | 1.00 | 3.48 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Category Breakdown: Harness Success

| Category | Direct | Tool Router | Difficulty | Always-full | LLM Tool Router | GH Gold | GH LLM | Registry-guarded GH |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| hard_tool_bait | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| minimal_pair | 0.50 | 0.50 | 0.64 | 1.00 | 0.54 | 1.00 | 0.80 | 0.80 |
| real_source_paraphrase | 0.10 | 0.15 | 0.15 | 1.00 | 0.35 | 1.00 | 0.45 | 0.45 |
| registry_absence | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 0.00 | 0.00 |
| sandbox_vs_real_side_effect | 0.00 | 0.00 | 0.00 | 0.50 | 0.50 | 1.00 | 0.75 | 0.25 |
| verification_evidence_trap | 0.00 | 0.00 | 0.00 | 1.00 | 0.50 | 1.00 | 1.00 | 1.00 |

## Interpretation

- GapHarness gold and oracle minimal reach 1.00 because labels and registry declarations are sufficient and minimal.
- LLM Tool Router sees the same registry and costs but not obligation labels; it under-covers minimal pairs, verification traps, and real-source paraphrases.
- The registry guard was calibrated on GapBench and does not solve this harder targeted diagnostic set; this is reported as a boundary result rather than a positive-only ablation.
