# Table 5. Transfer and Boundary Results

> **SUPERSEDED by table5_boundary_diagnostics_revised.md.** This earlier version is retained for provenance only; use `table5_boundary_diagnostics_revised.md` for the current boundary-diagnostics framing and terminology (e.g., "Cost Delta" instead of "Regret"). Data below is unchanged but no longer the canonical table.

| Result | Identity | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Boundary |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| GAIA-Transfer gold smoke | transfer-only gold compiler smoke | 200 | 1.00 | 1.48 | 1.48 | 0.00 | 0.00 | 0.00 | obligation labels only, not GAIA answer solving |
| GAIA registry-guarded | limitation result | 200 | 0.56 | 5.56 | 1.48 | 4.08 | 0.89 | 0.44 | shows transfer gap for multimodal/file/evidence/state obligations |
| GapBench-Natural review smoke | for-review smoke-only result | 200 | 1.00 | 2.83 | 2.83 | 0.00 | 0.00 | 0.00 | naturalized labels inherited, not final until human review |
| Terminal-Bench-obligation50 | appendix transfer scaffold | 50 | - | - | - | - | - | - | instruction-derived scaffold, labels pending audit, not Terminal-Bench solving |

Interpretation: transfer artifacts expose boundaries rather than replacing the controlled GapBench evidence.
