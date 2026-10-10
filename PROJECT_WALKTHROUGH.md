# Understand the F1 project, one step at a time

This is a reading companion to `f1_podium_prediction.ipynb`. Read one stage, open
the matching notebook section, and answer its checkpoint before moving on. You do
not need to understand every plotting command to understand the project.

The explanations below describe what the code actually does. They reconstruct
the reasoning supported by its checks and experiments; they cannot tell us what
Claude privately thought or which versions it tried outside this repository.
Read `REQUIREMENTS_AUDIT.md` alongside this guide: an implemented step can run
successfully and still have a flawed assumption or an overstated conclusion.

## Stage 1: What are we trying to predict?

**Notebook: opening and Section 1.**

Imagine the qualifying session has finished and the race has not started. For
each driver, you want a probability of finishing first, second, or third.
You are predicting **podium versus no podium**, not the exact finishing order.

One example is one driver in one race. The same driver in another race is a
different example. `(raceId, driverId)` identifies that example.

The answer used for training is:

```python
podium = int(positionOrder <= 3)
```

`positionOrder` is a complete result ordering, including drivers who retired.
It is more suitable than `position`, which can be missing for retirements.
The label is allowed to use the eventual result: we need the result to teach and
evaluate the model. The **inputs** must be available before that race starts.

The central distinction is **X versus y**:

- `X`: the information we give the model, such as grid position and previous form.
- `y`: the answer we want it to learn, whether this driver eventually podiumed.

**Checkpoint:** Why is this race's finishing position allowed in `y`, but not in `X`?

## Stage 2: Why are there fourteen CSV files?

**Notebook: Sections 1.1 and 2.**

The dataset is a relational database exported to CSV. Different files describe
different things. Instead of repeating each driver's name in every result row,
`results.csv` stores `driverId`; `drivers.csv` translates that ID to a person.

| Tables | What they describe | Main use here |
|---|---|---|
| `results` | One result entry, with driver, team, grid, result and status | Target and historical outcomes |
| `races`, `circuits`, `seasons` | Calendar, tracks and seasons | Time ordering, race context and era comparisons |
| `drivers`, `constructors` | People and teams | Names, home country, age and team identity |
| `qualifying` | Qualifying position and session times | Pre-race pace |
| `driver_standings`, `constructor_standings` | Championship state after each race | Previous-round standings |
| `status` | Meaning of each finish/retirement code | Historical reliability classification |
| `constructor_results` | Team points from a race | Audited; current-race points excluded |
| `lap_times`, `pit_stops` | Events during the race | Audited and explored; excluded from current-race inputs |
| `sprint_results` | Sprint outcomes | Audited; excluded to avoid inconsistent cutoff rules |

For example, to find a result's circuit country, you need:

```text
results.raceId → races.raceId
races.circuitId → circuits.circuitId
```

That is a **multi-hop join**: following more than one relationship.

`RAW` is a dictionary of the fourteen original tables. They are first read as
text, with automatic missing-value recognition turned off. This preserves the
actual file contents so the audit can discover problems instead of hiding them.
`CLEAN` later holds copies with repairs. File hashes provide a check that the
CSV files have not changed.

**Checkpoint:** Why can't `results.csv` alone answer whether a driver races at home?

## Stage 3: How do we discover what is wrong?

**Notebook: Sections 2.1–2.6.**

The notebook scans the data and produces tables and plots. Each finding is meant
to connect to a specific decision in cleaning.

| Problem | How the code detects it | Why it matters |
|---|---|---|
| Hidden missing values | Counts literal `\N`, empty strings and other possible placeholders | A string such as `\N` is not automatically a usable numeric missing value |
| Numbers/times read as text | Inspects dtypes and the shapes of date/time strings | We cannot reliably compute numeric gaps or time differences from strings |
| Dirty categories | Checks spelling variants and surrounding whitespace | `USA` and `United States` should not become separate countries |
| Invalid keys | Checks duplicates/nulls in primary keys and unmatched foreign keys | Broken relationships can lose rows or attach the wrong information |
| Multiple entries per driver–race | Checks `(raceId, driverId)` separately from `resultId` | The modeling unit must be unique even if result entry IDs are unique |
| Unrepresentative qualifying times | Compares times with session-best times | An extreme recorded lap can distort pace features |
| Uneven historical coverage | Plots qualifying coverage by season | Some eras cannot support the same inputs as modern races |

