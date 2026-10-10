# Milestone 1 requirements audit — 10 October 2026

## Verdict

**The local implementation and report are complete; submission is not yet verified.**
The supported CSV repairs, Q3 denominator correction, calendar/roster feature
changes and interpretation corrections have been applied. Remaining uncertainty
is documented rather than filled with invented race facts. Submission still
requires verified, accessible Kaggle/GitHub links. The four supplied team names
and student IDs are included in the report and README.

The eight-page brief was reread against the current files on 10 October 2026.
All eight deliverable categories are present locally. This is not a claim that
the revised holdout is still untouched: earlier test scores were reviewed during
development, so that part of the brief's unseen-test expectation needs the
qualification documented below. The final models still choose hyperparameters,
thresholds and the inference model using validation only.

The assessment uses the supplied eight-page assignment PDF, the notebook,
supplied CSVs and regenerated artifacts. Assignment instructions are criteria
being assessed; they were not treated as instructions to publish or submit.
Scientific repairs use CSV evidence, with four starting-grid corrections checked
against official F1/FIA records after the team reported its TA had advised online
verification. Sources, access dates, original values and changes are documented
in notebook Section 3.5, the report and `GRID_RECONSTRUCTION.md`.

## What was verified after repairs

- Local `.venv`: Python **3.12.15**, installed dependencies and **ipykernel**;
  registered **F1 Podium (.venv, Python 3.12)** for VS Code.
- All **84 code cells** executed top to bottom without notebook errors.
- Fourteen primary keys and all **23 declared foreign-key relationships** pass.
  The additional semantic audit covers fifteen cross-table/column issue types.
- Raw files and in-memory raw copies remain unchanged. Cleaning uses copies,
  preserves source values and exports repair records and unresolved flags.
- **378 independent artifact checks** pass, including labels, modeling grain,
  forty sampled prior-history calculations, repairs, Q3 eligibility/rates,
  training-only feature treatments, metrics, thresholds and selected model.
- **8,970 rows**, **428 races**, **28 features**, **1,284 podium labels**;
  **60 main model trials**, **52 ablation configurations**, **three order
  experiments**, and **48 notebook plots**.
- Report HTML includes all 48 plots. The regenerated PDF contains the current
  notebook explanations and results. Content checks are not a complete visual
  review of every page break and table.

For independent artifact checks, run `%run scripts/validate_artifacts.py` in
the selected project kernel, or `.venv/bin/python scripts/validate_artifacts.py`.
Detailed results are in `outputs/validation_summary.json`. Passing checks proves
execution and consistency under the documented conventions, not that every
historical source value is correct.

## Requirements mapped to evidence

Page numbers refer to the supplied assignment PDF; section numbers refer to
`f1_podium_prediction.ipynb`.

### Eight deliverables in the brief (pages 5–6)

| Deliverable | Current evidence | Status |
|---|---|---|
| 1. One sectioned Run All notebook containing the complete pipeline | `f1_podium_prediction.ipynb`; 84 executed code cells, no errors | Complete locally; Kaggle execution unverified |
| 2. EDA with plots | Sections 2 and 4; before/after cleaning, computed audits and distributions | Present |
| 3. Unique driver–race modeling table with documented duplicates and pre-race features | `outputs/modeling_table.csv`; 8,970 entries, 28 features; Sections 3 and 6 | Present; retrospective input-availability assumptions disclosed |
| 4. Model comparison and justified primary/secondary metrics | Section 11; six models/reference variants on train, validation and test; ROC-AUC, AP, F1, precision, recall, Brier, accuracy | Present; revised test is exploratory, not a new untouched evaluation |
| 5. Feature-group ablations and at least two preprocessing-order experiments | Sections 9.2 and 12; 52 ablation configurations, three order experiments | Present |
| 6. Plotted and interpreted global/local explanations | Section 13; permutation importance, SHAP, LIME; causal claims explicitly excluded | Present |
| 7. Inference function on complete and partially missing records | Section 14; 28-feature, 22-feature and grid-only examples | Present |
| 8. Analytical report with all three questions, figures, features/cutoff and limitations | `report.pdf`; 42 pages, current notebook explanations/results and four team names/IDs | Present locally; final visual review recommended |

The page-8 submission items are separate: an accessible Kaggle notebook link,
an accessible GitHub repository containing this version, and the PDF report.
The PDF exists locally; no Kaggle publication URL is recorded and current
repository changes remain uncommitted/unpushed. A GitHub browser fetch failed,
so evaluator access could not be verified; this does not establish that the
repository is private or inaccessible to the team.

