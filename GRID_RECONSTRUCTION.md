# Disputed grids: main handling and exploratory reconstruction

The main pipeline **does not reconstruct the disputed grids**. The supplied CSVs
identify a contradiction but cannot establish a unique correct assignment. All
fourteen original files remain unchanged.

## Main decision and its evidence

Four modern races assign one positive slot to two drivers. Each also has one
missing internal slot:

| Race | Duplicate | Gap |
|---|---:|---:|
| Germany 2003 | 13 | 12 |
| Italy 2015 | 17 | 11 |
| Russia 2015 | 17 | 16 |
| São Paulo 2024 | 17 | 18 |

Seventeen modern races have internal gaps; thirteen have no duplicate and are
left unchanged. An empty slot, withdrawal or zero-grid entry can coexist with a
gap, so gaps alone do not establish a recording error.

For the eight conflicting entries, preserve `grid` and `grid_original`, and keep
`grid_conflict` / `grid_conflict_source` true. Main `grid_assignment_assumed` and
`grid_inferred` flags are false because no assignment is adopted. Set both model
inputs `grid_pos` and `grid_drop` to missing; the fitted pipeline fills them with
training medians. Grid-based descriptive comparisons exclude these entries.

This is uncertainty handling rather than a verified replacement value. Median
imputation can weaken an individual prediction; it does not recover the true grid.
Other available qualifying, history and standings inputs remain usable.

The policy is chosen because source evidence is insufficient. It is not selected
because one holdout treatment scored slightly higher. The main modeling table,
model comparison, ablation, explanations and inference all use missing-grid
handling. `outputs/run_summary.json` records this policy explicitly.

## Reconstruction retained only as a sensitivity experiment

Notebook Section 3.5 creates a separate candidate copy. For each pair, assume
one duplicated entry should instead occupy the gap and the two drivers retained
their relative qualifying order. Assign the earlier of those two slots to the
better-qualified driver. This proposes:

| Race | Hypothetical change |
|---|---|
| Germany 2003 | Fisichella: 13 → 12 |
| Italy 2015 | Nasr: 17 → 11 |
| Russia 2015 | Ericsson: 17 → 16 |
| São Paulo 2024 | Hülkenberg: 17 → 18 |

Eligibility requires exactly one internal gap, one duplicated positive slot with
two drivers, and distinct known qualifying positions. The rule uses IDs, grids
and qualifying positions. Outcomes, points, race laps, random assignment and
internet facts do not determine the driver to move.

Penalties or sprint order can reverse qualifying order, and the gap might
legitimately be empty. Germany has stronger internal supporting evidence because
the other drivers' recorded grids match qualifying; the other races contain more
grid changes. A structurally unique grid is therefore not proof of historical
truth. Italy's candidate is a six-place change; the others are one-place changes.

These candidates are **not applied** to main results, main model inputs or
`outputs/cleaning_repairs.csv`. The eight paired candidate records are exported
in `outputs/grid_assignment_hypotheses.csv` with `verified=False` and
`used_in_main_pipeline=False`. `outputs/grid_gap_audit.csv` records all seventeen
gap races. Actual supported repairs elsewhere in the project remain applied.

## Refitted sensitivity and interpretation

Section 12.1 compares four model families under three policies:

1. Missing disputed grid inputs (the main policy).
2. The hypothetical qualifying-order assignments.
3. Opposite assignments in every pair.

Each policy uses identical rows, labels, 28 features, selected hyperparameters and
matched seeds. Pipelines refit imputation/scaling on training only; thresholds
and neural-network stopping use validation. Network scores average three matched
seeds. Opposite assignments reverse all four pairs together; they do not cover
all sixteen possible combinations.

The experiment exports `grid_policy_sensitivity.csv`, per-seed trials and affected
holdout-entry predictions. The notebook computes the signed probability changes
from its current run, naming both compared policies. A higher predicted podium
probability for one driver is not an increase in model accuracy, F1 or average
precision. Almost unchanged aggregate scores can hide individual sensitivity.
Different selected settings can change these results, so old probability numbers
are not reused after restoring the main policy.

These diagnostics demonstrate that a candidate was investigated; they neither
verify the grid nor select the main policy from holdout scores. The revised
holdout remains exploratory after a full-data audit. A definitive grid correction
would require additional reliable source records.
