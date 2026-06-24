# GapHarness MVP Experiment Summary

This report is generated from deterministic sandbox runs. It is suitable for MVP regression checks, not final paper numbers.

## Aggregate Metrics

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gapharness | 100 | 1.00 | 1.39 | 1.39 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Notes

- `success` is deterministic verifier pass against gold obligations and required capabilities.
- `over_harness` means predicted harness cost exceeds oracle minimal harness cost.
- `under_harness` means a supported task failed obligation/capability coverage.
- `redundancy` comes from drop-one counterfactual checks over selected modules.
