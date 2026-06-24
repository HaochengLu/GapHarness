# GAIA Transfer Human-Audited Package

This package contains larger GAIA transfer labels confirmed as gold truth.

Audit status:

- `gaia_validation_100_for_review.*`: human-audited and accepted.
- `gaia_test_100_for_review.*`: human-audited and accepted.
- The project owner confirmed on 2026-06-22 that the GAIA validation100/test100 transfer labels are gold truth.
- Files are stamped with `gold_source = project_owner_audited_confirmed_2026_06_22_gaia_transfer_200`.

Source:

- Hugging Face dataset: `gaia-benchmark/GAIA`
- Config: `2023_all`
- Split sizes loaded locally:
  - validation: 165 rows
  - test: 301 rows

Sampling:

- 100 examples from validation.
- 100 examples from test.
- Deterministic stratified take by GAIA level and whether the task has an attached file.

Files:

- `gaia_validation_100_for_review.jsonl`
- `gaia_validation_100_review_sheet.csv`
- `gaia_test_100_for_review.jsonl`
- `gaia_test_100_review_sheet.csv`
- `gaia_transfer_review_manifest.json`

Smoke verification:

- validation100 GapHarness gold compiler: success 1.00, regret 0.00.
- test100 GapHarness gold compiler: success 1.00, regret 0.00.
- combined transfer200 GapHarness gold compiler: success 1.00, regret 0.00.
