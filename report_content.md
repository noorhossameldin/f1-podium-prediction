# Formula 1 Podium Prediction

**Milestone 1 · Analytical report**

{{team}}

## 1. Task, data and exploratory findings

We predict whether each driver reaches the podium using information available **after qualifying and before the race starts**. Our target is `positionOrder <= 3`, with one unique `(raceId, driverId)` per prediction. Current-race outcomes supply labels and evaluation only.

We used the supplied Formula 1 World Championship CSVs for 1950–2024 and audited all 14 tables: results, races, drivers, constructors, circuits, status, qualifying, lap times, pit stops, sprint results, driver standings, constructor standings, constructor results and seasons. We joined results to the calendar, driver/team records and status, and qualifying by driver–race. All 14 primary-key and 23 foreign-key checks passed, but we also checked meaning and join sizes: valid IDs do not guarantee consistent records.

**Raw-data EDA.** We first read the files as text with automatic NA conversion disabled. Literal `\N` and empty strings conceal roughly 160,000 missing cells. Missingness is structural: retirements lack some classification/timing fields, knockout qualifying lacks later sessions, and several tables begin only in recent eras. A trailing nationality space creates a false category. We cleaned copies and used SHA-256 checks to confirm that all 14 source files stayed unchanged.

{{figure:eda_after_cleaning_impact|54|Figure 1. Before/after cleaning: missingness, semantic types, entry grain and categories.}}

**Modeling population.** Because qualifying is absent before 1994 and incomplete through 2002, we modeled 2003–2024 and kept earlier records as history. The resulting table contains **8,970 entries, 428 races, 28 features and 1,284 podium labels**. Exactly three labels are positive in every modeled race: prevalence is 14.3%, so an always-negative classifier already reaches about 86% accuracy and has F1 = 0.

{{figure:eda_after_coverage|40|Figure 2. Historical table coverage supports the 2003 modeling boundary.}}

**What we found.** Starting position and qualifying pace carry strong predictive information. Gradient boosting wins validation PR-AUC; logistic regression wins holdout PR-AUC. Neither result proves a universally superior model. We had already inspected the holdout during development, so we treat the revised results as exploratory.

<!-- page -->

## 2. How we cleaned the data and verified the grids

**Typing and plausibility.** We converted both missing sentinels, trimmed text, harmonised `United States`/`USA` and `Argentinian`/`Argentine`, and parsed dates and durations. IDs use nullable integers. Durations become seconds; race-time gap strings remain text, while race duration is derived from milliseconds. The lap parser agrees with the independent millisecond field on approximately 589,000 laps. We set qualifying times above 1.5× the session's fastest lap to missing but kept the qualifying positions. This heuristic flags unrepresentative laps; it does not prove a typo. We also kept and flagged pit durations above five minutes because duration alone cannot establish a red flag.

**Shared drives.** There are 85 duplicated driver–race pairs and 91 surplus rows in 1950–1978. We kept the lowest `positionOrder`, broke ties by `resultId`, and retained shared-drive flags. First-record selection would discard 16 credited podium labels; most-laps selection happens to match the chosen rule. The rule uses outcomes and can select a takeover car's grid, so historical descriptive rates have this caveat. No modeled entry is affected.

**Other repairs.** We swapped lap/stop in seven Monaco 2024 pit records, reconciled ten qualifying constructor IDs and 32 car numbers against result entries, removed four identical 2015 alias constructor aggregates, and marked 258 unranked fastest-lap ranks missing. We preserved originals and repair logs. We kept 13 historical `position`/`positionOrder` disagreements visible and followed the assignment's target, `positionOrder <= 3`. We flagged unresolved pit-record and classification/lap-log conflicts.

### TA guidance and starting-grid corrections

According to our TA, we should check the actual starting-grid positions online and document any corrections. We therefore checked both drivers in each of the four duplicate-slot pairs against official Formula 1 records or the FIA final grid. We used the **published starting-grid slots**, rather than finishing positions, and based the corrections on those records.

