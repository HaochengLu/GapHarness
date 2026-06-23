# GapHarness MVP Experiment Summary

This report is generated from deterministic sandbox runs. It is suitable for MVP regression checks, not final paper numbers.

## Aggregate Metrics

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| always_full | 200 | 0.75 | 16.00 | 3.48 | 12.53 | 12.53 | 0.75 | 0.00 | 0.00 | 0.33 |
| difficulty_router | 200 | 0.33 | 4.64 | 3.48 | 1.17 | 2.85 | 0.33 | 0.42 | 0.21 | 0.30 |
| direct | 200 | 0.28 | 0.00 | 3.48 | -3.48 | 0.00 | 0.00 | 0.47 | 0.00 | 0.00 |
| gapharness | 200 | 1.00 | 3.48 | 3.48 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 200 | 1.00 | 3.48 | 3.48 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_router | 200 | 0.29 | 2.60 | 3.48 | -0.87 | 1.21 | 0.29 | 0.46 | 0.31 | 0.28 |

## Notes

- `harness success` is deterministic verifier pass against expected status plus gold obligation/capability coverage.
- `cost_delta` is predicted harness cost minus oracle minimal harness cost. It can be negative for insufficient harnesses.
- `excess_cost` is the per-row positive excess `max(0, cost_delta)`. Aggregate reports average that row-level value, so it can be positive even when mean cost delta is negative.
- `over_harness` means predicted harness cost exceeds oracle minimal harness cost.
- `under_harness` means a supported task failed obligation/capability coverage.
- `redundancy` comes from drop-one counterfactual checks over selected modules.
