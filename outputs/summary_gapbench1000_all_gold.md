# GapHarness MVP Experiment Summary

This report is generated from deterministic sandbox runs. It is suitable for MVP regression checks, not final paper numbers.

## Aggregate Metrics

| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| always_full | 1000 | 0.94 | 16.00 | 3.67 | 12.33 | 0.94 | 0.00 | 0.00 | 0.51 |
| difficulty_router | 1000 | 0.43 | 3.46 | 3.67 | -0.21 | 0.28 | 0.51 | 0.16 | 0.14 |
| direct | 1000 | 0.20 | 0.00 | 3.67 | -3.67 | 0.00 | 0.74 | 0.00 | 0.00 |
| gapharness | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 1000 | 1.00 | 3.67 | 3.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_router | 1000 | 0.34 | 2.10 | 3.67 | -1.57 | 0.11 | 0.60 | 0.42 | 0.06 |

## Notes

- `success` is deterministic verifier pass against gold obligations and required capabilities.
- `over_harness` means predicted harness cost exceeds oracle minimal harness cost.
- `under_harness` means a supported task failed obligation/capability coverage.
- `redundancy` comes from drop-one counterfactual checks over selected modules.
