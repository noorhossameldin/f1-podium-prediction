# Additional CSV consistency audit

This second pass uses only the fourteen supplied CSVs. It checks relationships
between fields and tables, beyond primary/foreign keys and missing-value counts.
It found additional issues; the first audit was not exhaustive.

The supported repairs are now applied in notebook Section 3.5 and Q3. The raw
CSVs remain unchanged, confirmed by SHA-256 checks. Counts in this document
describe the original source findings; `outputs/cleaning_repair_summary.csv`
shows before/after counts. See `FIXES_AND_REMAINING_ISSUES.md` for current status.

Reproduce the checks with the project environment:

```python
# This can be run in a notebook cell with the .venv kernel selected.
%run scripts/audit_data_consistency.py
```

The script exports `outputs/data_consistency_summary.csv`, a row-level
`outputs/data_consistency_flags.csv`, and `outputs/data_consistency_audit.json`.
Counts below overlap: one entry can violate multiple checks. They are not all
confirmed errors, and should not all receive automatic replacement values.

## 1. Seven Monaco 2024 pit-stop records appear to have swapped columns

`raceId=1128`. The source contains:

| Driver ID | Raw `stop` | Raw `lap` | Time | Cleaned `stop` | Cleaned `lap` |
|---|---:|---:|---|---:|---:|
| 822 | 15 | 2 | 16:04:57 | 2 | 15 |
| 840 | 42 | 2 | 16:41:05 | 2 | 42 |
| 840 | 48 | 3 | 16:49:27 | 3 | 48 |
| 1 | 51 | 2 | 16:52:10 | 2 | 51 |
| 830 | 52 | 2 | 16:53:26 | 2 | 52 |
| 858 | 57 | 2 | 17:01:43 | 2 | 57 |
| 855 | 70 | 2 | 17:19:04 | 2 | 70 |

Each driver already has stop 1 recorded. A “70th stop on lap 2” contradicts
both the observed sequence and the intended meanings of these columns. Swapping
the two fields produces stops 2/3 at laps 15–70, consistent with their chronology.

Verification on the exported cleaned copy: seven rows changed, no duplicate
`(raceId, driverId, stop)` keys, and all six affected drivers have contiguous stop
numbers. This eliminates all six internal stop-sequence gaps in the dataset.

**Applied:** a narrowly scoped, documented swap on `CLEAN['pit_stops']`,
with before/after records and key/sequence assertions. Do not write back to raw CSV.
Original values and each changed record are preserved in the exported repair log.

Two other records begin at stop 2: Chilton at Britain 2014 (`908,820`) and Sainz
at Singapore 2019 (`1024,832`). There is no evidence that their values were
swapped. Flag incomplete coverage; do not invent stop 1 or renumber them blindly.

**Impact:** pit stops are excluded from current-race prediction features, so this
repair improves audit/EDA and future analyses rather than the current model's inputs.

## 2. Team identities disagree across qualifying and results

Ten qualifying entries use `constructorId=206` (Marussia), while the same
driver–race results use `209` (Manor Marussia). All are in 2015, at races
`937, 941, 942, 943, 944`, with two drivers affected per race.

Across 2015:

- Results contain 36 entries for constructor 209.
- Constructor standings use 209 for eighteen races.
- Qualifying mixes 206 (ten rows) and 209 (25 rows).
- Constructor results also contain four rows for 206.

Every ID passes the foreign-key test because both teams exist in `constructors`.
The problem is using different identities for the same race entry. Valid IDs
are not proof that a join is semantically consistent.

**Applied:** reconciled these specific entries using results as the canonical
race-entry metadata table; the result/standings agreement supports using 209
for these 2015 entries. Preserve original IDs and a repair flag. Do not replace
206 globally: that would also rewrite earlier Marussia history.

**Impact:** current qualifying gaps are joined by race/driver, and both teammates
share the same qualifying team ID in these cases. Therefore the mismatch alone
does not demonstrate that all ten existing gap values are wrong. It matters for
consistent team joins and aggregate analyses.

The constructor-results comparison finds seven rows whose `(raceId,
constructorId)` pair has no corresponding result entry: four of these 2015
Marussia rows, one 2002 team identity, and two 1979 Brabham identities. The four 2015 rows duplicate native 209 aggregates with identical zero points
and missing status. These four alias copies are now omitted from cleaned
constructor results. The three older unmatched team aggregates remain flagged;
the CSVs do not establish a unique repair.

## 3. Four modern races have duplicated positive grid slots

Eight rows form four conflicts:

| Race | Grid slot | Drivers |
|---|---:|---|
| Germany 2003, `raceId=119` | 13 | Villeneuve and Fisichella |
| Italy 2015, `raceId=938` | 17 | Sainz and Nasr |
| Russia 2015, `raceId=941` | 17 | Stevens and Ericsson |
| São Paulo 2024, `raceId=1141` | 17 | Verstappen and Hülkenberg |

Different drivers should not occupy the same ordinary grid slot. Their driver–race
keys remain unique, so the original grain check did not detect this.

**Applied uncertainty handling:** original grid numbers remain unchanged and
flagged. Both affected drivers' main model grid positions and grid drops are
missing and filled by training-only imputation. Grid-based descriptive comparisons
exclude these entries. A duplicate/gap audit identifies candidate pairs, but
qualifying order cannot establish the true final grid.

Section 12.1 retains hypothetical changes (Fisichella 13→12, Nasr 17→11,
Ericsson 17→16 and Hülkenberg 17→18) and opposite assignments as refitted
sensitivity experiments only. Candidates are exported with
`used_in_main_pipeline=False`; they are absent from the main repair log.
Thirteen other modern races with gaps but no duplicate are left unchanged.
See `GRID_RECONSTRUCTION.md`.

