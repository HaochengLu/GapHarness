# GapHarness Workshop Package

This package contains a shorter workshop-oriented version focused on motivation, method, main GapBench result, LLM profiler calibration, registry guarding, anti-circularity stress tests, and limitations.

## Main Files

- `gapharness_workshop_8page.pdf`: compiled workshop PDF.
- `gapharness_workshop_8page.md`: source manuscript in Markdown.
- `gapharness_workshop_8page.tex`: generated LaTeX source.
- `references.bib`: verified BibTeX references.

## Supporting Files

- `figures/`: key figures used by the workshop paper.
- `tables/`: core tables used by the workshop paper.
- `supplementary/`: reproducibility checklist, artifact index, result manifest, and claim boundaries.

## Build Command

From the repository root:

```bash
pandoc paper/drafts/gapharness_workshop_8page.md --citeproc -s --pdf-engine=tectonic -o paper/submission/workshop_8page_package/gapharness_workshop_8page.pdf
```

## Boundary Note

This workshop version is intentionally shorter than the arXiv technical report. It should be paired with the supplementary files if reviewers need raw artifact details.

