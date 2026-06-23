# GapHarness MVP Experiment Summary

This report is generated from deterministic sandbox runs. It is suitable for MVP regression checks, not final paper numbers.

## Aggregate Metrics

| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong | Redundancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| always_full | 50 | 1.00 | 16.00 | 12.00 | 4.00 | 4.00 | 1.00 | 0.00 | 0.00 | 0.11 |
| difficulty_router | 50 | 1.00 | 16.00 | 12.00 | 4.00 | 4.00 | 1.00 | 0.00 | 0.00 | 0.11 |
| direct | 50 | 0.00 | 0.00 | 12.00 | -12.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 |
| gapharness | 50 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| oracle_minimal | 50 | 1.00 | 12.00 | 12.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tool_router | 50 | 0.00 | 4.68 | 12.00 | -7.32 | 0.00 | 0.00 | 1.00 | 1.00 | 0.00 |

## Notes

- `harness success` is deterministic verifier pass against expected status plus gold obligation/capability coverage.
- `cost_delta` is predicted harness cost minus oracle minimal harness cost. It can be negative for insufficient harnesses.
- `excess_cost` is max(0, cost_delta) and should be used for non-negative over-cost claims.
- `over_harness` means predicted harness cost exceeds oracle minimal harness cost.
- `under_harness` means a supported task failed obligation/capability coverage.
- `redundancy` comes from drop-one counterfactual checks over selected modules.
