# Naturalistic Holdout v0.1 Candidate Review Package

This directory contains a **candidate review package**, not a human-audited gold benchmark.

The package is intended to seed an independent naturalistic holdout for GapHarness. It was sampled from public GitHub issue pages via the unauthenticated GitHub REST API. It is not generated from GapBench templates, not rewritten from GapBench, and does not modify GapBench.

## Contents

- `naturalistic_holdout_v0.1_candidates.jsonl`: 200 candidate tasks with provenance and blank annotation fields.
- `review_sheet.csv`: human annotation sheet with the requested obligation/capability/status columns.
- `manifest.json`: source distribution, audit status, files, and annotation plan.
- `schema.md`: field-level schema for the candidate records and review sheet.
- `redaction_scan_summary.md`: deterministic high-risk pattern scan summary for the candidate package.

A source copy is also written to `outputs/final/benchmark_sources/naturalistic_holdout_v0.1_candidates.jsonl` for final artifact collection.

## Audit Status

Status: `candidate_for_human_review_not_gold`.

Do not treat these rows as gold labels. Each JSONL row includes `audit_status=candidate_for_human_review_not_gold` and `gold_source=not_gold_candidate_for_human_review`. The fields `Observation`, `Execution`, `State`, `Action`, `Control`, `Verification`, `capabilities`, and `expected_status` are intentionally blank for human annotation. `suggested_category` is a lightweight triage hint only.

## Planned Review Protocol

1. Two annotators independently fill `annotator_a` and `annotator_b` plus the obligation, capability, and expected-status fields.
2. Compute Cohen kappa for binary/categorical fields.
3. Compute Krippendorff alpha where missing labels or multi-label capability coding make it more appropriate.
4. Adjudicate disagreements into the `adjudicated` and `notes` columns.
5. Only after adjudication should a derived gold file be stamped as human-audited.

## Source And Safety Notes

- Sources are public GitHub issues only.
- No private data sources were used.
- No user API key, Hugging Face token, or authenticated GitHub token was used.
- Obvious token/email/long-secret patterns were redacted and code blocks were omitted from snippets.
- Human reviewers should still inspect source snippets before public release because issue bodies are uncontrolled public text.

## Distribution

Source types:

- `public_github_issue_agent_development`: 170
- `public_github_issue_developer_tooling`: 30

Top repositories:

- `openai/openai-agents-python`: 35
- `langchain-ai/langgraph`: 35
- `langchain-ai/langchain`: 30
- `microsoft/autogen`: 30
- `crewAIInc/crewAI`: 30
- `All-Hands-AI/OpenHands`: 30
- `browser-use/browser-use`: 10

Suggested categories:

- `agent_workflow`: 44
- `bug_reproduction`: 45
- `documentation_question`: 24
- `feature_request`: 53
- `general_issue_request`: 6
- `integration_setup`: 22
- `performance_or_scaling`: 6