### Detailed requirement mapping

| Requirement | PDF pages | Implementation/evidence | Assessment |
|---|---|---|---|
| Correct binary target and driver–race unit | 1–3 | Opening; Sections 3.4, 6.4; raw-label agreement | Met |
| All fourteen relational tables | 1 | Sections 1–2; `Data/` | Met |
| EDA before and after cleaning, with plots | 2 | Sections 2 and 4 | Met |
| Sentinel handling and semantic typing | 2 | Sections 2.1–2.2, 3.1–3.2 | Met |
| Unique `(raceId, driverId)`; explained duplicate rule | 2 | Sections 2.5, 3.4; three rule comparisons | Met, with documented historical caveat |
| Primary/foreign-key audits | 2 | Sections 2.3–2.4; independent checks | Met |
| Immutable raw files; cleaning on copies | 2 | `RAW`/`CLEAN`; Sections 1.1 and 15.2 | Met |
| Q1: circuits, eras, grid versus qualifying | 2 | Section 5 Q1; joins, rates, plots | Met; observed changes distinguished from proof of underlying change |
| Q2: home country controlling for starting position | 3 | Section 5 Q2; mapping, stratification and logistic check | Met; conclusion states no detectable effect under the controls |
| Q3: mechanical retirements per race start, two eras | 3 | Section 5 Q3; status classification and sensitivity | Repaired; marked non-starts excluded, unresolved starts quantified with sensitivity |
| Each question has multi-hop joins, grain, missingness and cutoff explanation | 2–3 | Section 5 markdown and computed answers | Met; Q3 documents the estimated denominator and its limits |
| Feature evidence and preserved trials | 3, 6–7 | Sections 8.1–8.4; plots, correlations and comparisons | Met |
| Leakage-safe form and standings | 1, 5, 7 | Shifted histories; previous-round joins; six-race corruption test | Outcome-history and future-round invariance checks pass; archive caveat below |
| Grid/qualifying and context valid at cutoff | 1, 5 | Section 6.2 | Season-length/result-count dependencies removed; archived entry/grid snapshots unavailable |
| Justified train/validation/test split | 3, 7 | Section 7; chronological seasons and disjoint races | Met |
| At least two statistical models plus shallow NN, same rows/features | 3 | Logistic regression, random forest, boosting; 1–2-layer PyTorch NN | Met; three statistical model families present |
| Appropriate baseline; at least three modeling attempts | 6 | Default logistic baseline; 60 logged attempts | Met |
| Explain model mechanisms and limitations | 6–7 | Section 10 descriptions; Section 15 limitations | Met |
| ROC-AUC, PR summary and F1 on train/validation/test | 3–5 | Section 11; 18-row comparison CSV | Met; PR summary is average precision |
| Five metrics in deliverable; primary/secondary justification | 5 | ROC-AUC, AP, F1, precision, recall; Section 10.1 | Met; also reports Brier and accuracy |
| Hyperparameters and thresholds selected without test labels | 4 | Sections 10 and 11; threshold consistency; validation winner | Met in final-model selection |
| Feature-group ablation for each group | 4–5 | Section 12; six groups × four models | Met |
| At least two preprocessing-order experiments | 5, 7 | Section 9.2; three experiments | Met; deliberately invalid development-only fitting excludes test rows |
| Global permutation importance and SHAP | 4–5, 8 | Section 13; statistical model and NN | Met |
| Local LIME and/or SHAP, plotted and interpreted | 4–5, 8 | Two cases, both methods | Met |
| Explainability distinguished from causality | 5 | Sections 13 and 15 | Met explicitly |
| Inference on complete and partially missing records | 5 | Section 14; 28-feature and 22-feature records; grid-only example | Met |
| One logical, sectioned Run All notebook | 5–6 | Fresh successful execution | Met locally; Kaggle execution unverified |
| Analytical PDF with questions, figures, features and limitations | 5–7 | `report.pdf`, generated from current execution | Present, regenerated after repairs; all four supplied members/IDs included |
| Accessible Kaggle notebook link | 8 | No project publication URL supplied/found in README | **Unverified** |
| Accessible GitHub repository link | 8 | Configured remote: `noorhossameldin/f1-podium-prediction` | **Unverified public/evaluator accessibility** |
| Team members prepared to justify choices | 6 | `PROJECT_WALKTHROUGH.md` provides study checkpoints | Cannot certify from source files |

