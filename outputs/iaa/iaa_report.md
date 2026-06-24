# Multi-Model Inter-Annotator-Agreement Report (M3 gate)

**This is MULTI-MODEL agreement: a legitimate, honest proxy for and precursor to human inter-annotator agreement.** Three different model *families* each annotated the same rows from the shared neutral codebook only. It is NOT a human IAA study; the human protocol, codebook, and review sheet below are ready for a future human pass to plug into.

- Shared instrument (codebook): `docs/annotation_codebook.md`
- Stratified GapBench subset: `outputs/iaa/gapbench_subset.jsonl` (+ task ids in `outputs/iaa/gapbench_subset_task_ids.json`)
- Harder disguised-refusal set: `benchmarks/disguised_refusal/v0.1/disguised_refusal.jsonl`
- Raw cached responses (replay with no API): `outputs/iaa/raw/`
- Human review sheet: `outputs/iaa/human_review_sheet.csv`

## Annotators (exact model ids)

| Family | Model id | temperature | max_tokens |
|---|---|---:|---:|
| openai | `gpt-5.5` | 0.0 | 700 |
| anthropic | `claude-opus-4-1-20250805` | 0.0 | 700 |
| google | `gemini-2.5-pro` | 0.0 | 2048 (14 long rows re-fetched at 4096-6144 to avoid reasoning-token truncation) |

Independence: each annotator received only the codebook + the bare query. No annotator saw gold labels, the registry-guard code, the tuned profiler prompt, or the other annotators.

## Pre-committed stop-loss rule (committed before computing numbers)

- **SUPPORTED (GO):** per-obligation Krippendorff alpha >= 0.70 (especially on the disguised-refusal set) AND model-model Obl-Exact *materially* exceeds the paper's prior single-LLM 0.65.
- **WEAK (NO-GO):** alpha lands in [0.50, 0.65] on >= 2 obligations on the harder disguised-refusal set -> the taxonomy itself becomes the research target; recommend the honest 'proposal' reframe.
- The rule is applied to the ACTUAL numbers in the Verdict section below.

## GapBench stratified subset

Rows with all 3 annotators: **120** across **8** template/category clusters. Bootstrap CIs are cluster-bootstrap by template/category (rows are template-correlated).

Parse health: claude-opus-4-1-20250805 120/120 ok, gemini-2.5-pro 120/120 ok, gpt-5.5 120/120 ok

### Per-obligation agreement (3 annotators)

| Obligation | Prevalence | Krippendorff alpha | alpha 95% CI (cluster) | mean pairwise Cohen kappa |
|---|---:|---:|---:|---:|
| Observation | 0.54 | 0.866 | [0.778, 0.952] | 0.866 |
| Execution | 0.33 | 0.747 | [0.664, 0.849] | 0.750 |
| State | 0.57 | 0.796 | [0.678, 0.865] | 0.797 |
| Action | 0.52 | 0.878 | [0.805, 0.975] | 0.878 |
| Control | 0.58 | 0.875 | [0.801, 0.930] | 0.876 |
| Verification | 0.54 | 0.833 | [0.665, 0.909] | 0.833 |

Reading the table: a prevalence near 1.00 with alpha = n/a means **all three annotators include that obligation on essentially every row** -- that is unanimous agreement (good), not missing data; Krippendorff's alpha is simply undefined when there is no variation to disagree about. A low or negative alpha with mid-range prevalence (e.g. State, Verification on the hard set) is the diagnostic signal: the annotators vary AND do not agree, i.e. that obligation is not a reproducible judgment on these inputs.

### Status agreement (3 categories: supported / unsupported / clarify)

- Krippendorff alpha (nominal): **0.913** [0.000, 1.000]
- Raw full (all-3-agree) agreement: **0.983**
- Mean pairwise raw agreement: **0.989**

Note on the CI: with only 8 template clusters the cluster bootstrap is high-variance and the resample distribution can be narrow and slightly off-centre from the point estimate (the point alpha can fall just outside the percentile interval). Treat the CIs as indicative of between-template variability, not as tight standard errors; the point estimates and the raw-agreement numbers are the primary quantities.

Per-class pairwise confusion (symmetric pooled counts):

| transition | count |
|---|---:|
| clarify->clarify | 20 |
| clarify->supported | 4 |
| supported->clarify | 4 |
| supported->supported | 668 |
| unsupported->unsupported | 24 |

### Capability agreement (micro-F1 across annotator pairs)

- Pooled pairwise micro-F1: **0.907** [0.874, 0.915]
- Mean pairwise micro-F1: **0.906**
  - claude-opus-4-1-20250805|gemini-2.5-pro: 0.899
  - claude-opus-4-1-20250805|gpt-5.5: 0.896
  - gemini-2.5-pro|gpt-5.5: 0.924

### Model-model obligation-exact-set match

- Mean pairwise **Obl-Exact**: **0.647** [0.544, 0.789] (vs prior single-LLM secondary-audit Obl-Exact = 0.65)
  - claude-opus-4-1-20250805|gemini-2.5-pro: 0.650
  - claude-opus-4-1-20250805|gpt-5.5: 0.633
  - gemini-2.5-pro|gpt-5.5: 0.658

### Each annotator vs GOLD

| Model | n | Obl-Exact | Obl micro-F1 | Status agree |
|---|---:|---:|---:|---:|
| `claude-opus-4-1-20250805` | 120 | 0.525 | 0.859 | 0.992 |
| `gemini-2.5-pro` | 120 | 0.383 | 0.817 | 0.992 |
| `gpt-5.5` | 120 | 0.425 | 0.832 | 1.000 |