A **primary key** uniquely identifies a row. A **foreign key** points to a row
in another table. `results.resultId` can be unique while two rows still represent
the same driver in the same race. Checking only primary keys would miss that.

The original data contains 26,759 result rows. There are 85 duplicated
driver–race pairs, with 91 surplus rows. Early shared drives explain most of
this: a driver could appear in records for more than one car in one race.

**Checkpoint:** How can all `resultId` values be unique and the modeling grain still be wrong?

## Stage 4: How does cleaning fix those problems?

**Notebook: Section 3.**

### Missing values

The code trims whitespace and converts `\N` and empty strings into missing
values. It does **not** immediately replace every missing value with an average.

Missingness often has meaning. A Q3 time can be missing because a driver never
reached Q3. Qualifying data can be absent because a historical season was never
covered. Filling these with invented lap times would conceal that meaning.

### Types and units

Dates become datetime values. Numeric columns become numbers if conversion
preserves every non-missing value. Duration strings become seconds:

```text
"1:26.572" → 1 × 60 + 26.572 → 86.572 seconds
```

The duration parser is checked against the separately supplied milliseconds
column in 589,081 lap records. Agreement is evidence that the parser works on
these formats. It does not prove that every recorded time is factually correct.

### Values and categories

Qualifying times above 1.5 times the fastest time in the same qualifying
segment are marked missing. This preserves the driver row and qualifying
position while discarding the unrepresentative time. The threshold is a
heuristic: a slow recorded lap is not necessarily a typo or physically impossible.

Country/nationality spelling variants are harmonised. Pit-stop durations above
300 seconds receive a flag; the code does not delete them. The flag should be
read as **possible long stoppage**, because duration alone cannot prove a red flag.

### Duplicate driver–race rows

Three selection rules are compared. The chosen rule keeps the smallest
`positionOrder`, with `resultId` breaking ties. It preserves any podium credited
to a driver; choosing the first entry would lose 16 such labels.

This rule uses the outcome, which would be problematic for selecting modern
pre-race feature rows. In this dataset all affected rows are before 1979 and
the prediction table begins in 2003. The caveat still matters for the historical
descriptive analyses and histories.

**Checkpoint:** Why is converting missingness different from imputing it?

### Cross-table repairs added after the deeper audit

A primary key can be valid while two fields contradict one another. The deeper
checks in Section 2.7 compare entries across tables; Section 3.5 repairs the
cases supported by those comparisons:

- Seven Monaco 2024 pit records have a stop number larger than the recorded lap.
  Their times and neighbouring stops support swapping `stop` and `lap`; that
  removes the internal sequence gaps without creating duplicate keys.
- Ten qualifying team IDs and 32 car numbers disagree with their matching race
  entry. We choose results as the canonical **entry metadata**, preserve both
  original fields, and record the policy. This reconciles the tables; it does
  not independently prove which car number was physically displayed.
- Four 2015 alias constructor aggregates duplicate an existing native team's
  identical zero-point aggregate. Only these four duplicate copies are removed.
- Following the TA guidance reported by the team on 10 October 2026, four
  starting-grid clashes are checked online against official F1/FIA records. Both
  drivers in each pair are matched by race, name and car number; four slots
  change, four are confirmed unchanged, and source URLs/access dates are logged.
  See the step-by-step grid explanation below.
- Fastest-lap rank zero becomes missing in a derived column. The original zero
  remains available, because zero does not mean a rank ahead of first.

Every supported replacement is logged in `outputs/cleaning_repairs.csv`; original values
and dispute flags are exported. Incomplete pit histories and conflicting timing
or classification fields stay flagged because a valid replacement is unknown.
See `FIXES_AND_REMAINING_ISSUES.md` for the decisions and limits.

## Stage 5: What did the second EDA teach us?