| Race | Driver | Original → verified | Official evidence |
|---|---|---|---|
| Germany 2003 | Giancarlo Fisichella | 13 → 12 | [F1 starting grid](https://www.formula1.com/en/results/2003/races/748/germany/starting-grid) |
| Italy 2015 | Felipe Nasr | 17 → 11 | [F1 starting grid](https://www.formula1.com/en/results/2015/races/929/italy/starting-grid) |
| Russia 2015 | Marcus Ericsson | 17 → 16 | [F1 starting grid](https://www.formula1.com/en/results/2015/races/932/russia/starting-grid) |
| São Paulo 2024 | Nico Hülkenberg | 17 → 18 | [FIA final grid, document 63, 11:40](https://www.fia.com/sites/default/files/decision-document/2024%20S%C3%A3o%20Paulo%20Grand%20Prix%20-%20Final%20Starting%20Grid.pdf) |

We confirmed that Villeneuve 13, Sainz 17, Stevens 17 and Verstappen 17 were already correct. The FIA final numbered grid takes precedence over a provisional grid or counting occupied rows. We left ordinary gaps without duplicates unchanged and saved the original values, flags, all eight checks and source URLs in the verification files. The notebook stores the verified values, so it can run without repeating the web lookup.

{{figure:cleaning_cross_table_repairs|54|Figure 3. Supported repairs and remaining semantic conflicts.}}

**Effect.** Verified slots now feed grid features and descriptive controls. Previous qualifying-order, opposite-pair and missing-input policies remain sensitivity experiments (page 12). The raw CSVs and target labels remain intact. Notebook sections 2–3; full provenance: `GRID_RECONSTRUCTION.md` and `outputs/grid_verified_sources.json`.

<!-- page -->

## 3. Question 1: circuit front-row conversion

**Question.** Which circuits convert a front-row start into a podium most often, and does their ranking change in the hybrid era?

**Joins and grain.** We joined de-duplicated `results → races → circuits`, plus `qualifying` on `(raceId, driverId)`. We selected published grid slots 1 or 2 and grouped the front-row entries by circuit and era. Rates use the observed number of eligible entries, which can differ from twice the race count after historical shared-drive collapse. This is a descriptive outcome analysis; using race results here is permitted. Only its later predictive counterpart must use past races.

**Starting grid and qualifying classification are different.** Qualifying position records the qualifying result; grid includes subsequent penalties and, in 2021–2022 sprint weekends, sprint ordering. We used grid for the main definition. Grid is present; qualifying comparisons require 2003–2024 coverage. Official corrections from page 2 apply. For all-time rankings, we required at least **10 races** and plotted **95% Wilson intervals** to show sample uncertainty.

{{figure:q1_all_time|146|Figure 4. All-time circuit conversion with sample eligibility and Wilson intervals.}}

**Answer.** Overall conversion is **60.1%**. The leading eligible circuits are Circuit of the Americas **83.3%** (20/24), Magny-Cours **80.6%** (29/36), and Yas Marina **78.1%** (25/32). The lowest are Kyalami **42.5%**, Brands Hatch **39.3%**, and Nelson Piquet **35.0%**. Differences mix season composition, car/driver strength and reliability; they do not identify a causal track effect. Wide intervals make exact rankings uncertain.

**Historical assumption.** We collapsed shared drives at driver–race grain using the outcome-preserving rule. The selected grid can belong to a takeover car; early rates therefore describe the retained records. We kept genuine shared podium credits, so early races can have more than three credited drivers. Notebook section 5, Q1.

<!-- page -->

## 4. Question 1: era change and grid versus qualifying

We compared **2003–2013** with **2014–2024**, requiring at least five races per era for matched circuit rankings. Overall front-row conversion rises from **68.0% to 76.0%**. Across 14 eligible matched circuits, Spearman rank correlation is **ρ = 0.30, p = 0.29**.

{{figure:q1_era_change|90|Figure 5. Observed circuit rates and ranks in the pre-hybrid and hybrid periods.}}

Pre-hybrid leaders are Monaco and Monza (both about **77%**) and Silverstone (**73%**); hybrid leaders are Suzuka (**89%**), Yas Marina (**86%**) and Monaco (**85%**). Largest observed gains are Yas Marina **+26 percentage points**, Interlagos **+20**, and Montréal **+18**. Monza and Hungaroring each decline about five points.

**Uncertainty.** Matched circuit–era cells typically contain only 10–24 front-row entries. The rankings differ in the sample, but the correlation p-value tests zero association; it does not test whether the underlying rankings changed. These comparisons cannot prove a regulation effect or explain why individual circuits moved.

{{figure:q1_quali_vs_grid|56|Figure 6. Conversion changes when qualifying position is substituted for starting grid.}}

**Definition sensitivity.** Grid differs from qualifying position for **27.0%** of modeled entries. Of 856 top-two qualifiers, 38 start lower: their conversion is **28.9%**, compared with **72.6%** for the 818 who retain the front row. Drivers promoted from third or lower convert **63.9%** (23/36). Overall conversion is **72.2%** under the grid definition versus **70.7%** under qualifying; eligible circuit rankings correlate **ρ = 0.89**. These are associations under different definitions, not causal penalty effects.

**Our modeling choice.** We kept grid, qualifying and their difference. We tested circuit identity against a smoothed past-only conversion feature because the observed rankings alone do not justify fixed circuit effects. Notebook section 5, Q1; feature trials on page 8.

<!-- page -->

## 5. Question 2: home races with starting-position controls

**Question.** Do drivers reach the podium more often at home after controlling for starting position?

**Joins and grain.** `results → drivers` provides nationality; `results → races → circuits` provides circuit country. We mapped nationalities to countries to reconcile names such as British/UK. Dual nationalities count as home in either country; nationalities without a matching circuit are always away. Each row is a driver–race entry with a positive, non-conflicted grid slot; all eight verified pair members are included. Nationality and circuit country are complete. The historical shared-drive rule still applies. Outcomes are allowed because this is descriptive analysis.

**How we controlled for starting position.** We calculated Mantel–Haenszel pooled odds ratios within grid slots, grid × decade, driver × grid band, and constructor-season × grid band, keeping strata with both home and away observations. We pooled slots above 20, repeated the grid control for 2003–2024, and cross-checked with logistic regression using categorical grid and decade.

{{figure:q2_home_effect|84|Figure 7. Raw rates, starting-position comparisons and controlled home/away odds ratios.}}

| Comparison | Home/away odds ratio | 95% interval |
|---|---:|---|
| Raw, without controls | 0.81 | 0.71–0.92 |
| Same grid slot | 0.97 | 0.83–1.14 |
| Same grid slot and decade | 0.91 | 0.78–1.08 |
| Same driver and grid band | 1.02 | 0.84–1.23 |
| Same constructor-season and grid band | 1.07 | 0.87–1.30 |
| Same grid slot, 2003–2024 | 0.76 | 0.51–1.13 |
| Logistic check: grid and decade | 0.94 | 0.80–1.11 |

**Answer.** Among 25,033 eligible entries, 2,324 are home races. Raw podium rates are **11.4% home versus 13.8% away**, but home drivers start further back on average (**13.4 versus 11.7**). After controlling for starting position, every reported interval includes equal odds. **No home advantage is detectable under these controls.** This does not prove the true effect is zero: residual confounding, repeated drivers and dependence within races limit the inferential interpretation.

**Our modeling choice.** We kept `is_home` as a pre-race candidate and tested it through inclusion trials and group ablation. A weak controlled association does not automatically establish zero predictive value in combination. Notebook section 5, Q2.

<!-- page -->

## 6. Question 3: mechanical retirements and uncertain starts

**Question.** Which constructors have the highest mechanical-retirement rate in 2014–2021 versus 2022–2024?

**Joins and grain.** We joined `results → status`, `results → constructors`, and `results → races`, then grouped entries by constructor and era. We kept constructor IDs apart from documented alias repairs and required **40 assumed starts** per constructor–era. Renamed teams may have separate histories. No engine-supplier attribution is inferred.

**Failure labels and starting are separate decisions.** We counted mechanical failures using an explicit list of component/failure labels, excluding crash, driver and regulation labels. Ambiguous labels such as wheel, tyre and unspecified retirement enter only a broader sensitivity analysis; unknown labels default to ambiguous. A recorded component failure does not establish the initiating cause, such as earlier crash damage.

Positive laps confirm a start. Zero-lap withdrawals/non-qualification markers are excluded; positive-lap withdrawals remain starts. Other zero-lap entries are uncertain, including possible first-lap retirements. `grid=0` alone is insufficient. For our main estimate, we **assumed uncertain entries started** and applied the same rule to the numerator and denominator. All IDs resolve; uncertainty concerns their meaning. Current-race outcomes are permitted in this descriptive question, but only shifted history enters reliability features.

{{figure:q3_mechanical_retirements|79|Figure 8. Constructor mechanical-failure estimates, counts and Wilson intervals under the main convention.}}

**Answer.** In 2014–2021 the highest estimates are **Lotus F1 17.3% (13/75), Toro Rosso 16.1% (39/242), Renault 13.1% (26/199)**; lowest are Aston Martin 2.3% and Alfa Romeo 3.3%. In 2022–2024 leaders are **Alfa Romeo 11.4% (10/88), Alpine 10.4% (14/135), AlphaTauri 6.8% (6/88)**; lowest are Sauber 2.1% and Aston Martin 3.0%. Era averages fall from **8.81% to 5.33%**. Matched-constructor rank correlation is −0.34 (p = 0.31); precise rankings are uncertain.

| Era | Uncertain / excluded entries | Main rate | Positive-lap only | Eligibility bounds |
|---|---|---:|---:|---|
| 2014–2021 | 83 / 21 | 8.81% | 8.85% | 8.64–9.02% |
| 2022–2024 | 29 / 7 | 5.33% | 5.22% | 5.11–5.43% |

**Sensitivity.** Eligibility bounds vary unresolved starts while holding failure classification fixed; **they are assumption bounds, not confidence intervals**. Strict/broad-label rank agreement is **0.96** in the first era and **0.63** in the second. Small counts make newer rankings sensitive to borderline failures. Leclerc, Monaco 2021, is excluded by zero laps and withdrawal marker; Räikkönen, Malaysia 2017, remains uncertain with zero laps and retirement marker. The CSVs do not resolve every DNS/start. Appendix E shows both sensitivity plots; constructor tables are in notebook section 5, Q3.

<!-- page -->

## 7. Prediction cutoff, feature definitions and split

We built all 28 features from chronological 1950–2024 history, then selected the modeled seasons. We shifted every outcome-based aggregate before use and combined constructor outcomes per race **before** shifting. This prevents the second car's row from seeing the first car's current result.

| Group | Features and construction | Availability |
|---|---|---|
| Grid (3) | `grid_pos`: zero behind last slot; `no_grid_slot`; `grid_drop = grid_pos − quali_pos` | Published grid, with verified corrections |
| Qualifying (5) | `quali_pos`, `quali_gap_pct`, `mate_quali_gap_pct`, `team_best_gap_pct`, `quali_missing` | Recorded qualifying classification and fastest available Q1/Q2/Q3 laps; gaps capped at 10% and ±5% |
| Driver form (7) | `drv_podium_rate_5`, `drv_avg_finish_5`, `drv_dnf_rate_10`, `drv_career_podium_rate`, `drv_career_entries`, `drv_circuit_podium_rate`, `drv_circuit_entries` | Previous 5/10 entries and earlier career/circuit records |
| Constructor form (3) | `con_podium_rate_5`, `con_avg_finish_5`, `con_mech_rate_10` | Previous 5/10 team races; both cars; mechanical rate uses Q3 assumed-start denominator |
| Standings (5) | `drv_stand_pos`, `drv_points_share`, `drv_wins`, `con_stand_pos`, `con_points_share` | Previous round; previous season's final table at round 1 |
| Context (5) | `is_home`, `round_number`, `qualifying_field_size`, `driver_age`, `circuit_front_conv_prior` | Static/current-calendar/qualifying facts; past-only circuit rate with 10 prior front-row entries at running global rate |

**Domain assumptions.** Career/form entry counts include non-starts; the mechanical denominator is a different quantity. Rookies' form stays missing until training-only imputation. Unranked drivers/teams receive one position beyond the last ranked, zero points share and wins. Points shares reduce points-system scale differences. `no_grid_slot` does not distinguish pit-lane starts from DNS. Gaps use fastest recorded laps, which may come from different sessions/conditions.

**We excluded current-race** result position, points, laps, status, timing, fastest lap, pit stops, lap logs, constructor points and same-race standings. We also excluded sprint features to keep a consistent qualifying cutoff. Round number avoids eventual season-length leakage; qualifying count avoids post-race field size. Historical result entries and grids are retrospective proxies: timestamped pre-race roster/grid archives are unavailable.

| Set | Seasons | Races | Entries | Podiums | Use |
|---|---|---:|---:|---:|---|
| Train | 2003–2018 | 300 | 6,411 | 900 | Fit preprocessing and model |
| Validation | 2019–2021 | 60 | 1,200 | 180 | Feature/tuning/stopping/threshold selection |
| Holdout | 2022–2024 | 68 | 1,359 | 204 | Revised exploratory evaluation |

{{figure:split_timeline|44|Figure 9. Chronological, race-disjoint split.}}

**How we checked for leakage.** We corrupted current/future outcomes and standings for six sampled races; their input features stayed identical. Our deliberately leaky same-race standings failed the negative control, while changing later calendar rounds left earlier inputs unchanged. These checks address specific dependencies, not absent publication archives. Histories may update from earlier validation/test races because the task predicts each race after earlier races finish; they would be unavailable for a whole-season advance forecast. Notebook sections 6–7.

<!-- page -->

## 8. Evidence for feature selection

We assessed features using training-only AUC, mutual information, relationship plots and correlations. We fitted inclusion/encoding trials on training, scored them on validation, and kept all trial results. Grid/qualifying relate strongly and nonlinearly to podiums; standings and rolling form carry related measures of competitiveness. Race-constant context features cannot rank drivers within a race, though they can interact with driver-level inputs.

{{figure:features_effect_plots|42|Figure 10. Training-only feature/target relationships: steep position effects and nonlinear rates.}}

<div class="figure-pair">
{{figure:features_correlation|55|Figure 11. Spearman correlations expose overlap.}}
{{figure:features_trial_incremental|55|Figure 12. Validation scores as feature groups are added.}}
</div>

**Trial A: add groups.** Grid and qualifying provide much of the signal; team form and standings add further information. Later groups add less. Strong overlap means a feature can be useful alone but add little after another measurement of the same pattern. Correlation can destabilise coefficients and attributions; it does not guarantee prediction quality is unaffected.

{{figure:features_trial_encoding|40|Figure 13. Encoding/inclusion trials against the full 28-feature reference.}}

**Trial B: our decisions.** We recoded grid zero because it means no grid slot, even though the raw encoding slightly improves one validation score. We kept qualifying position alongside grid because they differ for 27% of entries; `grid_drop` describes that difference. Constructor/circuit one-hot identities expand to 57/59 columns without consistent improvement across the two model types. Rolling strength describes current competitiveness more directly than a fixed team identity. We kept home and weak context features because removing them did not consistently improve both trial models; all final learned models use the same 28 features as required.

**Interpretation limits.** Small changes on 60 validation races are not significance tests. Feature selection is development work; retrospective Q1/Q2 findings explain candidates but do not provide independent validation evidence. The later ablation retrains the selected model configurations to quantify conditional contributions (page 12). Notebook section 8.

<!-- page -->

## 9. Preprocessing and order experiments

**9.1 Our pipeline.** We split first, fitted **median imputation → standardisation on training only**, and applied those fitted statistics unchanged to validation/holdout. Scaling uses `z = (x − training mean) / training SD`; validation/holdout never fit their own scalers. Missing rates/gaps reflect first circuit visits, absent history or absent qualifying times. Median is a simple robust numeric default, not a claim that an imputed position was actually achieved. Repeated imputed ranks do not assign podium places. We did not test mode imputation.

{{figure:preprocessing_effect|48|Figure 14. Imputation creates a concentration at the median; scaling aligns units without removing skew.}}

Standardisation helps regularised logistic regression and neural optimisation across mixed units; tree splits are insensitive to ordinary positive linear rescaling. A common pipeline gives all learned models comparable inputs. We also tried mean imputation, missing indicators, robust scaling and no scaling. Validation AP is **0.7431 / 0.7275** (boosting/logistic) for the default and **0.7464 / 0.7295** with indicators. The small gain has no uncertainty test; existing missingness/history flags partly describe missingness. We kept the simpler pipeline, although these results do not prove it is optimal.

### 9.2 Order matters even when score changes are small

{{figure:preprocessing_order_experiments|44|Figure 15. Three order experiments on validation, with the deliberately invalid fit restricted to development data.}}

{{order_deltas}}

**Split versus fit.** Learning preprocessing from all development rows leaks validation statistics; excluding holdout makes the demonstration less intrusive, not valid. The scaler shifts by up to 0.144 training SD. We therefore kept split-first despite the small measured score change.

**Split versus histories.** We built shifted features on chronological history before assigning splits. Restarting within each split discards known past information: career counts change for 78% of validation rows and circuit history for many first visits. This task allows sequentially available past results; future outcomes remain excluded.

**Impute versus scale.** Scaling observed values before imputation uses a different variance from scaling the completed matrix; transformed values differ by up to 0.501. We kept impute-first to give all models the same completed, scaled inputs. Scaling is affine and preserves the completed distribution's shape; imputation itself changes that distribution. Notebook section 9; small AP changes do not establish statistical significance.

<!-- page -->

## 10. Models, tuning and experimental safeguards

We trained the learned models on the same rows, 28 features and training-only preprocessing. The grid-frequency reference intentionally uses only grid: training-set podium frequencies by slot, with no machine-learning estimator.

| Model | Mechanism and selected configuration | Main limitation |
|---|---|---|
| Logistic regression | Weighted sum → sigmoid; L2 penalty; `C=1`, no class weighting. Tuning returns the default baseline settings. | Linear log-odds; no explicit interactions; correlated coefficients unstable |
| Random forest | Average 300 trees; depth 12, minimum leaf 5; random feature subsets | Can memorise training patterns; limited extrapolation |
| Gradient boosting | Sequential trees reduce loss; learning rate 0.1, depth 4, 43 rounds, L2 = 0 | Flexible patterns can be specific to earlier seasons |
| Shallow neural network | ReLU layers 64/32, dropout 0.3, weight decay 0.0001, Adam | Small positive sample; seed variation; reused stopping validation |

**Tuning.** We logged **60 main attempts**: default baseline, 16 logistic configurations, 15 forests, 12 boosting settings and 16 networks. We chose settings on validation AP, selected boosting rounds by validation log-loss, and restored the network's lowest validation-loss epoch with patience 15. Test labels select neither settings nor thresholds. The 52 later ablation fits are separate. Learning curves expose fitting beyond the useful stopping point.

<div class="figure-pair">
{{figure:model_gb_training|45|Figure 16. Boosting training/validation loss and selected round.}}
{{figure:model_nn_training|45|Figure 17. Network loss with regularisation and stopping.}}
</div>

**Metrics.** Primary **PR-AUC is implemented as average precision (AP)**, a step-weighted precision–recall summary, not trapezoidal integration. It focuses on the rare podium class; random ranking has expected performance near prevalence (~0.15). Secondary **F1** measures thresholded precision/recall balance. We also report ROC-AUC, precision, recall, Brier (lower is better) and accuracy. ROC-AUC measures positive/negative ranking; it does not count correctly predicted negative labels. Accuracy is inflated by the negative majority.

We chose each decision threshold to maximise validation F1 and froze it for evaluation, keeping the grid reference for comparison. Boosting's threshold is **0.3906**. Independent thresholds may yield more or fewer than three positives; top-three-per-race is a separate decision rule.

{{figure:model_era_sensitivity|35|Figure 18. Validation performance when earlier training seasons are removed.}}

**Design checks.** Shortening the training window changes validation AP by 0.010 (logistic) and 0.028 (boosting); fewer/recent rows are confounded. We retained the full training window. Random row splits give lower average AP here (−0.049/−0.069; SD ~0.045), but change both evaluation population and dependence. Their comparison is not a clean leakage estimate and does not justify random splitting. Network seed SD concerns initialisation, not sampling or significance. Notebook section 10.

<!-- page -->

## 11. Model comparison and the meaning of “best”

{{model_scores}}

**Our model choice.** We selected gradient boosting because its validation AP was highest (**0.7555**). Logistic regression achieves the highest revised holdout AP (**0.6959 versus 0.6883**). Random forest achieves the highest holdout F1 (**0.6746**). We therefore distinguish our validation choice from the holdout winner. Selecting again using holdout scores would require a fresh evaluation.

{{figure:comparison_curves|37|Figure 19. ROC/PR curves and race-bootstrap AP intervals on the revised holdout.}}

**Uncertainty and overfitting.** We bootstrapped complete races to preserve dependence between drivers in the same race. Separate model intervals overlap; their overlap is not a formal paired test. Forest's training AP **0.929 → 0.686** is the clearest overfitting warning; boosting **0.782 → 0.688** also drops. Logistic's **0.693 → 0.696** gives less evidence of memorisation, but cannot prove absence of overfitting. Season shifts, limited samples and repeated validation selection also affect gaps.

{{figure:comparison_calibration_seasons|34|Figure 20. Calibration and variation across the three holdout seasons.}}

**Race structure.** We also tested selecting the three highest probabilities per race. This guarantees three predicted podium drivers without assigning their finish order. Boosting F1 becomes **0.706 validation / 0.647 holdout**, versus **0.738 / 0.665** with its threshold. The structural constraint improves plausibility but does not improve this F1 result. Notebook section 11.

<!-- page -->

## 12. Feature-group ablation and grid-policy sensitivity

**Our method.** We removed each of the six groups and **retrained from scratch** with the selected hyperparameters, comparing against the full model. We also trained on each group alone. Across four model families this gives **52 configurations**, averaging three matched network seeds. Keeping settings fixed measures contribution to our selected configuration, rather than the best retuned model for each subset.

{{figure:ablation_groups|50|Figure 21. Drop-group deltas and group-only scores across all four model families.}}

{{ablation_deltas}}

**Distinct questions.** “Only this group” measures stand-alone predictive value. “Drop this group and retrain” measures its additional value given the remaining inputs. A group can be strong alone yet replaceable by correlated inputs. Grid removal reduces validation and holdout AP for all four families. Other removals vary by model and period; tiny effects or improvements may reflect redundancy, overfitting, season differences or sampling. The experiment does not isolate their cause. Removing several groups together may hurt more. The grey band is network seed SD, not statistical significance or race-sampling uncertainty.

### Official-source grid policy and alternatives

We compared verified slots with the earlier qualifying-order hypothesis, opposite assignments and missing disputed inputs. We refitted using identical rows, labels, features, settings and matched seeds, with preprocessing fitted on training and thresholds/stopping chosen on validation. Opposite-pair reversal does not exhaust all 16 combinations. The candidate happens to match official slots, but official documents supply the evidence.

{{figure:grid_assignment_sensitivity|44|Figure 22. Aggregate AP and affected-entry probability changes under grid policies.}}

**Result and interpretation.** Aggregate AP changes are small. Verstappen's São Paulo 2024 mean network probability is **31.23% verified versus 23.79% opposite**, a **−7.44 percentage-point** sensitivity change after refitting. This concerns one prediction, not overall accuracy. A higher probability or score cannot establish a correct historical grid. Following our TA's guidance, we used official records to choose the corrected slots; the holdout differences remain exploratory. Notebook section 12; all policy scores and entry probabilities are exported.

<!-- page -->

## 13. Global explainability: reliance and direction

> **Explanations are not causal effects. A feature being important to the model is not proof that it causes podium finishes; it means the model relies on it to make predictions.** Standings, grid and outcomes share influences such as car pace and driver ability. These methods do not establish what would happen after a real-world intervention.

We explained both our selected statistical model (boosting) and the neural network. **Permutation importance** measures the fall in holdout AP after shuffling, with 20 repeats; group permutations use one shared row permutation for all group members. **SHAP** allocates a model prediction relative to a reference into feature contributions; mean absolute contributions summarise global influence. Neither statistic measures a physical effect on podium outcomes.

{{figure:xai_permutation_importance|90|Figure 23. Single-feature and group permutation importance for both explained models.}}

{{figure:xai_shap_global_bar|45|Figure 24. Global SHAP shares at feature and group level for both models.}}

**Interpretation.** Starting slot and qualifying pace lead the explanations, followed by standings and recent driver/team form. Small single-feature permutation effects can arise because a correlated input substitutes for it (`grid_pos`/`quali_pos` correlation ~0.97); group shuffling reduces substitution within that group but not across remaining groups. Correlated features also make attribution allocation unstable.

**Direction and method differences.** The SHAP distributions on the following page show low grid/qualifying positions pushing predictions toward podium. Higher strength measures tend to push upward. Context may move scores without improving ranking. Permutation measures ranking degradation; SHAP measures prediction movement, so their orderings need not match. Agreement with EDA/ablation provides complementary evidence on the same data, not three independent statistical experiments. Notebook section 13.

<!-- page -->

## 14. SHAP direction and local explanations

<div class="figure-pair">
{{figure:xai_shap_beeswarm_best_statistical|58|Figure 25. Boosting SHAP distributions and feature directions.}}
{{figure:xai_shap_beeswarm_neural_network|58|Figure 26. Network SHAP distributions on the same feature set.}}
</div>

**How we chose the cases.** We selected the actual podium with the highest predicted probability and the actual podium with the lowest. These illustrate a confident correct prediction and a large miss, rather than a representative error sample. We explained both with SHAP waterfalls and LIME, which fits a local surrogate around sampled nearby inputs.

<div class="figure-pair">
{{figure:xai_local_shap_case_A|52|Figure 27. Case A: Max Verstappen, Austria 2022.}}
{{figure:xai_local_shap_case_B|52|Figure 28. Case B: Pierre Gasly, Netherlands 2023.}}
</div>

**Case A.** Verstappen, Red Bull Ring 2022 round 11: grid 1, finish 2, podium probability **0.90**. Grid 1, qualifying position 1 and team-best gap 0 push the prediction upward. **Case B.** Gasly, Zandvoort 2023 round 13: grid 12, finish 3, probability **0.01**. Team-best gap 10%, constructor points share 0.11 and qualifying position 12 push downward. This identifies why the model underestimated the entry; it cannot establish whether the miss arose from in-race events, missing pre-race variables, data errors or model limitations.

{{figure:xai_local_lime|45|Figure 29. LIME local surrogate explanations for the same two cases.}}

SHAP and LIME share four of their five leading features in each case, but their agreement is not a robustness proof. Different baselines, correlated features and LIME sampling can change allocations; LIME can weight nearly constant flags through its sampled neighbourhood. SHAP explains the model output relative to its reference, while LIME approximates nearby behaviour. **Neither explains why the real race outcome occurred or identifies a causal intervention.** Notebook section 13.

<!-- page -->

## 15. Inference, limitations and conclusions

Our `predict_podium` function accepts a dictionary of engineered pre-race features for one entry. It returns probability, thresholded decision, selected model, number provided and names imputed. Missing/`None` inputs use the fitted training medians and scaler; unknown names raise an error. It does not accept only a driver name and automatically reconstruct history. Trained objects live in notebook memory and require execution after restart.

{{figure:inference_demo|35|Figure 30. Complete, partially missing and grid-only inputs for the same recorded entry.}}

Lando Norris, Abu Dhabi 2024: complete 28-feature record gives **0.7387**; a record missing six features gives **0.7046**; grid-only gives **0.0448**, using threshold **0.3906**. The missing fields are qualifying gap, team-mate gap, team-best gap, driver DNF rate, driver circuit podium rate and constructor mechanical rate. Imputation can move probability either way and supplies no uncertainty interval. Many missing inputs mean greater reliance on defaults. The single-entry threshold does not enforce three podiums; the race-level rule requires the full race's scores.

### Assumptions and practical limits

- **Coverage and changing formats:** validity is restricted to 2003 onward; qualifying formats/session conditions, points systems, field sizes and reliability vary. The 2022 regulation era differs from training. Sprint ordering in 2021–2022 means grid drops mix penalties and sprint effects; sprint features themselves are excluded.
- **Historical sources:** shared-drive collapse uses outcomes only outside the modeling window. Constructor renames split histories. Unresolved lap/classification and pit records remain flags. Mechanical causes and uncertain starts follow explicit conventions and sensitivity bounds, not invented exact classifications.
- **Availability:** result entries and recorded grids are retrospective pre-race proxies; timestamped publications are absent. Calendar/qualifying proxies remove specific future dependencies but do not prove every historical input was published at the cutoff.
- **Missing predictors and dependence:** weather, tyres, strategy, practice pace and upgrades are unavailable. Drivers in a race are dependent; rows are scored independently, with top-three structure applied only at decision time. Race-bootstrap intervals address within-race dependence, not every temporal dependence.
- **Evaluation:** 900 training positives and 204 holdout positives limit precision. Validation is reused for features, hyperparameters, stopping and thresholds. Earlier test results and full-data repairs have already been reviewed; the revised holdout is **exploratory**, not a fresh untouched test. Models remain trained through 2018 without train+validation refitting. Observed gaps cannot isolate overfitting from season shifts.
- **Explainability:** importance and local contributions describe model reliance; they are not causal effects. Correlated inputs, reference choices and local surrogate sampling limit attribution stability.

**What we learned.** Front-row conversion rises in the observed hybrid period with uncertain circuit rankings; no home advantage is detected under starting-position controls; mechanical-failure estimates fall under both era conventions, with newer constructor rankings sensitive to definitions. Boosting is the validation-selected model; logistic regression leads holdout AP and forest leads holdout F1. We do not have enough evidence to name a clear overall winner. Our next step would be evaluation across several chronological windows, followed by a genuinely unseen later period; we have not performed that evaluation yet.

**Reproducibility and evidence.** Our executed notebook contains 84 code cells, and artifact checks pass under our stated conventions. All 48 notebook plots appear in this report: 30 alongside the main analysis and 18 with explanations in Appendices A–I. Full trial results and a figure gallery remain available. Scores, ablations, order experiments, Q3 sensitivity and grid provenance are in `outputs/`. Data source: [Formula 1 World Championship CSV collection](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020); official correction references are on page 2. We have not verified evaluator access to our GitHub submission. Notebook sections 14–15.

<!-- page -->

## Appendix A. Missing-value and relationship audits

We began with the raw tables so that cleaning choices followed measured problems. These checks complement the before/after comparison on page 1; neither requires manual inspection of individual CSV rows.

{{figure:eda_before_sentinels|105|Figure 31. Raw placeholder counts and the missingness concealed by an ordinary read.}}

**What we found.** The literal `\N` accounts for most placeholders, but qualifying Q2/Q3 also contain empty strings. Ordinary missing-value detection therefore understates missingness. We converted both representations before calculating distributions or joining numerical fields. Much of this missingness has a meaning: a driver may have been eliminated before Q3, a timing field may be absent for a retirement, or a table may not exist for that era. We did not fill such source fields indiscriminately; only the model pipeline later fills its selected inputs using training statistics.

{{figure:audit_keys|65|Figure 32. Declared primary-key and foreign-key checks across the relational tables.}}

**What the checks establish.** All 14 declared primary keys are unique and non-null, and all 23 declared foreign-key relationships reconcile. This supports joining the tables without orphan references. It does not mean all values agree across tables, or that a join on an incomplete key is safe. We separately checked driver–race uniqueness, row counts, expected join cardinality and cross-table metadata. For example, a unique `resultId` can still coexist with several rows for one driver in one race. Notebook sections 2.1–2.4.

<!-- page -->

## Appendix B. Duplicate entries and the rule we chose

The prediction unit is a driver entering a race, while the historical source can record more than one car for that driver. We needed a reproducible rule that preserves credited podiums without pretending those records describe independent predictions.

{{figure:eda_before_duplicates|67|Figure 33. Historical concentration and examples of repeated driver–race entries.}}

**Interpretation.** The 85 repeated pairs are concentrated in early shared drives, with some later multiple-entry/non-qualification cases; together they contain 91 surplus rows. These are different result entries, not necessarily accidental duplicate lines. A driver could take over another car and receive a podium credit. Deleting arbitrary rows could change the driver's label. The affected records end in 1978, so this choice does not remove or select any row in our 2003–2024 modeling table.

{{figure:cleaning_duplicate_rules|69|Figure 34. Comparison of best-result, first-record and most-laps duplicate rules.}}

**Why we kept the best result.** Among repeated pairs, 22 have a credited podium. Keeping the lowest `resultId` preserves only six and loses 16. Keeping the lowest `positionOrder` preserves all 22; the most-laps rule happens to choose the same rows here. We selected the outcome-preserving rule, with `resultId` as a deterministic tie-break, and retained `shared_drive` and entry-count flags. It uses post-race information and may attach a takeover car's grid to the retained record. We disclose that cost for the historical descriptive questions and do not claim it is a generally valid pre-race population rule. Notebook sections 2.5 and 3.4.

<!-- page -->

## Appendix C. Semantic conflicts and typed durations

{{figure:eda_before_cross_table_consistency|92|Figure 35. Cross-table conflicts found even though declared key checks pass.}}

**How we handled the findings.** We checked related values as well as IDs. Examples include ten qualifying constructor mismatches, 32 car-number mismatches, eight conflicting grid entries, seven apparent lap/stop swaps and 258 zero fastest-lap ranks. Page 2 records the supported repairs and their sources. Other findings, including missing initial pit records, disagreements between lap logs and classifications, and historical withdrawal labels, remain visible. A flag does not authorise an arbitrary replacement. The apparent modern constructor-points discrepancy disappears once sprint points are included, so we did not “repair” valid totals. The Q3 start rule uses entry evidence separately from failure labels.

{{figure:eda_after_durations|67|Figure 36. Duration distributions after parsing lap, qualifying and pit records into seconds.}}

**What typing made possible.** Qualifying laps mostly lie around 55–130 seconds, varying with circuit length. Race laps have a longer right tail, and pit-lane durations concentrate around 20–25 seconds with some much longer records. Converting text to seconds makes these distributions measurable; the independent lap millisecond field checks parser consistency. Long durations can reflect several circumstances, so duration alone does not identify a red flag, a slow stop or an erroneous record. We retained flagged long pit records and excluded pit/lap logs from current-race predictors because they occur after the cutoff. Notebook sections 2.7, 3.2–3.5 and 4.2.

<!-- page -->

## Appendix D. Target balance and starting-position evidence

{{figure:eda_after_target|69|Figure 37. Podium prevalence and field size after cleaning.}}

**Why prevalence matters.** Every modeled race has exactly three positive driver labels, so podium prevalence depends on field size. Across the 2003–2024 table it is 14.3%, with a slightly lower share in training than validation/holdout. An always-negative prediction would have roughly 86% overall accuracy but identify no podiums. We therefore selected average precision as our primary metric and F1 as the secondary decision metric. Historical shared podium credits before the modeled era are retained and need not produce exactly three driver labels; we did not change the prescribed target to force that constraint.

{{figure:eda_after_grid|75|Figure 38. Podium conversion by starting slot and the meaning of grid zero.}}

**Why grid needs a domain rule.** Conversion is highest near the front and falls sharply toward the middle/back of the grid. This motivates a grid-based reference model and nonlinear candidate models. Zero is a marker for no ordinary grid slot, not a better position than pole; historically it includes non-qualifiers, while newer entries can include pit-lane starts or non-starters. We moved zero behind the last positive slot and kept a separate flag. This describes the marker without claiming that we know which of those situations occurred. Grid is associated with car pace and driver strength, so the plot does not estimate the causal effect of moving a car forward. Notebook sections 4.4–4.5.

<!-- page -->

## Appendix E. Question 3: two separate sensitivity checks

{{figure:q3_trend_and_change|72|Figure 39. Mechanical-failure trends and constructor ranking sensitivity to broader labels.}}

**Failure-label sensitivity.** The year-by-year view supports the observed decline from an era average of 8.81% in 2014–2021 to 5.33% in 2022–2024 under our main start convention. It does not establish a regulation effect. Adding ambiguous labels raises failure estimates; agreement between strict and broad constructor rankings is 0.96 in the first era and 0.63 in the second. The latter is more sensitive to a few borderline retirements. Across matched constructors, era rankings correlate −0.34 (p = 0.31); this does not establish a stable ordering or a statistically proven reversal.

{{figure:q3_start_eligibility_sensitivity|79|Figure 40. Assumed-start estimates versus positive-lap-only estimates and eligibility bounds.}}

**Start-eligibility sensitivity.** We separately varied whether uncertain zero-lap entries started, while keeping mechanical labels fixed. There are 83 uncertain entries in the first era and 29 in the second, after excluding 21 and seven marked non-starts. Main rates are 8.81% and 5.33%; positive-lap-only rates are 8.85% and 5.22%. Eligibility bounds of 8.64–9.02% and 5.11–5.43% do not overlap, so the observed era difference survives these stated start conventions. These are assumption bounds, not statistical confidence intervals, and they do not cover every failure-label error. We need better start evidence to classify every unresolved entry exactly. Notebook section 5, Q3.

<!-- page -->

## Appendix F. Remaining missingness and individual feature evidence

{{figure:features_missingness|58|Figure 41. Missingness in the final modeling inputs, grouped by feature source.}}

**What remains missing.** First visits to a circuit account for many missing circuit podium rates; rookie histories and absent driver/team-mate qualifying times create others. Their meanings differ, so our history counts and qualifying-missing flag help the model distinguish cases even after imputation. All eight originally conflicting grid entries now use official verified slots; the former conflict is not a reason to leave `grid_pos` missing. A missing qualifying position can still leave `grid_drop` missing. We learn fills from training only.

{{figure:features_univariate_auc|130|Figure 42. Training-only ranking power of each of the 28 individual inputs.}}

**How we used this evidence.** Qualifying position and grid each reach about 0.91 univariate ROC-AUC; qualifying gaps, standings and recent form also show useful associations. Direction is ignored for this ranking: lower grid is favourable, while higher podium rate is favourable. Weak-alone context variables can interact with stronger inputs, so we also tested group addition, encoding changes and ablation. A race-constant variable cannot order drivers within that race, even if pooled scores differ across races. These are training associations, not independent validation or causal effects. Notebook sections 6.4 and 8.1.

<!-- page -->

## Appendix G. Scaling ranges and logistic-regression tuning

{{figure:preprocessing_ranges|72|Figure 43. Feature ranges before and after training-only imputation and standardisation.}}

**What scaling changes.** Original inputs mix counts, years, positions, rates and gaps. Standardisation makes their training variances comparable, which helps regularised logistic regression and gradient-based network training. It does not bound values to a fixed interval: rare binary flags can have large standardised maxima, and skewed variables remain skewed. Imputation can add a concentration at a median; scaling then shifts and rescales that completed distribution. We apply the same training statistics to later splits rather than making each split define its own units.

{{figure:model_lr_tuning|77|Figure 44. Logistic training/validation AP across regularisation and class-weight choices.}}

**Why the tuned baseline stayed simple.** We compared eight values of `C` under ordinary and balanced class weights, keeping all 16 trials. Smaller `C` strengthens L2 regularisation. The highest validation AP is 0.7275 at `C=1` without class weighting, exactly the default baseline's settings. Reweighting the rare class therefore did not improve our chosen ranking metric in this comparison. A training gain alone would not justify a setting. Since the later holdout AP is 0.6959, this simple model remains a serious alternative to boosting despite its lower validation score. Notebook sections 9.1 and 10.3.

<!-- page -->

## Appendix H. Forest complexity and the complete model search

{{figure:model_rf_tuning|76|Figure 45. Random-forest training and validation AP across depth and leaf-size settings.}}

**Where fitting becomes too specific.** Deeper trees and smaller leaves can improve training fit without a matching validation improvement. We tested five depth choices and three leaf sizes, selecting depth 12 and minimum leaf size five on validation AP (0.7473). Even this selected forest has training AP 0.929 and holdout AP 0.686. That is the strongest memorisation warning among our models. The gap can also contain season differences; the plot does not tell us what share comes from overfitting. Larger leaves, stronger restrictions and several chronological validation windows would be sensible future comparisons, rather than changes selected from holdout scores.

{{figure:model_all_trials|78|Figure 46. All 60 logged modeling attempts, with the statistical baseline as a reference.}}

**What the search establishes.** The log contains the baseline, 16 logistic variants, 15 forests, 12 boosting settings and 16 shallow networks. Boosting has the highest validation AP (0.7555); forest reaches 0.7473, logistic 0.7275 and the network 0.7267. This satisfies the requirement to compare more than three attempts with recorded evidence. These are development comparisons on repeatedly reused validation seasons; the search does not provide 60 independent tests or prove a universally best family. Ablation's 52 configurations are a separate experiment. Notebook sections 10.4 and 10.7.

<!-- page -->

## Appendix I. Performance gaps and the resulting decisions

{{figure:comparison_train_val_test|76|Figure 47. Training, validation and revised holdout metrics for the recorded models.}}

**Reading the gaps.** The forest's large training advantage contracts sharply on later seasons. Boosting has a smaller training/validation gap but also declines on holdout. Logistic AP is similar on training and holdout, while the network shows a later-period drop. These results do not prove that one model is free of overfitting, because the populations differ and validation influenced selection. Boosting is our validation choice; logistic leads holdout AP and forest leads holdout F1. Our table on page 11 reports all seven metrics, and our limitations explain why the holdout is exploratory rather than a fresh test.

{{figure:comparison_confusion|72|Figure 48. Holdout confusion matrices using each model's frozen validation-selected threshold.}}

**What the errors mean.** Precision and recall reflect different error balances. Logistic regression recovers about 82% of actual podiums but has precision around 56%; boosting recovers about 68% with precision around 65%. Forest has similar precision to boosting and somewhat higher recall, giving the highest observed F1. Many correct negative decisions should not hide missed podiums, which is why accuracy is not our main metric. Thresholding each driver independently can predict more or fewer than three podiums; the separately evaluated top-three rule enforces the count but did not improve boosting F1. These matrices describe prediction errors, not why the actual race outcomes happened. Notebook section 11.
