# SWE-HarnessExec-20

SWE-HarnessExec-20 is a small executable trace validation over sandboxed software-maintenance fixtures.

Each case creates a local Python repo, runs a failing pytest test, applies a provided patch, reruns pytest, and verifies that the trace contains the required inspection, execution, action, state, control, and verification affordances.

This is not SWE-bench pass@1, not repository checkout from SWE-bench, and not model patch generation. It is execution-level evidence that the harness loop can drive real files and tests.

Audit status: author-reviewed executable fixtures as of 2026-06-23.
