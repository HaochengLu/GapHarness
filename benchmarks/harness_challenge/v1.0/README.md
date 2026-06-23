# HarnessChallenge-200

HarnessChallenge-200 is a targeted diagnostic benchmark for GapHarness. It is deliberately constructed to stress obligation semantics and declared registry boundaries.

It is not a natural-distribution benchmark and should not be used to claim broad assistant quality.

## Composition

- Minimal pairs: 50
- Hard tool-bait: 30
- Sandbox/mock vs real side-effect boundaries: 40
- Registry absence/affordance gap: 30
- Verification/evidence traps: 30
- Real-source paraphrases from SWE/GAIA/terminal-style scaffolds: 20

## Audit Status

Labels are author-reviewed targeted diagnostics as of 2026-06-23. Independent human audit is not claimed in this artifact.

## Protocol

All baselines receive the same query text and declared registry. GapHarness gold receives the gold obligation profile. Router baselines receive only query text. The intended claim is obligation sensitivity, not end-to-end answer correctness.
