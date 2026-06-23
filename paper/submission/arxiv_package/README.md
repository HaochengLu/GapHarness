# GapHarness arXiv Package

This package contains the paper-facing submission artifacts.

## Main Files

- `gapharness_arxiv.pdf`: compiled final PDF, 20 pages, letter single-column.
- `gapharness_manuscript_v2.md`: source manuscript in Markdown.
- `gapharness_manuscript_v2.tex`: package-local generated LaTeX source with relative bibliography and figure paths.
- `gapharness_package_local.md`: package-local Markdown source with relative bibliography and figure paths.
- `checksums.sha256`: package-local SHA-256 checksums using paths relative to this directory.
- `references.bib`: verified BibTeX references.

## Supporting Files

- `figures/`: main figure sources and PDF-compatible cropped PNG copies.
- `tables/`: revised main table files, compiler replay/scaling tables, LLM Tool Router baseline, feedback-level replay, certificate utility proxy, cost-scheme sensitivity/proxy calibration, status confusion, profiler taxonomy, HarnessChallenge, SWE-HarnessExec-20, and SWE-HarnessExec-50 tables.
- `phase4_reports/`: reviewer-hardening reports for the optimized compiler, certificate samples, LLM Tool Router baseline, HarnessChallenge-200, SWE-HarnessExec-20/50, bootstrap CIs, and secondary audit.
- `phase5_reports/`: diagnostic-feedback strategy baseline and GapHarness-Repair summaries for GapBench test800, HarnessChallenge-200, and SWE-HarnessExec-20.
- `phase6_reports/`: feedback-level replay, certificate utility proxy plus audit packet, cost-scheme sensitivity/proxy calibration, status confusion, profiler error taxonomy, and RealBoundary-100 reports.
- `benchmark_sources/naturalistic_holdout_v0.1/`: 200-row independent public GitHub issue-derived candidate review package with blank annotation fields and review sheet.
- `appendix/`: reproducibility, stress-test details, transfer scaffold notes, and artifact checklist.
- `artifact_index.md`: final artifact index.
- `docs/final_result_manifest.md`: result identity and boundary manifest.
- `docs/paper_claims_and_boundaries.md`: supported claims and non-claims.

## Build Command

From the repository root:

```bash
pandoc paper/drafts/gapharness_manuscript_v2.md --citeproc -s --pdf-engine=tectonic -o paper/submission/arxiv_package/gapharness_arxiv.pdf
```

From inside this package directory:

```bash
pandoc gapharness_package_local.md --citeproc -s --pdf-engine=tectonic -o gapharness_arxiv.pdf
```

Direct TeX build from inside this package directory:

```bash
tectonic --only-cached gapharness_manuscript_v2.tex
```

Build requirements: `pandoc` plus a TeX engine for Markdown rebuilds, or Tectonic alone for the direct TeX route. On a fresh machine, Tectonic may need to download or already have its TeX bundle cached. If the machine is offline or blocks that download, use the included `gapharness_arxiv.pdf` and verify it with `shasum -a 256 -c checksums.sha256` instead of treating source-path resolution as failed. The package-local source paths are relative to this directory (`references.bib` and `figures/`).

Path note: root-level manifests use repository-relative paths such as `benchmarks/...` and `outputs/...`. The package-local copies of selected benchmark sources are under `benchmark_sources/`.

## Boundary Note

The paper claims obligation-first runtime harness compilation under declared registry boundaries. Harness success means obligation/capability coverage, not answer-level correctness. Diagnostic-feedback baselines compare policies over a shared registry/executor/verifier, not whole frameworks; verifier-repair and ReAct-style baselines receive verifier feedback after failed routes and do not emit GapHarness minimality certificates. GapHarness-Repair converts verifier diagnostics into profile patches and recompiles with certificates, but it is a feedback-assisted upper-bound variant rather than a one-shot profiler result. Certificate utility results are deterministic proxies plus a prepared audit packet, not completed human timing. RealBoundary-100 is fresh relative to the post-hoc registry guard, but it is author-seeded and review-pending. Naturalistic-Holdout v0.1 is independent of GapBench and has a review sheet, but it is still a candidate package until two-annotator labels, agreement metrics, and adjudication are complete. The optimized compiler preserves frozen exact outputs in replay and emits checkable certificates, but exact compilation remains exponential in the worst case, as shown by the mostly non-dominated scaling stress. SWE-HarnessExec-50 is a provided-patch sandbox pytest trace scale-up, not real-repository checkout or model-generated repair. The report does not claim full GAIA solving, Terminal-Bench solving, SWE-bench patch solving/pass@1, arbitrary real-world side-effect safety, model-generated repairs in SWE-HarnessExec, or fully solved LLM profiling.
