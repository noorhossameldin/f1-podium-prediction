"""CSV-only cross-table audit. Export findings; never modify the source CSVs."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
paths = sorted((ROOT / "Data").glob("*.csv"))
before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
data = {path.stem: pd.read_csv(path, na_values=["\\N", ""]) for path in paths}
races, results, qualifying = (data[name] for name in ["races", "results", "qualifying"])
keys = ["raceId", "driverId"]
facts = (results.merge(races[["raceId", "year", "name"]], on="raceId")
         .merge(data["drivers"][["driverId", "forename", "surname"]], on="driverId")
         .merge(data["status"], on="statusId"))
findings, rows = [], []


def flag(name, table, frame, classification, recommendation, groups=None):
    findings.append({"issue": name, "source_table": table, "rows": len(frame),
                     "groups": groups, "classification": classification,
                     "recommendation": recommendation})
    if len(frame):
        frame = frame.copy()
        frame.insert(0, "issue", name)
        frame.insert(1, "source_table", table)
        rows.append(frame)


q_join = qualifying.merge(facts[keys + ["constructorId", "number", "year", "name"]],
                          on=keys, suffixes=("_qualifying", "_results"))
flag("qualifying_constructor_mismatch", "qualifying",
     q_join[q_join.constructorId_qualifying.ne(q_join.constructorId_results)],
     "Conflicting team identity across tables",
     "Reconcile the specific entries; do not merge constructor IDs globally.")
flag("qualifying_car_number_mismatch", "qualifying",
     q_join[q_join.number_qualifying.notna() & q_join.number_results.notna()
            & q_join.number_qualifying.ne(q_join.number_results)],
     "Conflicting entry metadata; exact truth not established",
     "Keep both values and an audit flag until a documented authority is chosen.")

modern_grid = facts[facts.year.ge(2003) & facts.grid.gt(0)]
duplicate_grid = modern_grid[modern_grid.duplicated(["raceId", "grid"], keep=False)]
flag("duplicate_modern_grid_slot", "results", duplicate_grid,
     "Conflicting ordinary grid assignments",
     "Flag disputed slots; do not substitute qualifying order without accounting for penalties.",
     len(duplicate_grid[["raceId", "grid"]].drop_duplicates()))

pit = data["pit_stops"]
swapped = pit.stop.gt(pit.lap)
flag("pit_stop_lap_apparently_swapped", "pit_stops", pit[swapped],
     "Strong evidence of swapped fields in seven Monaco 2024 records",
     "Swap stop/lap for the identified records on a cleaned copy and verify chronology and keys.",
     int(pit.loc[swapped, "driverId"].nunique()))
pit_repaired = pit.copy()
pit_repaired.loc[swapped, ["stop", "lap"]] = pit.loc[swapped, ["lap", "stop"]].to_numpy()
sequence = pit_repaired.groupby(keys).stop.agg(["min", "max", "size"])
internal_gaps = sequence[sequence["size"].ne(sequence["max"] - sequence["min"] + 1)]
missing_first = sequence[sequence["min"].gt(1)].reset_index()
flag("pit_first_stop_not_recorded", "pit_stops", missing_first,
     "Incomplete coverage or numbering ambiguity",
     "Flag incomplete history; do not invent a missing stop or renumber the observed record.")
swap_verification = {
    "proposed_swap_rows": int(swapped.sum()),
    "duplicate_keys_after_proposal": int(pit_repaired.duplicated(keys + ["stop"]).sum()),
    "internal_sequence_gap_groups_after_proposal": len(internal_gaps),
}

lap_max = data["lap_times"].groupby(keys).lap.max().reset_index(name="max_recorded_lap")
lap_join = lap_max.merge(facts, on=keys)
flag("logged_laps_exceed_result_laps", "lap_times",
     lap_join[lap_join.max_recorded_lap.gt(lap_join.laps)],
     "Official classification and timing log disagree; not necessarily corruption",
     "Retain both fields; distinguish recorded laps from classified laps.")
flag("fastest_lap_exceeds_result_laps", "results", facts[facts.fastestLap.gt(facts.laps)],
     "Fastest-lap metadata contradicts classified lap total",
     "Flag the bundle; examine lap logs before choosing a source or setting values missing.")
pit_join = pit.merge(facts[keys + ["laps", "year", "name", "status"]], on=keys)
flag("pit_lap_exceeds_result_laps", "pit_stops", pit_join[pit_join.lap.gt(pit_join.laps)],
     "Timing versus classification discrepancy for a disqualified entry",
     "Preserve observed pit stops; do not overwrite official zero-lap classification automatically.")

flag("position_differs_position_order", "results",
     facts[facts.position.notna() & facts.position.ne(facts.positionOrder)],
     "Different classification/order conventions in one historical race",
     "Document the discrepancy; preserve the milestone target definition positionOrder <= 3.")
flag("withdrawal_label_with_completed_laps", "results",
     facts[facts.status.eq("Withdrew") & facts.laps.gt(0)],
     "Withdrawal can occur after a race start in historical records",
     "Do not define every Withdrew label as a non-start across all eras.")
flag("withdrawal_marker_with_completed_laps", "results",
     facts[facts.positionText.eq("W") & facts.laps.gt(0)],
     "Historical withdrawal markers do not universally imply DNS",
     "Condition start inference on era and lap evidence; retain unresolved cases.")
withdrawn_modern = facts[facts.year.between(2014, 2024) & facts.positionText.eq("W")]
flag("modern_withdrawal_marker_not_status_withdrew", "results",
     withdrawn_modern[~withdrawn_modern.status.eq("Withdrew")],
     "Withdrawal marker carries information missing from the status-only start rule",
     "Use both positionText and failure status when forming the Q3 numerator and denominator.")

rank_zero = facts[facts["rank"].eq(0)]
flag("fastest_lap_rank_zero", "results", rank_zero,
     "Numeric no-ranking marker, not an actual fastest-lap rank",
     "Represent unranked as missing in a derived rank column; preserve raw zero.")

team_entries = results[["raceId", "constructorId"]].drop_duplicates()
constructor_join = data["constructor_results"].merge(
    team_entries, on=["raceId", "constructorId"], how="left", indicator=True)
flag("constructor_result_without_matching_team_entry", "constructor_results",
     constructor_join[constructor_join._merge.eq("left_only")].drop(columns="_merge")
     .merge(races[["raceId", "year", "name"]], on="raceId"),
     "Valid constructor ID, but no corresponding race/team entry in results",
     "Reconcile by race; beware duplicate aggregates after mapping a conflicting team ID.")

facts["laps_behind_status"] = pd.to_numeric(
    facts.status.str.extract(r"^\+(\d+) Laps?$")[0], errors="coerce")
winner_laps = facts[facts.positionOrder.eq(1)].groupby("raceId").laps.max()
facts["winner_laps"] = facts.raceId.map(winner_laps)
flag("lapped_status_differs_lap_totals", "results",
     facts[facts.laps_behind_status.notna()
           & (facts.winner_laps - facts.laps).ne(facts.laps_behind_status)],
     "Status and classified lap totals disagree",
     "Flag, distinguish timing/classification conventions, and avoid guessed replacement values.")


def seconds(value):
    if pd.isna(value):
        return np.nan
    total = 0.0
    for part in str(value).split(":"):
        total = total * 60 + float(part)
    return total


# Eliminate apparent errors that are explained by other columns/tables.
race_points = results.groupby(["raceId", "constructorId"]).points.sum().reset_index(name="driver_points")
with_race = data["constructor_results"].merge(race_points, on=["raceId", "constructorId"])
with_race = with_race.merge(races[["raceId", "year"]], on="raceId")
modern_race_difference = with_race[with_race.year.ge(2003) & with_race.points.ne(with_race.driver_points)]
weekend_points = pd.concat([results, data["sprint_results"]]).groupby(
    ["raceId", "constructorId"]).points.sum().reset_index(name="weekend_points")
with_weekend = data["constructor_results"].merge(weekend_points, on=["raceId", "constructorId"])
with_weekend = with_weekend.merge(races[["raceId", "year"]], on="raceId")
modern_weekend_difference = with_weekend[
    with_weekend.year.ge(2003) & with_weekend.points.ne(with_weekend.weekend_points)]
screened = {
    "natural_key_duplicate_counts": {
        table: int(data[table].duplicated(columns).sum()) for table, columns in [
            ("races", ["year", "round"]), ("qualifying", keys),
            ("driver_standings", keys), ("constructor_standings", ["raceId", "constructorId"]),
            ("constructor_results", ["raceId", "constructorId"]), ("sprint_results", keys)]},
    "pit_duration_milliseconds_disagreements": int((~np.isclose(
        pit.duration.map(seconds), pit.milliseconds / 1000, equal_nan=True)).sum()),
    "lap_duration_milliseconds_disagreements": int((~np.isclose(
        data["lap_times"].time.map(seconds), data["lap_times"].milliseconds / 1000, equal_nan=True)).sum()),
    "race_date_year_disagreements": int(pd.to_datetime(races.date).dt.year.ne(races.year).sum()),
    "invalid_circuit_coordinate_rows": int((data["circuits"].lat.abs().gt(90)
                                           | data["circuits"].lng.abs().gt(180)).sum()),
    "modern_constructor_points_disagreements_ignoring_sprints": len(modern_race_difference),
    "modern_constructor_points_disagreements_including_sprints": len(modern_weekend_difference),
    "rank_zero_rows_with_recorded_fastest_time": int(rank_zero.fastestLapTime.notna().sum()),
    "modern_withdrawal_marker_rows_with_completed_laps": int(withdrawn_modern.laps.gt(0).sum()),
}
after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
assert before == after, "Raw files changed during the audit"
output = ROOT / "outputs"
pd.concat(rows, ignore_index=True, sort=False).to_csv(output / "data_consistency_flags.csv", index=False)
pd.DataFrame(findings).to_csv(output / "data_consistency_summary.csv", index=False)
(output / "data_consistency_audit.json").write_text(json.dumps({
    "findings": findings, "screened_checks": screened, "pit_swap_verification": swap_verification,
    "raw_files_unchanged": before == after, "raw_sha256": before,
    "scope": "Supplied CSVs only. Flags are evidence for review, not automatic corrections.",
}, indent=2) + "\n")
for finding in findings:
    print(f"{finding['issue']}: {finding['rows']}")
print("Pit swap proposal:", swap_verification)
print("Modern point discrepancies after including sprint points:", len(modern_weekend_difference))
print("Raw files unchanged:", before == after)