**Impact:** this affects a central predictor in eight modeling entries, including
two entries in the test window. Changes selected after inspecting test evidence
must be disclosed; do not silently claim the same evaluation stayed untouched.

## 4. Fastest-lap metadata can contradict recorded race laps

Twelve result rows have `fastestLap > laps`. Examples:

- Vettel, Australia 2014: three race laps, fastest lap labelled lap 26.
- Hartley, Italy 2018: zero race laps, fastest lap labelled lap 6.
- Hülkenberg, São Paulo 2024: zero classified laps with status `Disqualified`,
  but a fastest lap labelled lap 21.

The last example also has a thirty-lap timing log and three pit stops. It
illustrates why classified lap totals and observed racing activity must be
distinguished. Not every conflict necessarily means the timing log is wrong.

There are also **258 rows with fastest-lap `rank=0`**, all lacking a recorded
fastest-lap time. Zero represents no ranking, rather than a rank ahead of first.

**Applied:** preserved raw values, exported contradiction flags, and represented
zero as missing in `fastest_lap_rank`. The twelve conflicting lap bundles remain
unresolved. Where actual timing logs are
available, compare the fastest-lap bundle before choosing a corrected value.
Do not manufacture a fastest time from an unverified lap index.

**Impact:** fastest-lap fields are excluded from current-race predictors. This is
still relevant to semantic cleaning and the analytical audit.

## 5. Timing logs and result classifications do not always match

- **37 driver–race pairs** have logged laps beyond `results.laps`.
- **Three pit-stop rows** exceed their driver's result lap total; all belong
  to Hülkenberg's disqualified São Paulo 2024 entry.
- **20 result rows**, including nine in 2003–2024, have a `+n Laps` status
  inconsistent with the difference between winner laps and driver laps.

Many timing-log differences cluster in China 2014: logged lap counts exceed
classified counts by two. A common race-level pattern can reflect classification
conventions rather than independent typos. Without external evidence, the CSV
does not establish the exact cause.

**Recommendation:** keep fields for observed versus classified laps, flag
disagreements and document their use. Do not overwrite race labels or truncate
every timing log merely to force agreement.

## 6. Finishing-position fields use inconsistent historical conventions

Thirteen rows in Brazil 1983 (`raceId=452`) disagree between `position` and
`positionOrder`. For example, Lauda has `position=3` but `positionOrder=2`;
Laffite has `position=4` but `positionOrder=3`. The same race contains
disqualified drivers, and `positionOrder` places them after the classified entries.

**Recommendation:** preserve both columns and document their different ordering.
The milestone explicitly defines the target using `positionOrder <= 3`; do not
silently switch to `position <= 3`. This race is outside the modeling window
but can affect long-history descriptive statistics.

## 7. Withdrawal labels are not a universal no-start rule

Twenty-three historical entries have `status='Withdrew'` and completed laps;
five have `positionText='W'` and completed laps. They demonstrate that withdrawing
can happen after starting. A global “Withdrew means DNS” cleaning rule is unsafe.

In 2014–2024, every `W` entry has zero laps. Seventeen of those entries have a
status other than `Withdrew`, including failure, illness and retirement labels.
This reinforces the previously identified Q3 issue: status-only classification
misses relevant information in `positionText`.

**Applied:** start eligibility now uses both columns and lap evidence. Q3
excludes 28 marked non-starts in 2014–2024, retains positive-lap withdrawals,
and marks 112 remaining zero-lap entries uncertain. Main, positive-lap-only
rates and eligibility bounds are exported, including constructor-level sensitivity. Do not assume that a rule valid in modern seasons is valid for all eras.

## 8. Other metadata disagreements and false alarms

Qualifying and results disagree on car number in **32 entries**, five of them
in 2003–2024. These now use results as the canonical entry-metadata authority in cleaned
qualifying, with original numbers and change flags retained. This reconciles
representations; it does not prove which conflicting number is physically correct. Number is not
one of the final 28 features, so they do not directly change this model.

The following checks passed:

- No duplicated natural keys in qualifying, driver standings, constructor
  standings/results or sprint results; no duplicate `(year, round)` race keys.
- All lap-time and pit-stop duration strings agree with their milliseconds columns.
- Race date years agree with season years; circuit coordinates are in valid ranges.
- No modeled-era negative points/laps, duplicated non-missing car numbers,
  or duplicated qualifying positions were found in the exploratory checks.

An apparent **82 modern constructor-points discrepancies** disappears entirely
when race points **plus sprint points** are compared with constructor results.
Those totals should not be “fixed” to match race points alone.

Very long race laps can include stoppages; incomplete qualifying-session times
can reflect elimination or a missing valid lap. A large or missing value is not,
by itself, proof of corruption.

## Current implementation and remaining limits

The notebook now runs these cross-table checks before cleaning, applies the
supported repairs, and exports a repair log and before/after plot. The raw-source
flags deliberately remain available even when a cleaned representation has been
reconciled. A row flag is evidence to review, not a claim that a guessed value is true.

Unresolved grid conflicts remain flagged alongside two incomplete pit
histories, timing/classification discrepancies, and three older constructor
aggregates. Start and failure-type uncertainties are addressed with explicit
conventions and sensitivity analyses. Exact reconstruction needs better source
records; see `FIXES_AND_REMAINING_ISSUES.md` for recommendations.

This deeper pass improves coverage but does not prove that no other errors exist.
The defensible claim is that these checks ran, their findings were recorded, and
supported repairs are distinguished from unresolved cases.
