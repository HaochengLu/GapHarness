# SWE-Obligation-50 v1.0

SWE-Obligation-50 is a human-audited obligation-transfer diagnostic derived from public SWE-bench Lite rows.

Source:

- Dataset: `princeton-nlp/SWE-bench_Lite`
- Split/config: `test` / `default`
- Offset/limit: `0` / `50`
- URL: https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite

Audit status:

- `swe_obligation50_human_audited.jsonl` is human-audited by the project owner as of 2026-06-23.
- Labels describe required harness obligations only.
- This is not SWE-bench solving, not repository checkout, not patch generation, and not pass@1.

Intended use:

- Boundary/external-validity diagnostic for whether real software issue descriptions naturally map into the six-obligation ontology.
- Gold-profile compiler smoke and optional LLM profiler/router comparison.

Non-use:

- Do not compare this as a coding-agent benchmark.
- Do not report answer-level or patch-level correctness from these rows.
