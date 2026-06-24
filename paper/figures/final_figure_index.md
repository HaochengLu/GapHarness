# Final Figure Index

The main manuscript includes four main figures. Captions below state what each figure supports and what it does not support.

## Figure 1. GapHarness System Pipeline

- Original source SVG: `paper/figures/figure1_pipeline.svg`
- Print-friendly source SVG: `paper/figures/figure1_pipeline_print.svg`
- PDF-compatible PNG: `paper/figures/figure1_pipeline_print.png`
- Supports: system decomposition into obligation profiling, registry lookup, exact compilation, sandbox execution, tracing, and verification.
- Does not support: end-to-end open-world task solving.

## Figure 2. Cost-Success Frontier

- Source SVG: `paper/figures/figure2_cost_success_frontier.svg`
- PDF-compatible PNG: `paper/figures/figure2_cost_success_frontier.png`
- Supports: gold GapHarness matches oracle minimal cost while Always-full buys success with much higher cost.
- Does not support: fully calibrated LLM profiling.

## Figure 3. Over / Under / Wrong Harnessing Bar Chart

- Source SVG: `paper/figures/figure3_over_under_wrong_bars.svg`
- PDF-compatible PNG: `paper/figures/figure3_over_under_wrong_bars.png`
- Supports: baseline policies fail in distinguishable ways.
- Does not support: unchanged rates on every naturalistic benchmark.

## Figure 4. Registry-Guarded Unsupported False-Positive Reduction

- Source SVG: `paper/figures/figure4_registry_guard_unsupported_fp_reduction.svg`
- PDF-compatible PNG: `paper/figures/figure4_registry_guard_unsupported_fp_reduction.png`
- Supports: registry guarding reduces a specific sandbox-action unsupported false-positive failure.
- Does not support: full GAIA solving or a general fix for all profiler errors.

## v3 (Reframed Manuscript) Figures

The reframed manuscript `paper/drafts/gapharness_manuscript_v3.md` (built to `gapharness_manuscript_v3.pdf`) uses Figure 1 plus three new figures generated from real artifacts by `scripts/generate_v3_figures.py` (PNG + PDF):

### Figure 5. Reliability of the Obligation Instrument (headline)

- Source: `paper/figures/figure5_reliability_alpha.png` / `.pdf` (from `outputs/iaa/iaa_metrics.json`)
- Supports: the status decision and coarse Observation/Action/Control obligations reproduce across three independent model families (incl. on adversarial inputs); fine Execution/State/Verification obligations collapse to at-or-below chance on adversarial inputs.
- Does not support: a human inter-annotator-agreement claim (this is multi-model agreement, a proxy).

### Figure 6. Certificate vs Coverage at Medium Non-Leaky Feedback

- Source: `paper/figures/figure6_certificate_vs_coverage.png` / `.pdf` (from `outputs/final/feedback_cost/feedback_cost_rows.jsonl`)
- Supports: equal coverage is reachable without a certificate; only GapHarness-Repair emits a third-party-checkable witness.
- Does not support: a coverage advantage for GapHarness.

### Figure 7. Canonicalization No-Lexical Ablation

- Source: `paper/figures/figure7_canonicalize_ablation.png` / `.pdf` (from `outputs/ablation/ablation_metrics.json`)
- Supports: removing the lexical normalization moves held-out coverage by only +0.039 with obligation micro-F1 unchanged; the model, not a keyword router, carries the inference.
- Does not support: a claim that the pipeline is free of lexical aids.

## Appendix Figure Candidates

- `figures/final/regret_distribution.svg`
- `figures/final/drop_one_necessity.svg`
- obligation-level F1 from `outputs/final/phase2b/table2_obligation_level_f1.md`
- category breakdowns from `outputs/final/phase2/` and `outputs/final/phase2b/`
