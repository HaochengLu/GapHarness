# Phase 2C GAIA-Transfer Registry-Guarded Report

This is an obligation-transfer run only. It does not claim full GAIA answer-level solving.

## Aggregate Metrics

| N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Obl P | Obl R | Obl F1 | Exact Set |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 200 | 0.56 | 5.56 | 1.48 | 4.08 | 0.89 | 0.44 | 0.42 | 0.253 | 0.814 | 0.386 | 0.10 |

## Harness Selection Metrics

- Guard applied: 0 / 200.
- Unsupported false positives: 0.
- Removed sandbox false `real_world_side_effect`: 0.
- Converted unsupported to supported: 0.

## Category Breakdown

# Category Breakdown

## Success

| Category | gaia_transfer_registry_guarded |
|---|---:|
| gaia_transfer_level_1 | 0.56 |
| gaia_transfer_level_2 | 0.57 |
| gaia_transfer_level_3 | 0.54 |

## Under

| Category | gaia_transfer_registry_guarded |
|---|---:|
| gaia_transfer_level_1 | 0.44 |
| gaia_transfer_level_2 | 0.43 |
| gaia_transfer_level_3 | 0.46 |

## Over

| Category | gaia_transfer_registry_guarded |
|---|---:|
| gaia_transfer_level_1 | 0.85 |
| gaia_transfer_level_2 | 0.91 |
| gaia_transfer_level_3 | 0.91 |


## Qualitative Examples

| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |
|---:|---|---|---|---|---|---:|---:|---|---|---|
| 1 | gaia-validation-review-001 | gaia_transfer_level_1 | Execution,Verification | Execution,Observation,Verification | supported | 7 | 3.00 | missing_capabilities:contract_check,dependency_or_constraint_failure | - | If Eliud Kipchoge could maintain his record-making marathon pace indefinitely, how many thousand ... |
| 2 | gaia-validation-review-002 | gaia_transfer_level_1 | Control,Observation | Observation,Verification | supported | 6 | 3.00 | missing_obligations:Control,missing_capabilities:permission,dependency_or_constraint_failure | - | An office held a Secret Santa gift exchange where each of its twelve employees was assigned one o... |
| 3 | gaia-validation-review-003 | gaia_transfer_level_2 |  | Observation,Verification | supported | 4 | 4.00 | - | - | A paper about AI regulation that was originally submitted to arXiv.org in June 2022 shows a figur... |
| 4 | gaia-validation-review-004 | gaia_transfer_level_2 |  | Observation,Verification | supported | 6 | 6.00 | - | - | The attached spreadsheet shows the inventory for a movie and video game rental store in Seattle, ... |
| 5 | gaia-validation-review-005 | gaia_transfer_level_3 | State | Execution,Observation,Verification | supported | 8 | 7.00 | missing_obligations:State,missing_capabilities:durable_state,dependency_or_constraint_failure | - | In July 2, 1959 United States standards for grades of processed fruits, vegetables, and certain o... |
| 6 | gaia-validation-review-006 | gaia_transfer_level_3 | Observation | Execution,Observation,Verification | supported | 9 | 7.00 | - | - | What is the average number of pre-2020 works on the open researcher and contributor identificatio... |
| 7 | gaia-validation-review-007 | gaia_transfer_level_1 | Observation,Verification | Execution,Observation,Verification | supported | 7 | 2.00 | missing_capabilities:contract_check,dependency_or_constraint_failure | - | How many studio albums were published by Mercedes Sosa between 2000 and 2009 (included)? You can ... |
| 8 | gaia-validation-review-008 | gaia_transfer_level_1 |  | Execution,Observation,Verification | supported | 9 | 9.00 | - | - | Each cell in the attached spreadsheet represents a plot of land. The color of the cell indicates ... |
| 9 | gaia-validation-review-009 | gaia_transfer_level_2 |  | Execution,Observation,Verification | supported | 7 | 7.00 | - | - | I’m researching species that became invasive after people who kept them as pets released them. Th... |
| 10 | gaia-validation-review-010 | gaia_transfer_level_2 | Execution,Observation,Verification | Execution,Observation,Verification | supported | 7 | 1.00 | missing_capabilities:contract_check,workspace_inspection,dependency_or_constraint_failure | - | Using the Biopython library in Python, parse the PDB file of the protein identified by the PDB ID... |
| 11 | gaia-validation-review-011 | gaia_transfer_level_3 |  | Observation | supported | 4 | 4.00 | - | - | Assuming scientists in the famous youtube video The Thinking Machine (Artificial Intelligence in ... |
| 12 | gaia-validation-review-012 | gaia_transfer_level_3 |  | Observation,Verification | supported | 5 | 5.00 | - | - | Which of the text elements under CATEGORIES in the XML would contain the one food in the spreadsh... |
| 13 | gaia-validation-review-013 | gaia_transfer_level_1 |  | Execution | supported | 2 | 2.00 | - | - | Here's a fun riddle that I think you'll enjoy.  You have been selected to play the final round of... |
| 14 | gaia-validation-review-014 | gaia_transfer_level_1 | Observation | Execution,Observation,Verification | supported | 8 | 6.00 | missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | Review the chess position provided in the image. It is black's turn. Provide the correct next mov... |
| 15 | gaia-validation-review-015 | gaia_transfer_level_2 |  | Execution | supported | 2 | 2.00 | - | - | If we assume all articles published by Nature in 2020 (articles, only, not book reviews/columns, ... |
| 16 | gaia-validation-review-016 | gaia_transfer_level_2 | Observation | Execution,Observation,Verification | supported | 8 | 6.00 | missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | When you take the average of the standard population deviation of the red numbers and the standar... |
| 17 | gaia-validation-review-017 | gaia_transfer_level_3 | Observation | Execution,Observation,Verification | supported | 8 | 6.00 | missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | In the NCATS PubChem compound database for Food Additive Status classification, find the compound... |
| 18 | gaia-validation-review-018 | gaia_transfer_level_3 | Observation | Execution,Observation,Verification | supported | 8 | 6.00 | missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | In the NIH translation of the original 1913 Michaelis-Menten Paper, what is the velocity of a rea... |
| 19 | gaia-validation-review-019 | gaia_transfer_level_1 | Execution,Verification | Observation | supported | 4 | 0.00 | missing_obligations:Execution,missing_capabilities:contract_check,execution,execution_log,dependency_or_constraint_failure | - | What was the volume in m^3 of the fish bag that was calculated in the University of Leicester pap... |
| 20 | gaia-validation-review-020 | gaia_transfer_level_1 | Observation | Observation | supported | 4 | 2.00 | missing_capabilities:workspace_inspection,dependency_or_constraint_failure | - | As a comma separated list with no whitespace, using the provided image provide all the fractions ... |

## Interpretation Boundary

GAIA-Transfer v1.0 labels evaluate obligation prediction and harness selection. They do not evaluate final answer correctness against GAIA final answers.
