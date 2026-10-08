# Repairs and remaining issues — 8 October 2026

The supported fixes are applied in `f1_podium_prediction.ipynb`. They use the
supplied CSVs. All fourteen raw files stay unchanged; repaired tables, original
values and audit flags are saved under `outputs/`.

## What was fixed, how we found it, and why

| Issue | Evidence that exposed it | Applied treatment and reason |
|---|---|---|
| Seven swapped Monaco 2024 pit records | Stop numbers such as 70 on lap 2 contradict their times and neighbouring stops | Swap `stop` and `lap` only in those seven rows. All six affected sequences become contiguous; no duplicate stop keys appear. Keep original fields. |
| Ten qualifying constructor mismatches | Same driver/race uses 206 in qualifying but 209 in results; 2015 standings agree with 209 | Use the matching result entry as canonical metadata. Preserve original IDs and repair flags. This is a scoped reconciliation policy, not a global merger of teams. |
| 32 conflicting car numbers | Qualifying and result metadata disagree for the same entry | Reconcile cleaned qualifying to result-entry numbers and preserve both. The policy establishes consistency; it does not prove which conflicting number was physically used. |
| Four duplicate 2015 constructor aggregates | Alias 206 rows duplicate native 209 rows with identical zero points and missing status | Omit only the four duplicate alias aggregates. Keep the native records and all other constructor history. Total points stay unchanged. |
| 258 fastest-lap ranks equal zero | Each lacks a fastest-lap time; zero is not a valid first-or-later rank | Add `fastest_lap_rank`, representing zero as missing. Preserve raw `rank`. |
| Eight disputed grid entries | Four modern races each assign the same positive grid slot to two drivers | Preserve and flag both source entries; leave their main grid predictors missing for training-only imputation. Keep hypothetical qualifying-order and opposite assignments as refitted sensitivity experiments only. The correct assignments remain unknown. |
| Q3 counted withdrawals as mechanical retirements/starts | Zero-lap `W` entries can carry component-failure labels; historical withdrawals can also have positive laps | Separate failure type from start eligibility. Positive laps confirm a start; zero-lap withdrawal/non-qualification markers exclude an entry. Other zero-lap entries remain uncertain. |
| Unknown status labels became mechanical by default | Failure classification used a fallback instead of positive evidence | Use an explicit mechanical allowlist; unknown labels default to ambiguous. Keep strict/broad failure-type sensitivity. |
| Reliability denominator did not follow Q3 | Historical mechanical failures were divided by entries including marked non-starts | Use the same start-eligibility convention for previous-race constructor reliability, aggregating both cars before shifting. |
| Future season length entered features | `round / max(round)` depends on the eventual calendar | Replace with current `round_number`. Changing strictly later round numbers no longer changes sampled current-race features. |
| Field size came from post-race records | Result-entry count was a retrospective roster proxy | Replace with `qualifying_field_size`, the count already recorded in qualifying. Archived entry-list availability remains a limitation. |
| Feature names implied facts the CSV did not establish | Grid zero is not uniquely a pit-lane start; driver history counts include non-start entries | Use `no_grid_slot`, `drv_career_entries` and `drv_circuit_entries`, with definitions matching the calculations. |
| An order experiment used test covariates | The deliberately invalid preprocessing comparison fitted on all splits | Restrict that negative example to train + validation development data. Final models still fit imputation/scaling on train only. |
| Some conclusions overstated the evidence | Non-significant estimates, seed variation and descriptive explanations were treated as proof | Qualify home/ranking effects, distinguish seed noise from statistical uncertainty, avoid guessed red-flag causes, and label revised holdout results honestly. |

`outputs/cleaning_repairs.csv` contains each of the **53 direct row-level
reconciliation actions** (7 + 10 + 32 + 4). Derived rank changes and unresolved
grid flags are represented in their exported columns and
`outputs/cleaning_repair_summary.csv`. The original-source audit flags remain
available even when a cleaned representation has been repaired.

The unresolved-grid decision and exploratory reconstruction are documented in
`GRID_RECONSTRUCTION.md` and notebook Sections 3.5 and 12.1. Main grid numbers
remain unchanged; hypotheses are separate sensitivity experiments only.

## What cannot be reconstructed reliably from these CSVs

These issues have usable mitigations, but the current data cannot supply every
true replacement value.

