# Milestone 1 final requirements review — 14 October 2026

## Verdict and scope

We reread all eight pages of the supplied **CSEN903 - Project - MS1 Description.pdf**
and checked the current notebook, exported tables and PDF against the objectives,
eight deliverables, evaluation expectations and checkbox checklist.

**All eight deliverable categories are implemented locally.** A fresh top-to-bottom
execution of all **84 code cells** completed successfully in **117 seconds**, and
**445 artifact checks** pass. The **24-page report includes all 48 notebook plots**,
with explanations: 30 in the main analysis and 18 in Appendices A–I. Team 63 and
all four members/IDs appear in the report, with each member on a separate line.

This is not an unconditional claim that every requirement is fully satisfied:

1. **Unseen-test qualification:** earlier test scores were inspected and source
   repairs followed a full-data audit. The revised 2022–2024 holdout is exploratory,
   not a fresh untouched test. Final model settings, stopping and thresholds still
   use training/validation only. Re-running the same seasons does not undo prior
   exposure. A genuinely unseen later period is needed for a fresh final test.
2. **GitHub delivery is not verified:** the remote is
   `https://github.com/noorhossameldin/f1-podium-prediction.git`. An unauthenticated
   read requested a username and could not complete. This does not establish
   whether the cause is privacy, permissions or another access issue. Current
   local report/notebook changes are uncommitted; the final version must be
   uploaded and evaluator access checked before submission.
3. **Team readiness requires preparation:** files cannot certify that every
   member can explain the choices. `PROJECT_WALKTHROUGH.md` supplies study prompts.

**The Kaggle link/publication check is excluded at the user's request.** We did
not publish, push, submit, change sharing, or contact anyone during this review.

## Source brief and verification evidence

- Assignment: `/Users/masry/Downloads/CSEN903 - Project - MS1 Description.pdf`.
- Assignment SHA-256:
  `aa5d6cde88b5c43e045c66fb7015373750da1dbd7fd3b3dc8b79482822db85a5`.
- Fresh execution: `.venv/bin/python scripts/run_notebook.py`; 84/84 cells,
  no execution-error outputs. The runner saves the notebook only on success.
- Report: `.venv/bin/python make_report.py`; **24 pages**, no section spillover,
  every notebook figure included once. All pages were rendered for layout review.
- Validation: `.venv/bin/python scripts/validate_artifacts.py`; **445 checks pass**.
- Figure inventory and source-image hashes: `outputs/report_manifest.json`.
- Data/metric checks and raw hashes: `outputs/validation_summary.json`.
- All 14 raw CSV hashes also match the committed audit's recorded hashes.

Assignment wording is treated as criteria to assess, not as authorisation to
publish or submit. A passing check establishes consistency under our documented
conventions; it does not prove every historical record is correct.

## Eight deliverables (brief page 5)

Notebook section numbers below refer to `f1_podium_prediction.ipynb`; report page
numbers refer to the rebuilt 24-page `report.pdf`.

| Deliverable | Notebook and saved evidence | Report evidence | Assessment |
|---|---|---|---|
| 1. One sectioned Run All notebook with the complete pipeline | Sections 1–15; 84 freshly executed code cells; no errors | Main analysis and Appendices A–I | Met locally |
| 2. EDA supported by plots | Sections 2 and 4; before/after missingness, types, keys, grain, durations, coverage and target | Pages 1–2, Appendices A–D | Met |
| 3. Unique driver–race table; documented duplicates and pre-race features | Sections 3 and 6; `outputs/modeling_table.csv`; 8,970 rows, 428 races, 28 features, 1,284 positives | Pages 2 and 7; Appendix B | Met under stated availability/history assumptions |
| 4. Statistical/NN model comparison, required metrics and primary/secondary rationale | Sections 10–11; 18 model/split rows in `outputs/model_comparison.csv`; AP, ROC-AUC, F1, precision, recall, Brier, accuracy | Pages 10–11 and Appendix I; all seven metrics on train/validation/holdout | Implemented; unseen-test qualification above |
| 5. Group ablation and at least two preprocessing-order experiments | Sections 9.2 and 12; three order experiments, 52 ablation configurations across four model families | Pages 9 and 12 | Met |
| 6. Global and local explanations, plotted and interpreted | Section 13; permutation, SHAP, two local cases with both SHAP and LIME | Pages 13–14 | Met; causal claims explicitly excluded |
| 7. Inference demonstrated on complete and partially missing records | Section 14; 28-input, 22-input and one-input examples; unknown-name rejection | Page 15 | Met |
| 8. Analytical PDF: three answers, features/cutoff and limitations | `report.pdf`, `report_content.md`, source notebook and exported results | 24 pages; all 48 plots and interpretations | Met locally |

