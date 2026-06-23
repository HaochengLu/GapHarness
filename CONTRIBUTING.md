# Contributing

This repository is primarily a research artifact. Contributions are welcome when they improve reproducibility, clarity, benchmark provenance, or implementation correctness.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Pull Request Expectations

- Keep claims bounded to harness coverage and registry-constrained support selection.
- Do not add API keys, private endpoints, raw credentials, or provider-specific secrets.
- Add or update tests for compiler, verifier, baseline, or data-format changes.
- Update benchmark manifests when changing dataset rows or provenance.
- Regenerate checksums when release artifacts change.

## Benchmark Changes

For any benchmark row addition or edit, include:

- source or generation provenance,
- obligation labels,
- required capabilities,
- expected status,
- audit status,
- notes on unsupported or boundary-sensitive behavior.

## Artifact Changes

When changing `outputs/final/` or the paper package, run:

```bash
pytest
python -m py_compile gapharness/*.py scripts/*.py
shasum -a 256 -c --strict outputs/final/checksums.sha256
shasum -a 256 -c --strict paper/submission/arxiv_package/checksums.sha256
```

