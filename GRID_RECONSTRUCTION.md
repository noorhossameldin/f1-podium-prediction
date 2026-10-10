# Verified starting-grid corrections after TA guidance

On **10 October 2026**, the team reported that it had asked its TA about duplicate
starting-grid slots and had been advised to search online for the actual values
and document the corrections. This is the team's reported guidance; the project
records neither a TA name nor an invented consultation transcript.

## Finding, evidence and applied changes

Grouping positive `results.grid` values by race exposed four duplicate pairs in
2003–2024. Each race also has an internal gap. That structure identifies suspect
records but does not prove which driver should move: penalties and sprint results
can change qualifying order, and a withdrawn car can leave a legitimate gap.

Following the reported TA guidance, we checked **both drivers in each pair**
against official starting-grid records, matching the race/date, driver and car
number. Four entries need a correction; their four paired entries are confirmed
unchanged. These are **starting positions**, not finishing positions.

| Race | Driver | CSV grid | Verified grid | Official evidence |
|---|---|---:|---:|---|
| Germany 2003 | Giancarlo Fisichella | 13 | 12 | [Formula 1 starting grid](https://www.formula1.com/en/results/2003/races/748/germany/starting-grid) |
| Italy 2015 | Felipe Nasr | 17 | 11 | [Formula 1 starting grid](https://www.formula1.com/en/results/2015/races/929/italy/starting-grid) |
| Russia 2015 | Marcus Ericsson | 17 | 16 | [Formula 1 starting grid](https://www.formula1.com/en/results/2015/races/932/russia/starting-grid) |
| São Paulo 2024 | Nico Hülkenberg | 17 | 18 | [FIA Final Starting Grid, document 63, 11:40](https://www.fia.com/sites/default/files/decision-document/2024%20S%C3%A3o%20Paulo%20Grand%20Prix%20-%20Final%20Starting%20Grid.pdf) |

The paired entries remain Villeneuve **13**, Sainz **17**, Stevens **17** and
Verstappen **17**. Sources were checked on **10 October 2026**. Nasr's correction
is six places; the other three changes are one place each.

For São Paulo, the FIA's final numbered grid takes precedence over an earlier
preview or prose counting occupied starting places. It explicitly lists
Verstappen in slot 17 and Hülkenberg in slot 18. We retain the official numbered
slots rather than compressing an empty slot. No race-finishing classification,
points, laps or podium labels determine any replacement.

## Main policy and provenance

The earlier main policy masked both drivers' disputed grid inputs and used
training-only imputation. It was appropriate while the sources could not resolve
the assignment. The main policy is now **Verified starting grid**, chosen from
external source evidence following TA guidance, irrespective of model scores.

Notebook Section 3.5 embeds eight evidence records and checks their original
values, car numbers and event dates before applying four replacements to
`CLEAN['results']`. All fourteen raw CSV files stay unchanged. `grid_original`
and `grid_conflict_source` preserve the original eight disputed entries;
`grid_external_verified` marks all eight checks, `grid_corrected` marks the four
changes, and `grid_conflict` records zero remaining clashes in the modeled era.
`grid_inferred` and `grid_assignment_assumed` stay false: the main corrections
are source-backed rather than inferred from qualifying.

The model's `grid_pos` and `grid_drop` use the verified slots. Grid-based EDA
and Q2 include the resolved entries again. Labels, population, split boundaries
and the 28-feature definition stay the same; models, ablations and explanations
are rerun. The other thirteen modern races with internal gaps and no duplicate
are left unchanged: a gap alone is insufficient evidence for a correction.

Reproducible evidence is exported to:

- `outputs/grid_external_verification.csv`: all eight checked entries, sources,
  access dates and whether each changed.
- `outputs/grid_verified_corrections.csv`: the four changed entries.
- `outputs/grid_verified_sources.json`: reported TA guidance and eight records.
- `outputs/cleaning_repairs.csv`: four official-grid actions alongside prior repairs.
- `outputs/cleaned_results_metadata.csv`: source values, corrected values and flags.

Run All uses the embedded, dated manifest. It does not scrape changing web pages
or require a live connection to reproduce the corrections. Source links remain
available for a reviewer to inspect. Notebook markdown is included in the
regenerated HTML/PDF report.

## Earlier assumptions and refitted sensitivity

The previous qualifying-order hypothesis proposed these same four changes. The
official checks happen to confirm all eight candidate slots, but qualifying
order itself did not establish their truth. Its separate hypothesis export now
records `matches_verified_grid=True` and `verified=True`; its
`used_in_main_pipeline=False` still means the heuristic is not the main repair
method. Official evidence supplies that justification.

Section 12.1 compares four model families under four policies:

1. Verified starting grid (the main policy).
2. The earlier qualifying-order hypothesis.
3. Opposite assignments in every pair.
4. Missing disputed grid inputs (the earlier main policy).

Each policy uses identical rows, labels, 28 features, selected hyperparameters and
matched seeds. Imputation/scaling refit on training only; thresholds and neural
stopping use validation. Neural scores average three matched seeds. The verified
and qualifying-order policies should match under the same fit because their
input values are identical. Opposite assignments reverse all four pairs together
and do not exhaust all sixteen possible combinations.

The exported experiment has 32 aggregate model/split/policy rows. Individual
probability changes are signed and computed from the current run. A driver's
probability increasing is not an increase in aggregate accuracy, F1 or average
precision. Model scores do not verify historical facts or select the repair.

This revision follows a full-season audit and previous inspection of test
results, so the revised holdout remains exploratory. The external starting-grid
checks do not introduce finishing outcomes into inputs; they also do not restore
an untouched holdout or supply timestamped pre-race snapshots for every race.