The deliverables refer to “all five metrics,” although the earlier metric table
names three. The implementation covers both readings by reporting ROC-AUC, AP,
F1, precision and recall.

## Applied corrections

See `FIXES_AND_REMAINING_ISSUES.md` for the before/after decisions and
`DATA_CONSISTENCY_AUDIT.md` for original CSV evidence.

- Swapped `stop`/`lap` in seven identified Monaco 2024 pit records.
- Reconciled ten qualifying constructor IDs and 32 car numbers to canonical
  result-entry metadata; kept originals. Removed four identical 2015 alias
  constructor aggregates without merging constructor histories globally.
- Represented 258 unranked fastest laps as missing in a derived column.
- Checked eight source-conflicted grid entries against official starting grids
  following reported TA guidance. Corrected four cleaned slots, confirmed four
  unchanged, and resolved all four modeled-era clashes. Main `grid_pos` and
  `grid_drop` now use verified values; original values/source flags and all links
  are preserved. Earlier candidate, opposite and missing-input policies remain
  refitted sensitivity comparisons. See `GRID_RECONSTRUCTION.md`.
- Q3 separates failure labels from start evidence, excludes marked non-starts,
  preserves positive-lap starts and quantifies 112 uncertain zero-lap entries.
  The same convention supplies past-only constructor reliability.
- Replaced eventual `season_progress` with known `round_number` and post-race
  `field_size` with `qualifying_field_size`. Renamed misleading pit-lane and
  driver-start count features to `no_grid_slot` and historical entry counts.
- Corrected overstatements about home advantage, rank changes, seed variation,
  race-constant predictors, long-stop causes and explanations of prediction errors.
- The deliberately invalid preprocessing example now uses development data only.
  All final pipelines fit preprocessing on training only; choices use validation.

## Remaining scientific limitations and recommendations

Official sources now resolve the four identified grid clashes. The supplied CSVs
cannot reconstruct every missing pit stop, classification/timing mismatch or
exact start of a zero-lap entry. Keep the
provenance flags and publish the chosen conventions/sensitivity results. Obtain
reliable entry/start/timing records before replacing unresolved values. Exact
mechanical-failure causes and continuity between renamed organisations also need
additional evidence. The assignment's `positionOrder <= 3` target remains intact.

Round number and qualifying entry count remove the identified future-data
proxies, but the dataset still lacks archived pre-race entry/grid publication
snapshots. Describe this retrospective availability assumption. To validate live
forecasting, build rows from a timestamped pre-race entry list.

This revision follows an audit of all seasons, including test-era source records,
and earlier test scores had already been inspected. **The revised 2022–2024
holdout is exploratory**, even though hyperparameters and thresholds still use
validation only. Freeze the current rules and use unseen later races for a new
untouched final evaluation. Do not select further changes on that new test.

Leakage restrictions apply to training, validation and test rows. Every row's
inputs must respect its own race cutoff; preprocessing is fitted on training,
selection uses validation, and test evaluates the frozen choices. Earlier test
race outcomes can enter features for later test races only under the stated
race-by-race forecasting protocol.

## Remaining submission work

1. Run the notebook in Kaggle with the intended dataset, save/publish the version
   and add its evaluator-accessible link to README. Local execution cannot
   verify Kaggle compatibility or publication.
2. Commit/push the final reviewed files and verify evaluator access to the GitHub repository
   `https://github.com/noorhossameldin/f1-podium-prediction` and include both links
   in the submission. A public-page fetch could not verify accessibility. Final review changes are
   still local and must be committed/pushed before that link represents this version.
3. Review PDF page breaks and table legibility and practise the checkpoints in
   `PROJECT_WALKTHROUGH.md`.

The PDF states **18 October 2026, 11:59 pm** as the deadline. This is the supplied
brief's date; a later course announcement was not checked. The README and project
report are prepared locally; no publishing or submission was performed.

## Current result to explain at evaluation

Gradient boosting is selected by validation AP **0.7555**, with **43** rounds,
depth **4**, learning rate **0.1**, L2 **0.0** and threshold **0.3906**.
Its revised holdout AP is **0.6883**, ROC-AUC **0.9374**, F1 **0.6651**, precision
**0.6540** and recall **0.6765**. The logistic baseline reaches AP **0.6959**;
the grid-only rule reaches **0.6465**. The selected model need not win on test,
and these scores do not prove that extra complexity outperforms logistic
regression on future seasons. Selecting a replacement based on the test winner
would compromise that evaluation further.