| Unresolved issue | Current handling | Recommended resolution |
|---|---|---|
| True grid slots for eight entries | Original slots preserved and conflicts flagged; main grid inputs missing, with hypothetical assignments used only for sensitivity | Obtain a corrected final-grid record for each of the four races. Qualifying order alone cannot account for penalties or sprint-derived grids. |
| 112 uncertain zero-lap entries in Q3 | Main estimate assumes they started; positive-lap-only estimates and entry-eligibility bounds reported by era and constructor | Obtain start/DNS classifications or additional timing evidence. Until then retain sensitivity; do not declare all zero-lap rows DNS. |
| Two pit histories begin at stop 2 | Marked `incomplete_stop_history`; existing records retained | Obtain the missing original pit record or documentation of the numbering convention. Do not invent stop 1 or renumber by assumption. |
| 12 fastest-lap indices exceed classified laps | Bundle flagged; values retained and excluded from prediction inputs | Compare trusted timing records with the classification and resolve the entire fastest-lap bundle together. A guessed index or time would create new inconsistencies. |
| 37 timing histories exceed result lap totals; three pit rows exceed one disqualified driver's classified total | Cross-table flags retained; timing evidence and classification remain distinct | Establish whether fields mean observed or officially credited laps before correcting them. Do not truncate timing logs or overwrite classification solely to force equality. |
| 20 lapped-status/total discrepancies | Flagged; source fields retained | Verify race-level classification conventions and correct only entries with supported evidence. |
| Three older constructor aggregates have no matching result team | Flagged after the four supported 2015 alias duplicates are removed | Obtain the appropriate race-entry/team identity record; a broad constructor-ID replacement could join distinct histories or double-count points. |
| 13 historical `position`/`positionOrder` disagreements | Both retained, with a flag; target uses the assignment's `positionOrder <= 3` | Document the ordering convention. Do not change the target to another field to make the columns match. |
| Failure label does not identify the initiating cause | Explicit status-label policy plus strict/broad sensitivity | Keep the analysis about recorded failure labels. Establishing whether crash damage caused a later component failure needs causal evidence outside these fields. |
| Renamed teams have separate constructor IDs | No unproven global merges | If organisational continuity matters, provide a versioned, era-specific mapping with a stated analytical purpose. |
| Retrospective entry/grid availability | Known-current-round and qualifying-count proxies used; archive limitation stated | For live forecasting, construct the prediction population from timestamped pre-race entries and grid publications. These snapshots are absent from the supplied data. |
| Earlier test data/results have already been reviewed | Updated 2022–2024 scores labelled exploratory; settings/thresholds still selected on validation | Freeze repairs and evaluate genuinely unseen later races for a fresh final test. Re-running the same repaired test does not restore its untouched status. |

## How much Q3 changed

The repaired entry-level rule excludes **28 marked non-starts** in 2014–2024
and retains positive-lap withdrawals as starts. It leaves **83** uncertain
zero-lap entries in the first era and **29** in the second.

| Era | Main rate: unresolved entries assumed to start | Positive-lap-only rate | Start-eligibility bounds |
|---|---:|---:|---:|
| 2014–2021 | 8.81% | 8.85% | 8.64–9.02% |
| 2022–2024 | 5.33% | 5.22% | 5.11–5.43% |

The bounds vary which uncertain entries started, while holding the strict
failure-label classification fixed. They are **not confidence intervals** and
do not include every possible status-label error. The separate broad-label
analysis addresses another source of uncertainty.

Leclerc's Monaco 2021 row is excluded because the supplied CSV has zero laps
and `positionText=W`. Räikkönen's Malaysia 2017 row remains uncertain because
the CSV has zero laps and `positionText=R`; no internet DNS correction was
imported. This is why a source-grounded repair cannot make both entries equally
certain.

## Verification and submission

The repaired notebook executes **84 code cells**, generates **48 plots**, and
passes the independent artifact validator. Model inputs remain **28 features**
across **8,970 entries**. The report and study walkthrough are updated to match.
Run `%run scripts/validate_artifacts.py` in the selected project kernel to check
the exported evidence again.

The local VS Code environment already contains `ipykernel`. Select
**F1 Podium (.venv, Python 3.12)** or this folder's `.venv/bin/python`, then use
**Run All**. Installing into that environment does not add packages to a
different globally selected Python interpreter.

The four supplied team names and IDs are included in the report and README.
Before submission, execute/publish the intended Kaggle notebook and verify evaluator access to Kaggle/GitHub links. These need
information or external publication not present in the local project; the
required technical implementation and local validation are complete under the
documented data conventions. No audit can certify that a historical dataset
contains no additional errors.