**Notebook: Section 4.**

EDA means **exploratory data analysis**: looking at distributions, missingness,
relationships and coverage before committing to a model.

Before-cleaning EDA discovers faults. After-cleaning EDA checks the impact of
the repairs and discovers useful patterns.

The main modeling decisions are:

1. **Start at 2003.** Qualifying coverage is patchy before then. This yields
   8,970 driver–race examples across 428 races through 2024. Older results still
   supply historical information, but are not training/prediction examples.
2. **Treat podium as a rare class.** The modeled window contains 1,284 positive
   examples, about 14.3%. Predicting no podium for everyone would get about
   85.7% accuracy while finding no podiums.
3. **Use grid position as an important input.** The plot shows podium rates
   falling steeply as starting position gets worse.
4. **Handle `grid = 0` separately.** Zero indicates no ordinary grid slot; it
   should not be treated as better than pole position. In modern data it can
   also occur for non-starters. The repaired feature is named `no_grid_slot`; it does not claim to identify a pit-lane start.

Eight source entries share a positive grid slot with another driver in their
race. We found them by grouping positive grid values by race and checking counts.
Each pair also has a gap. That suggested an error but did not identify the driver
to move, since qualifying order can change after penalties or a sprint.

The team asked its TA and reported that she advised checking the actual values
online. We used official starting-grid records, matching race/date, driver and
car number for both members of each pair. They support Fisichella 13→12 (Germany
2003), Nasr 17→11 (Italy 2015), Ericsson 17→16 (Russia 2015), and Hülkenberg 17→18
(São Paulo 2024). The other four drivers retain their recorded slots. For São
Paulo we use the FIA final numbered grid rather than compressing an empty slot.

Why choose these replacements? Official evidence identifies the slots; a gap,
qualifying-order assumption or improved test score cannot prove them. The main
model now uses verified starting slots and derived grid drops. Original CSVs,
original values and conflict flags remain preserved, and each changed row has a
source link and access date. No finishing result is used as a starting position.
Run All uses an embedded dated manifest, so the notebook does not scrape the web.

Section 12.1 compares verified values, our earlier qualifying-order candidate,
opposite assignments and the earlier missing-input policy. The candidate happens
to match the official values, but it is source evidence that justifies adopting
them. See `GRID_RECONSTRUCTION.md` for all links and exported provenance.

**Checkpoint:** Why could a model with 85% accuracy be useless here?

## Stage 6: The three analysis questions

**Notebook: Section 5.**

These questions describe what happened in historical races. They may use
outcomes directly. The pre-race restriction applies when those facts become
inputs for predicting a particular race.

### Question 1: Which circuits convert front-row starts into podiums?

Join results to races and circuits, then qualifying. Count actual grid slots
1 and 2, and calculate how many of those entries finished in the top three.

`qualifying.position` and `results.grid` answer different questions. A driver
can qualify second and start seventh after a penalty. The analysis reports both.

The current run's historical front-row conversion is about 60%. In the two
modern comparison windows it rises from about 68% in 2003–2013 to 76% in
2014–2024. Grid differs from qualifying order for about 27% of entries.

Minimum race counts and Wilson confidence intervals make small samples visible.
A circuit with ten front-row starters cannot support a precise rate estimate.
The observed circuit rankings move, but the code's rank-correlation test does
not by itself prove a robust change in the underlying rankings.

### Question 2: Does racing at home help?

Join results to drivers, races and circuits. Translate nationality into country:
`British` must match `UK`, for example. Then create an `is_home` flag.

Raw rates are about 11.4% at home and 13.8% away. That does not show that home
races hurt: home entries also start farther back on average.

The code compares home and away within the same starting positions, and adds
checks within driver or constructor-season. This controls for some differences
in who appears in each group.

The same-grid odds ratio is about 0.97, with a 95% interval of 0.83–1.14. An odds
ratio of 1 means equal odds. Because the interval includes 1, the defensible
conclusion is **no detectable home advantage under these controls**, not proof
that the true effect is exactly zero.

### Question 3: Which constructors retire mechanically most often?

