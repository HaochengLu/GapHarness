# Phase 2D Negative-Control Analysis: Pure Language and Tool-Bait

This analysis tests whether systems are obligation-sensitive rather than keyword/tool-sensitive.

## Category-Level Results

| Category | System | N | Success | Avg Cost | Over | Under | Wrong |
|---|---|---:|---:|---:|---:|---:|---:|
| pure_language_negative | direct | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pure_language_negative | tool_router | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pure_language_negative | always_full | 100 | 1.00 | 16.00 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | difficulty_router | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pure_language_negative | gapharness_gold | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pure_language_negative | gapharness_llm_single | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pure_language_negative | gapharness_registry_guarded | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_bait | direct | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_bait | tool_router | 100 | 1.00 | 1.26 | 0.51 | 0.00 | 0.00 |
| tool_bait | always_full | 100 | 1.00 | 16.00 | 1.00 | 0.00 | 0.00 |
| tool_bait | difficulty_router | 100 | 1.00 | 1.22 | 0.51 | 0.00 | 0.00 |
| tool_bait | gapharness_gold | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_bait | gapharness_llm_single | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_bait | gapharness_registry_guarded | 100 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Combined Negative Controls

| System | N | Success | Avg Cost | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|
| direct | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_router | 200 | 1.00 | 0.63 | 0.26 | 0.00 | 0.00 |
| always_full | 200 | 1.00 | 16.00 | 1.00 | 0.00 | 0.00 |
| difficulty_router | 200 | 1.00 | 0.61 | 0.26 | 0.00 | 0.00 |
| gapharness_gold | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| gapharness_llm_single | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| gapharness_registry_guarded | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Interpretation: GapHarness gold and calibrated LLM variants should avoid over-harnessing pure language and explicit no-tool bait, while Always-full necessarily over-harnesses.
