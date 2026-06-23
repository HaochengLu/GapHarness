# Naturalistic Holdout v0.1 Schema

This schema describes candidate records and the annotation sheet. The package is candidate-only and not gold.

## Candidate JSONL Fields

| Field | Description |
|---|---|
| `task_id` | Stable candidate id within this package, e.g. `nh-v0.1-001`. |
| `audit_status` | Always `candidate_for_human_review_not_gold`; row-level guard against treating candidates as adjudicated gold. |
| `gold_source` | Always `not_gold_candidate_for_human_review` until a separately adjudicated gold file is produced. |
| `source_type` | Public-source bucket, usually public GitHub issue derived. |
| `source_url` | Public source URL for reviewer traceability. |
| `source_ref` | Compact source reference, usually `owner/repo#issue`. |
| `repo_project` | GitHub repository/project when available. |
| `raw_title` | Sanitized public issue title. |
| `raw_prompt` | Candidate task text assembled from title, body snippet, and source URL. |
| `raw_body_snippet` | Sanitized public issue body snippet; code blocks omitted. |
| `provenance` | Collection method, timestamps, issue metadata, labels, and redaction note. |
| `suggested_category` | Non-gold triage hint for review balancing. |
| `Observation` | Blank for human annotation. |
| `Execution` | Blank for human annotation. |
| `State` | Blank for human annotation. |
| `Action` | Blank for human annotation. |
| `Control` | Blank for human annotation. |
| `Verification` | Blank for human annotation. |
| `capabilities` | Blank for human annotation. |
| `expected_status` | Blank for human annotation. |
| `annotator_a` | Blank for independent annotator A. |
| `annotator_b` | Blank for independent annotator B. |
| `adjudicated` | Blank until disagreement resolution. |
| `notes` | Blank reviewer notes. |

## Review Sheet Columns

`review_sheet.csv` uses the same reviewer-facing columns and keeps the requested annotation fields blank:

`task_id, source_type, source_url, source_ref, repo_project, raw_title, raw_prompt, suggested_category, Observation, Execution, State, Action, Control, Verification, capabilities, expected_status, annotator_a, annotator_b, adjudicated, notes`
