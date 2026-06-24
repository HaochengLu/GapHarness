# GapHarness MVP Experiment Summary

This report is generated from deterministic sandbox runs. It is suitable for MVP regression checks, not final paper numbers.

## Aggregate Metrics

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| always_full | 100 | 0.86 | 16.00 | 2.88 | 13.12 | 0.86 | 0.00 | 0.00 | 0.51 |
| difficulty_router | 100 | 0.61 | 5.84 | 2.88 | 2.96 | 0.48 | 0.25 | 0.15 | 0.24 |
| direct | 100 | 0.18 | 0.00 | 2.88 | -2.88 | 0.00 | 0.68 | 0.00 | 0.00 |
| gapharness | 100 | 1.00 | 2.88 | 2.88 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 100 | 1.00 | 2.88 | 2.88 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_router | 100 | 0.51 | 3.11 | 2.88 | 0.23 | 0.25 | 0.35 | 0.27 | 0.12 |

## Notes

- `success` is deterministic verifier pass against gold obligations and required capabilities.
- `over_harness` means predicted harness cost exceeds oracle minimal harness cost.
- `under_harness` means a supported task failed obligation/capability coverage.
- `redundancy` comes from drop-one counterfactual checks over selected modules.