Join results to status, constructors and races. Classify status labels and
divide mechanical retirements by race starts, separately for 2014–2021 and
2022–2024. A broader classification tests sensitivity to ambiguous labels.

The repaired notebook reports about **8.81% versus 5.33%** under its main
start convention. Lotus F1, Toro Rosso and Renault rank highest in the first era;
Alfa Romeo, Alpine and AlphaTauri in the second (minimum 40 assumed starts).

We found the old rule was incomplete by comparing failure labels with
`positionText` and completed laps. Leclerc's Monaco 2021 CSV row has `W`, zero
laps and `Driveshaft`. A failure label explains the withdrawal but does not make
it a retirement after starting. That entry is now excluded. Conversely, a
historical withdrawal with positive laps is retained as a start.

The new rule treats positive laps as confirmed starts, excludes zero-lap
withdrawal/non-qualification markers, and marks remaining zero-lap entries
**uncertain**. There are 83 uncertain entries in 2014–2021 and 29 in 2022–2024.
The main estimate assumes these entries started; companion tables also show
positive-lap-only estimates and the lowest/highest rates possible as uncertain
entries' eligibility varies. The corresponding bounds are **8.64–9.02%** and
**5.11–5.43%**. These are assumption bounds, not confidence intervals.

We chose this because dropping every zero-lap retirement would remove genuine
first-lap retirements, while counting every component failure as a start would
retain some withdrawals. The CSVs cannot resolve all such entries exactly.
Unknown failure labels now become ambiguous rather than automatically mechanical.
The constructor reliability feature uses the same convention on earlier races only.

**Checkpoint:** Why can a raw home/away comparison be misleading?

## Stage 7: Turning history into safe inputs

**Notebook: Section 6.**

A **feature** is one input column. Feature engineering builds useful inputs from
the raw tables. This project uses 28 features in six groups.

| Group | Count | What it asks |
|---|---:|---|
| Grid | 3 | Where will this driver start? Did grid order change from qualifying? |
| Qualifying | 5 | How fast was this driver, their teammate and their team? |
| Driver form | 7 | How has this driver performed in previous races and visits? |
| Constructor form | 3 | How has the team performed and how often has it failed? |
| Standings | 5 | How strong were driver and team before this race? |
| Context | 5 | Home race, current round, qualifying entry count, age and track history |

### The important leakage example

Suppose a driver has outcomes in their last five races:

```text
0, 1, 0, 0, 1 → past podium rate = 2 / 5 = 0.4
```

That is safe for predicting the **next** race. If you include the next race's
outcome in its own rolling average, the input partly contains the answer.

The code orders races by date and applies:

```python
s.shift(1).rolling(5, min_periods=1).mean()
```

`shift(1)` moves each known outcome to the following example. `rolling(5)`
then summarises previous appearances. The beginning of a career has fewer
than five observations; `min_periods=1` permits those shorter histories.

For constructors, both cars are first aggregated **by race**, then the race
aggregate is shifted. Otherwise the second driver row could accidentally see
their teammate's outcome from the same race.

The driver career/circuit count features are named `*_entries`: their histories
include recorded entries that did not start. Driver finish/form rates likewise
summarise earlier entries. Constructor mechanical reliability instead uses the
explicit start-eligibility denominator required by Q3. These are different,
documented quantities rather than interchangeable meanings of “starts.”

### The standings trap

Standings associated with race X include the points from race X. Joining them
to race X leaks its result. `prior_standings` joins the previous round instead.
At round one it uses the previous season's final table.

Points are divided by the championship leader's points. This makes different
points systems more comparable than using raw totals.

### Qualifying gaps

Suppose the fastest recorded qualifying lap is 80 seconds and this driver has
81.2 seconds:

```text
(81.2 / 80 − 1) × 100 = 1.5% slower
```

A percentage helps compare circuits with different lap lengths. The code uses
the best recorded lap across Q1/Q2/Q3, so this is a gap to the fastest recorded
lap, which need not be the pole lap. Weather and changing session conditions
can also make this imperfect.

### How leakage is tested