The brief names three headline metrics earlier, then asks for “all five metrics”
in the deliverables. We cover both readings by including ROC-AUC, AP, F1,
precision and recall, plus Brier and accuracy. AP is explicitly identified as
average precision rather than trapezoidal PR integration.

## Objective and checkbox checklist (brief pages 1–4, 6–8)

| Requirement | Evidence and review finding | Status |
|---|---|---|
| Binary podium target and one driver entering one race | `positionOrder <= 3`; target matches original labels; unique `(raceId, driverId)` | Met |
| All 14 relational tables considered | Raw-table inventory; key audit; source/use/cutoff table | Met |
| EDA before and after cleaning; implementation and plots | Programmatic audits, distributions and before/after comparison; report contains the original diagnostic plots | Met |
| Sentinels including literal `\N`; semantic dates/durations | Both `\N` and empty strings handled; numeric/nullable-ID typing; seconds parser checked against lap milliseconds | Met |
| Duplicate driver–race entries checked, resolved and justified | 85 pairs, 91 surplus rows; three rules compared; credited-podium preservation and historical cost stated | Met |
| Primary keys non-null/unique; foreign keys reconcile | 14 primary-key and 23 foreign-key checks; semantic conflicts checked separately | Met |
| Raw files immutable; cleaning on copies | End-of-run file/frame checks and comparison with committed raw hashes | Met |
| Q1 multi-hop joins; circuits, hybrid-era comparison, grid versus qualifying | Results/calendar/circuits/qualifying joins; eligible circuit counts, Wilson intervals, ranking and definition sensitivity | Met |
| Q2 multi-hop joins; home-country mapping and starting-position control | Nationality/country mapping; stratified grid, decade, driver and constructor-season checks; logistic cross-check | Met |
| Q3 multi-hop joins; mechanical failures excluding crash/driver/regulation labels | Status allowlist, separate start-eligibility rule, constructor × era aggregation, strict/broad labels and start bounds | Met as a documented CSV-based estimate; exact causes/starts unresolved |
| Each answer has grain, missingness, cutoff explanation and results | Written question methods and computed Markdown answers; report pages 3–6 and Appendix E | Met |
| Feature selection justified with plots/correlations/trials | Section 8; single-feature evidence, curves, correlations, group addition and encoding/inclusion trials retained | Met |
| Plot effect of selected features | Training-only binned relationships and ranking plots; report page 8 and Appendix F | Met |
| Leakage-safe form and standings | Shifted history; aggregate team race before shifting; previous-round standings; negative-control and future-calendar checks | Met for tested dependencies; publication-archive assumption disclosed |
| Effects of preprocessing on distributions/ranges/values | Histograms, before/after table and range figure | Met |
| Preprocessing-order experiments reported | Split/fit, split/history, impute/scale; alternatives use development data only | Met; deliberately invalid order clearly labelled |
| Appropriate training/validation/testing split and justification | Chronological, race-disjoint seasons; all models use same splits | Met |
| At least two statistical ML models and shallow network | Logistic regression, random forest, gradient boosting, 1–2-layer PyTorch NN | Met |
| Same rows and features across required learned models | Shared 28-feature modeling table and preprocessing; grid-only rule is an additional reference | Met |
| Baseline is statistical ML or shallow FFNN | Default logistic regression; grid-frequency reference is additional | Met |
| At least three distinct modeling attempts; comparisons visible | 60 logged baseline/hyperparameter attempts, separate model sections and displayed trial tables; feature/preprocessing variants also compared | Met |
| Model mechanism and limitations explained | Linear log-odds, averaged trees, sequential boosting and shallow network; complexity/regularisation/stopping discussed | Met |
| Metrics on training/validation and unseen test | All required split scores are computed and reported | Scores present; fresh unseen-test condition qualified |
| Hyperparameters/thresholds use only train/validation | Selection functions and frozen thresholds; boosting/network stopping uses validation | Met in final-model selection; repeated validation reuse disclosed |
| Training/validation performance and plots | Tuning/loss curves, score panels, all-trial search; report page 10 and Appendices G–I | Met |
| Feature-group ablation retrains, one group at a time | Six groups × four families; drop-group and group-only fits; matched NN seeds | Met |
| Global permutation importance and SHAP | Both selected statistical model and network; feature/group permutation; SHAP shares and distributions | Met |
| Local explanation including LIME | Two selected cases, SHAP waterfalls and LIME with interpretation | Met, including checklist page 8's LIME wording |
| Explainability distinguished explicitly from causality | Report page 13 states that importance means model reliance, not cause; examples and limitations repeat the distinction | Met |
| All plots and answers in notebook and structured report | Each of the 48 notebook figures appears exactly once in the PDF; Appendices A–I explain 18 additional diagnostics | Met after this review's report revision |
| Logical sectioning, Markdown justification, no hidden manual modification | Fresh top-to-bottom execution and notebook source review | Met locally |
| Every member can justify choices using evidence | Study walkthrough and report provide explanations; individual preparation cannot be tested from artifacts | Team action |

