# Security Policy

GapHarness is a research artifact. It should not be used as a production safety boundary for irreversible real-world actions.

## Supported Surface

The committed executor and traces are sandbox/mock oriented. They are intended to evaluate harness coverage, registry constraints, permission boundaries, and verification logic.

## Reporting Issues

Please open a GitHub issue for:

- accidental credential exposure,
- unsafe default behavior,
- misleading unsupported/supported status,
- incorrect permission or action boundary handling,
- reproducibility artifacts that contain private endpoints.

Do not include real credentials in issues. Use redacted examples.

## Secrets

The repository should never contain:

- API keys,
- private provider endpoints,
- personal tokens,
- SSH keys,
- production deployment credentials.

LLM provider configuration must be passed through environment variables at runtime.