## Disguised-refusal set (HARDER)

Rows with all 3 annotators: **63** across **9** template/category clusters. Bootstrap CIs are cluster-bootstrap by template/category (rows are template-correlated).

Parse health: claude-opus-4-1-20250805 63/63 ok, gemini-2.5-pro 63/63 ok, gpt-5.5 63/63 ok

### Per-obligation agreement (3 annotators)

| Obligation | Prevalence | Krippendorff alpha | alpha 95% CI (cluster) | mean pairwise Cohen kappa |
|---|---:|---:|---:|---:|
| Observation | 0.98 | 1.000 | [1.000, 1.000] | 1.000 |
| Execution | 0.17 | 0.270 | [0.210, 0.345] | 0.244 |
| State | 0.47 | -0.015 | [-0.183, 0.086] | 0.187 |
| Action | 1.00 | n/a | [n/a] | n/a |
| Control | 1.00 | n/a | [n/a] | n/a |
| Verification | 0.41 | -0.107 | [-0.292, 0.050] | 0.088 |

Reading the table: a prevalence near 1.00 with alpha = n/a means **all three annotators include that obligation on essentially every row** -- that is unanimous agreement (good), not missing data; Krippendorff's alpha is simply undefined when there is no variation to disagree about. A low or negative alpha with mid-range prevalence (e.g. State, Verification on the hard set) is the diagnostic signal: the annotators vary AND do not agree, i.e. that obligation is not a reproducible judgment on these inputs.

### Status agreement (3 categories: supported / unsupported / clarify)

- Krippendorff alpha (nominal): **0.787** [0.759, 0.784]
- Raw full (all-3-agree) agreement: **0.937**
- Mean pairwise raw agreement: **0.958**

Note on the CI: with only 9 template clusters the cluster bootstrap is high-variance and the resample distribution can be narrow and slightly off-centre from the point estimate (the point alpha can fall just outside the percentile interval). Treat the CIs as indicative of between-template variability, not as tight standard errors; the point estimates and the raw-agreement numbers are the primary quantities.

Per-class pairwise confusion (symmetric pooled counts):

| transition | count |
|---|---:|
| clarify->clarify | 34 |
| clarify->unsupported | 8 |
| unsupported->clarify | 8 |
| unsupported->unsupported | 328 |

### Capability agreement (micro-F1 across annotator pairs)

- Pooled pairwise micro-F1: **0.827** [0.811, 0.843]
- Mean pairwise micro-F1: **0.828**
  - claude-opus-4-1-20250805|gemini-2.5-pro: 0.774
  - claude-opus-4-1-20250805|gpt-5.5: 0.872
  - gemini-2.5-pro|gpt-5.5: 0.838

### Model-model obligation-exact-set match

- Mean pairwise **Obl-Exact**: **0.317** [0.267, 0.368] (vs prior single-LLM secondary-audit Obl-Exact = 0.65)
  - claude-opus-4-1-20250805|gemini-2.5-pro: 0.111
  - claude-opus-4-1-20250805|gpt-5.5: 0.540
  - gemini-2.5-pro|gpt-5.5: 0.302

### Each annotator vs GOLD

| Model | n | Obl-Exact | Obl micro-F1 | Status agree |
|---|---:|---:|---:|---:|
| `claude-opus-4-1-20250805` | 63 | 0.016 | 0.777 | 0.905 |
| `gemini-2.5-pro` | 63 | 0.016 | 0.584 | 0.921 |
| `gpt-5.5` | 63 | 0.016 | 0.686 | 0.937 |

## STOP-LOSS VERDICT (applied to actual numbers)

**NO-GO / PREMISE FAILS ON HARD SET -> honest 'proposal' reframe (taxonomy is the research target)**

- Disguised-set model-model Obl-Exact: 0.317 (prior single-LLM = 0.65)
- GapBench-subset model-model Obl-Exact: 0.647
- Disguised per-obligation alpha defined on 4/6 obligations; of those: 1 have alpha>=0.70, 0 are weak [0.50,0.65], 3 below 0.50.

Disguised per-obligation alpha: Observation=1.000, Execution=0.270, State=-0.015, Action=n/a, Control=n/a, Verification=-0.107

=> The premise **FAILS on the hard set**: 3 of the obligations with defined alpha fall BELOW 0.50 (i.e. at or below chance) on the disguised-refusal set -- strictly worse than the pre-committed [0.50,0.65] WEAK band. The committed stop-loss therefore fires in its 'taxonomy is the research target' direction, and then some. Recommend the honest 'proposal' reframe: present the obligation taxonomy and harness as a PROPOSED instrument whose obligation-level reproducibility is partial -- strong on Observation/Action/Control and status, but weak-to-absent on Execution/State/Verification on adversarial scope-confusion inputs -- with the disagreement structure (which obligations reproduce, which do not, and why) as a first-class finding and the human pass as the decisive next step.

## Human pass: ready protocol

The same instrument supports a human study with no code change:
1. Recruit >=3 annotators; give each ONLY `docs/annotation_codebook.md`.
2. Have them fill `outputs/iaa/human_review_sheet.csv` (one row per query; columns for obligations, capabilities, status, and free-text notes).
3. Re-run `scripts.compute_iaa` over the human annotations (same kappa / Krippendorff alpha / micro-F1 / cluster-bootstrap pipeline) to get human IAA.
4. Compare human IAA to this multi-model proxy; adjudicate disagreements; fold confirmed labels back into gold.