## Repairs made during this review

- Restored all 18 omitted diagnostic plots to the PDF in nine explained appendix
  pages. The previous 15-page PDF plus a separate HTML gallery did not establish
  compliance with page 7's “all plots” requirement. The new report is one PDF.
- Added a build-time check that every notebook figure is included once and a
  validation check that the PDF contains all 48 images.
- Rebuilt the report and manifest from the freshly executed notebook, resolving
  the earlier stale notebook/report fingerprint mismatch.
- Corrected stale prose that said the verified grid entries were still masked.
- Corrected the partially missing inference description from five to six fields.
- Clarified ROC-AUC, the SHAP reference/output scale, conditional ablation effects,
  missing-indicator evidence, and the revised holdout's exploratory status.
- Aligned notebook TA wording with the report's team voice, while preserving
  dated source-verification records in provenance exports.

The computational model configurations, target and split boundaries did not
change. Freshly generated model scores match the reported rounded results.

## Important scientific assumptions to retain

1. The historical best-result shared-drive rule uses the outcome. Its affected
   rows end in 1978, outside modeling, but it can affect long-history summaries.
2. Grid corrections follow official starting-grid evidence and TA guidance;
   model scores do not establish historical truth. Original values and sources
   remain in exports. Other gaps are not automatically filled.
3. Mechanical rates describe recorded labels under stated start conventions.
   Uncertain zero-lap entries and ambiguous labels have separate sensitivity
   analyses. Eligibility bounds are not statistical confidence intervals.
4. Driver form counts entries, including non-starts; Q3 reliability uses assumed
   starts. These denominators are not interchangeable.
5. Earlier races may update history before later validation/holdout races. This
   matches race-by-race forecasting, not a whole-season forecast made in advance.
6. Retrospective entries/grids stand in for pre-race publications. The CSVs lack
   archived timestamped roster/grid snapshots. Specific corruption checks do not
   establish all information-availability assumptions.
7. Renamed constructor histories, qualifying-format drift, sprint-grid effects,
   unobserved weather/tyres/strategy and era changes remain limitations.
8. Repeated validation use and already-inspected holdout data limit claims.
   Separate bootstrap intervals and NN seed variation are not paired model tests.

## Submission items (brief page 8)

| Item | Current state |
|---|---|
| Kaggle notebook link | Excluded from this review at the user's request |
| Accessible GitHub repository containing the final code | Remote configured; anonymous access not verified; final local changes not uploaded by this review |
| Analytical report in PDF | `report.pdf`, 24 pages, Team 63, all 48 plots with explanations |
| Team evaluation readiness | Every member must prepare; see `PROJECT_WALKTHROUGH.md` |

The supplied brief states a deadline of **18 October 2026 at 11:59 PM**. This is
recorded from the PDF, not independently verified as a later announcement.
