# GapBench Expansion Human-Audited Release

This package expands the human-audited 100-item seed benchmark to 500 and 1000 total items.

Important audit status:
- The original 100 seed items are preserved with confirmed human-audited labels.
- The project owner confirmed on 2026-06-22 that the expansion items are also gold truth.
- JSONL and CSV files are stamped with `gold_source = human_audited_confirmed_2026_06_22_gapbench_expansion`.

Files:
- `gapbench_1000_for_review.jsonl`: full 1000-item JSONL benchmark, now human-audited.
- `gapbench_500_for_review.jsonl`: stratified 500-item human-audited subset that includes the original seed items.
- `gapbench_1000_review_sheet.csv`: CSV review sheet stamped accepted.
- `gapbench_500_review_sheet.csv`: 500-item review sheet stamped accepted.
- `gapbench_expansion_manifest.json`: schema, counts, assumed registry, and audit metadata.

1000 category counts:
```json
{
  "pure_language_negative": 100,
  "tool_bait": 100,
  "single_obligation": 180,
  "pairwise_obligation": 260,
  "triple_obligation": 230,
  "unsupported": 30,
  "ambiguous": 30,
  "complex_obligation": 70
}
```

500 category counts:
```json
{
  "pure_language_negative": 50,
  "tool_bait": 50,
  "single_obligation": 90,
  "pairwise_obligation": 130,
  "triple_obligation": 115,
  "complex_obligation": 35,
  "unsupported": 15,
  "ambiguous": 15
}
```

Review columns in CSV:
- `review_decision`: accept / revise / drop
- `reviewer_notes`: free-form comments
- `revised_gold_obligations`: fill only if label changes
- `revised_oracle_minimal_harness`: fill only if harness changes
- `revised_expected_status`: fill only if supported / unsupported / clarify changes

Current review result:
- all rows accepted as gold truth.