For six races, the code corrupts current and future outcomes and post-race
standings, then rebuilds the features. Those races' input features stay unchanged.
A deliberately incorrect same-race standings join changes, proving the test can
detect that particular leak.

This is good evidence against outcome leakage in the tested cases. It is not a
universal proof. A separate check changes strictly later round numbers and confirms the sampled
races' features stay unchanged. This catches the former season-length dependency.
Neither check reconstructs archived entry/grid publication snapshots.

**Checkpoint:** Why does constructor form need aggregation before shifting?

## Stage 8: Separating learning, decisions and final evaluation

**Notebook: Section 7.**

| Set | Seasons | Rows | Races | Podiums | Job |
|---|---|---:|---:|---:|---|
| Train | 2003–2018 | 6,411 | 300 | 900 | Learn model parameters and preprocessing statistics |
| Validation | 2019–2021 | 1,200 | 60 | 180 | Choose settings and decision thresholds |
| Test | 2022–2024 | 1,359 | 68 | 204 | Evaluate the frozen choices on later seasons |

This chronological split matches intended use: learn from older races and
predict newer ones. It keeps every race together. A random row split would mix
drivers from the same race across sets and train on some outcomes later than
those being evaluated.

Historical features for a later test race may include outcomes of **earlier
test races**. That is valid for race-by-race forecasting: those races have
already happened. It would be invalid if the claimed task were to forecast the
whole test season before its first race.

Leakage rules apply to **training, validation and test**: each row's inputs must
use only facts available before that race. Fit preprocessing on training only;
use validation to choose hyperparameters, features and thresholds. Test measures
those frozen choices. A past-only history can be built before splitting because
it does not learn future information; a scaler cannot be fitted on all splits.

This revision followed an audit of all CSV seasons, including test-era records,
and the earlier test results had already been inspected. Therefore these scores
are labelled a **revised exploratory holdout**, not a newly untouched test.
To get a fresh final evaluation, freeze the repairs and evaluate later unseen
races using the same rules, without selecting further changes on their results.

**Checkpoint:** What is validation allowed to choose that test is not?

## Stage 9: Why these features and this preprocessing?

**Notebook: Sections 8 and 9.**

Feature choices are supported by training-set plots, Spearman correlations,
single-feature ranking scores, mutual information, and validation experiments.

The trials add groups incrementally, try raw grid encoding, remove candidate
features, and add one-hot team/circuit identities. They preserve comparative
evidence rather than merely announcing a chosen set.

Strong correlations explain why two useful features can appear redundant. Grid
and qualifying position measure related things; standings and form both
describe recent strength. A weak feature on its own can still help through an
interaction, but that requires evidence.

The main preprocessing pipeline is:

```text
missing values → training medians → training mean/std scaling → model
```

**Median imputation** replaces a missing value with a typical training value.
The median is relatively insensitive to extreme observations.

**Standardisation** computes:

```text
z = (x − training mean) / training standard deviation
```

For a training mean of 10 and standard deviation of 5, a grid value of 2 becomes
`(2 − 10) / 5 = −1.6`. This puts inputs on comparable scales for regularised
logistic regression and neural-network optimisation. Trees usually do not
need it, but all final learned models receive the same preprocessing.

The imputer and scaler are fitted on training rows only. Validation/test values
use those existing statistics; they do not create their own statistics.

Three order experiments compare:

1. Splitting before fitting preprocessing versus fitting on train + validation
   development rows first. Even the deliberately invalid example excludes test rows.
2. Building past-only history before splitting versus resetting history inside each split.
3. Imputing before scaling versus scaling before imputing.

The first deliberately demonstrates an invalid pipeline as a negative example.
Its small score change does not make the leak acceptable. The second explains
why preserving past history is correct. The third compares two different but
train-fitted transformations.

**Checkpoint:** Why can building past-only features before splitting be valid,
while fitting a scaler before splitting is invalid?

## Stage 10: What do the models actually learn?

**Notebook: Section 10.**

### Grid-frequency rule

Look up how often a grid slot produced podiums in training. It uses only grid
position. It asks whether machine learning adds useful information beyond
the most obvious predictor.

### Logistic regression

