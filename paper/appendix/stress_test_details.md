# Appendix: Stress Test Details

## Registry Perturbation

For each removed module, the experiment selects a relevant first-N 60-task subset and compares base registry behavior against the perturbed registry.

Removed modules:

- `python_executor`
- `source_span_checker`
- `permission_gate`
- `sandbox_file_editor`
- `web_retrieval`
- `contract_verifier`

Result: base registry success is 1.00 for all subsets; perturbed registry success is 0.00 for all six removals. The compiler returns unsupported or the verifier reports under-covered capability obligations.

## Gold Label Permutation

The compiler receives corrupted obligation profiles, while the verifier checks the original project-owner-audited labels. This separates label corruption from verifier truth.

Corruptions include:

- Observation and Execution swaps
- Action and State swaps
- Verification deletion
- Control addition
- Primary obligation deletion

Permutation integrity: 200 / 200 corrupted profiles changed obligations or required capabilities; no-op corruptions: 0.

This is not a realistic corruption model. It is an anti-circularity stress test.

## Negative Controls

The negative-control analysis evaluates `pure_language_negative` and `tool_bait` separately across:

- Direct
- Tool Router
- Always-full
- Difficulty Router
- GapHarness gold
- GapHarness LLM
- Registry-guarded GapHarness

GapHarness variants avoid over-harnessing both categories, while Always-full over-harnesses both and keyword routers over-harness tool-bait prompts.
