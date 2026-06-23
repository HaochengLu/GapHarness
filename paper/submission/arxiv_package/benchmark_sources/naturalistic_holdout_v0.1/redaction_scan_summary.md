# Naturalistic Holdout v0.1 Redaction Scan Summary

Scope: files in `benchmarks/naturalistic_holdout/v0.1/` with extensions `.jsonl`, `.csv`, `.md`, and `.json`.

This scan is a deterministic high-risk pattern check, not a replacement for human review of uncontrolled public issue text.

| Pattern | Regex Class | Matches |
|---|---|---:|
| OpenAI-style API key | `sk-[A-Za-z0-9_-]{20,}` | 0 |
| Hugging Face token | `hf_[A-Za-z0-9]{20,}` | 0 |
| AWS access key | `AKIA[0-9A-Z]{16}` | 0 |
| GitHub token | `gh[pousr]_[A-Za-z0-9_]{20,}` | 0 |
| Generic assignment secret | `(api[_-]?key|secret|token|password)[:=]...` | 0 |
| Email address | common email-address regex | 0 |

Notes:

- Candidate snippets are public GitHub issue-derived text and code blocks are omitted.
- Environment-variable names may appear in public issue prose; the scan above looks for credential-like values, not mere variable names.
- Before public release as a scored benchmark, reviewers should manually inspect the final adjudicated source file again.