Compute a weighted sum of features, then apply a sigmoid to obtain a probability.
It learns how each input changes the log-odds of podium. The baseline uses
`C=1.0`; tuning tries different regularisation strengths and class weighting.
Smaller `C` means stronger regularisation, which discourages large weights.

It is a reasonable baseline because it is simple and interpretable. It is limited
when relationships are curved or require interactions.

### Random forest

Many trees ask threshold questions, such as whether grid position is at most
three. Each sees a resampled training set and subsets of candidate features.
Their probabilities are averaged. It can learn nonlinearities and interactions.

Tuning varies depth and leaf size. Deep trees can memorise training data. If
training PR-AUC improves but validation PR-AUC does not, that is evidence of
overfitting. Shallower trees/larger leaves constrain complexity.

### Gradient boosting

Small trees are added sequentially, each correcting errors left by earlier ones.
Learning rate controls the size of each correction. Depth and L2 regularisation
also limit complexity.

The code trains up to 400 rounds, measures validation log-loss after each round,
and refits using the best round count. Different settings are compared by
validation average precision. The selected model uses 43 rounds, depth 4,
learning rate 0.1 and L2 regularisation 0.0 in the verified run.

### Shallow neural network

The network takes the same 28 inputs, passes them through one or two hidden
layers, and outputs one logit. A sigmoid converts that logit to podium probability.
It learns with Adam and binary cross-entropy in minibatches of 64 examples.

Dropout, weight decay and early stopping are tested to limit overfitting. Early
stopping restores the weights from the epoch with the best validation loss.
Multiple seeds check how much random initialisation changes the result.

The main tuning log contains 60 attempts: a logistic baseline plus 16 logistic
variants, 15 forest variants, 12 boosting variants and 16 network variants.
Feature and ablation experiments add more fits outside this particular log.

**Checkpoint:** Why is the lowest training loss not enough to choose a model?

## Stage 11: Reading the metrics and selecting a model

**Notebook: Section 11.**

Suppose 10 entries are predicted to podium, 7 really do, and there were 12 actual
podium entries:

```text
precision = 7 / 10 = 0.70
recall = 7 / 12 ≈ 0.583
F1 = 2 × precision × recall / (precision + recall) ≈ 0.636
```

**ROC-AUC** measures how well scores rank positives above negatives.
**Average precision (AP)** summarises precision across increasing recall. This
notebook calls AP “PR-AUC”; it is a common PR summary, but is not identical to
the trapezoidal area under a plotted PR curve.

AP is primary because podiums are rare. F1 is secondary because it evaluates
actual yes/no decisions. Precision, recall, accuracy and Brier score are also
reported; Brier measures squared probability error, where lower is better.

Each model's threshold is chosen to maximise validation F1. A probability of
0.4 could mean podium for one model and no podium for another, depending on
their frozen thresholds. This threshold tuning must never use test labels.

The verified run selects **gradient boosting on validation AP**. On test it gets
approximately AP 0.688, ROC-AUC 0.937, F1 0.665, precision 0.654 and recall 0.676.
The decision threshold is about 0.391.

The simple logistic baseline gets test AP about 0.696; random forest about
0.686. That is not a contradiction. The model chosen on validation need not win
on a different future sample. Replacing it with the test winner would use test
information to make a choice.

The honest finding is that the learned models are close. This run does not show
that additional complexity clearly beats logistic regression on future seasons.
Race-level bootstrap intervals show uncertainty, although overlapping separate
intervals are not a formal paired test of the difference between models.

The additional top-three-per-race rule selects exactly three highest-scoring
drivers. The ordinary probability-threshold rule can predict more or fewer.
Neither predicts the order of first, second and third.

**Checkpoint:** Why shouldn't we replace the chosen model with whichever model wins on test?

## Stage 12: What ablation tells us

**Notebook: Section 12.**

An ablation removes a feature group, retrains the model, and compares the score
with the full feature set. It asks what the removed group uniquely adds once
other information is available.

A second experiment trains with only that group. It asks whether the group is
useful by itself. The code runs 52 configurations across four model types:
four full sets, 24 drop-one sets and 24 only-one sets. Network configurations
are averaged across three seeds.

Grid and qualifying overlap, so removing one may barely hurt even though either
is useful alone. A small drop does not prove a group contains no information.
Conversely, a slight improvement after removal can be sample noise or reduced
overfitting; it is not automatic proof that the feature is harmful.

Section 12.1 compares the main verified-grid policy with the earlier
qualifying-order candidate, opposite assignments and missing inputs. Each policy
refits preprocessing and models using the same rows and settings. Current outputs
give aggregate scores and signed changes to individual predicted probabilities.
This measures modeling sensitivity. Official evidence, following reported TA
guidance, establishes the main repair; model scores do not establish historical
truth. The qualifying-order candidate produces the same inputs as the verified
policy in these four cases.

**Checkpoint:** How can a feature group be strong alone but have little unique contribution?

## Stage 13: Explaining predictions

**Notebook: Section 13.**

**Permutation importance:** shuffle a feature and measure how much test AP falls.
A large fall means the fitted model relied on that input for ranking quality.
Groups are also shuffled together because correlated features can substitute
for each other.

**SHAP:** allocate a prediction's difference from a reference output among
features. The global beeswarm shows many individual contributions. A waterfall
shows one prediction. Boosting contributions are in log-odds here; network
contributions are in probability units, so their raw magnitudes are not directly
comparable.

**LIME:** sample points around an example and fit a simple local approximation.
It gives readable conditions, but its sampled records can be unrealistic for
correlated F1 inputs.

The local examples are selected by fixed rules: the actual podium with the
highest predicted probability, and the actual podium with the lowest probability.
These are useful contrasting cases, but deliberately extreme cases rather than
a representative error sample.

Explanations tell us **why the model produced a score**. They do not prove why
the real race unfolded that way. A missed podium is not, by itself, proof that
only unpredictable in-race events caused the error; inputs and model assumptions
can also be imperfect.

**Checkpoint:** Does high SHAP importance for starting position prove that moving any car to pole causes a podium?

## Stage 14: Using the inference function

**Notebook: Section 14.**

`predict_podium` expects a dictionary containing the engineered feature values.
It does not take a driver name and build all histories automatically.

```python
predict_podium({"grid_pos": 2, "quali_pos": 2})
```

It creates one row in the established feature order, fills missing values using
the fitted training medians, scales it using training statistics, and calls the
selected model. It returns probability, decision, threshold and a list of filled
features. Unknown names cause an error so spelling mistakes are visible.

The notebook demonstrates a complete real record, a version with six missing
features, and a grid-only record. Removing features can move the probability
in either direction. Median imputation does not guarantee that every model's
score moves toward the average, or provide an uncertainty interval.

The trained objects live in notebook memory. To use them after restarting the
kernel, rerun the training cells. Model persistence/deployment is not implemented
and is not a Milestone 1 requirement.

**Checkpoint:** Why doesn't a dictionary containing only `driverId` meet this function's input contract?

## Stage 15: What gets submitted, and how to study it

**Notebook: Section 15; files: README and requirements audit.**

The notebook saves figures and CSV tables and checks that raw files remain
unchanged. `make_report.py` converts explanations, plots and selected tables
from the executed notebook into a PDF. The report is derived from the notebook;
it is not independent evidence that the notebook currently runs.

The assignment also asks for accessible Kaggle and GitHub links and a PDF.
A local run cannot establish that the Kaggle publication runs in its environment.
The report now includes the four supplied member names and student IDs.

Suggested study sessions:

1. Stages 1–5: understand the prediction unit and data repairs.
2. Stage 6: explain each join and each denominator without reading code aloud.
3. Stages 7–9: trace one driver's past-only features and preprocessing.
4. Stages 10–12: defend the baseline, split, metrics, tuning and ablation.
5. Stages 13–15: explain one prediction and review the submission gaps.

For each decision, practise this sentence pattern:

> We checked ___. The evidence showed ___. We chose ___ because ___, and its limitation is ___.

That is the reasoning you need to defend. “Claude wrote it” does not explain
why a data rule or modeling choice is correct.
