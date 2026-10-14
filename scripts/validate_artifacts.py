"""Check execution and exported artifacts; scientific assumptions still need review."""

import ast
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
nb = nbformat.read(ROOT / "f1_podium_prediction.ipynb", as_version=4)
checks = {}


def check(name, condition):
    checks[name] = bool(condition)
    if not condition:
        raise AssertionError(name)


def literal_assignment(name):
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        for node in ast.parse(cell.source).body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == name for target in node.targets
            ):
                return ast.literal_eval(node.value)
    raise ValueError(f"Assignment not found: {name}")


code = [cell for cell in nb.cells if cell.cell_type == "code"]
check("all_code_cells_executed", all(cell.execution_count is not None for cell in code))
check("no_notebook_errors", not any(
    output.output_type == "error" for cell in code for output in cell.get("outputs", [])
))

raw = {path.stem: pd.read_csv(path, dtype=str, keep_default_na=False)
       for path in sorted((ROOT / "Data").glob("*.csv"))}
pk = literal_assignment("PRIMARY_KEYS")
fk = literal_assignment("FOREIGN_KEYS")
for table, keys in pk.items():
    check(f"primary_key_{table}", not raw[table].duplicated(keys).any()
          and not raw[table][keys].isin(["", "\\N"]).any().any())
for child, column, parent, parent_column in fk:
    check(f"foreign_key_{child}_{column}", raw[child][column].isin(raw[parent][parent_column]).all())

groups = literal_assignment("FEATURE_GROUPS")
features = [feature for group in groups.values() for feature in group]
table = pd.read_csv(ROOT / "outputs/modeling_table.csv", parse_dates=["date"])
check("unique_driver_race", not table.duplicated(["raceId", "driverId"]).any())
check("feature_columns_present", set(features).issubset(table.columns))
check("three_podiums_per_modeled_race", table.groupby("raceId").podium.sum().eq(3).all())
check("no_infinite_features", not np.isinf(table[features].to_numpy()).any())

results = pd.read_csv(ROOT / "Data/results.csv", na_values="\\N")
races = pd.read_csv(ROOT / "Data/races.csv", parse_dates=["date"])
history = (results.sort_values(["positionOrder", "resultId"])
           .drop_duplicates(["raceId", "driverId"])
           .merge(races[["raceId", "date", "circuitId"]], on="raceId")
           .sort_values(["date", "raceId", "driverId"]))
history["podium"] = (history.positionOrder <= 3).astype(int)
statuses = pd.read_csv(ROOT / "Data/status.csv").set_index("statusId").status
historical_status = history.statusId.map(statuses)
historical_nonstart = history.laps.le(0) & (
    history.positionText.isin(["W", "F", "P"])
    | historical_status.isin(literal_assignment("NOT_STARTED")))
history["eligible_start"] = ~historical_nonstart
history["eligible_mechanical"] = historical_status.isin(literal_assignment("MECHANICAL")) & ~historical_nonstart
labels = table.merge(history[["raceId", "driverId", "podium"]],
                     on=["raceId", "driverId"], validate="one_to_one", suffixes=("", "_raw"))
check("target_matches_raw_results", len(labels) == len(table) and labels.podium.eq(labels.podium_raw).all())

# Independently compute recent/career history for entries spanning all three splits.
sample = pd.concat([table[table.year == year].head(10) for year in [2003, 2019, 2022, 2024]])
for row in sample.itertuples():
    previous = history[(history.driverId == row.driverId) & (history.date < row.date)]
    expected = {
        "drv_podium_rate_5": previous.tail(5).podium.mean(),
        "drv_avg_finish_5": previous.tail(5).positionOrder.mean(),
        "drv_career_entries": len(previous),
        "drv_career_podium_rate": previous.podium.mean(),
        "drv_circuit_entries": int(previous.circuitId.eq(row.circuitId).sum()),
    }
    for feature, value in expected.items():
        check(f"history_{row.raceId}_{row.driverId}_{feature}",
              np.isclose(getattr(row, feature), value, equal_nan=True))
    team_history = history[(history.constructorId == row.constructorId) & (history.date < row.date)]
    previous_team_races = team_history.drop_duplicates("raceId").tail(10).raceId
    previous_team_entries = team_history[team_history.raceId.isin(previous_team_races)]
    starts = previous_team_entries.eligible_start.sum()
    mechanical_rate = previous_team_entries.eligible_mechanical.sum() / starts if starts else np.nan
    check(f"history_{row.raceId}_{row.driverId}_con_mech_rate_10",
          np.isclose(row.con_mech_rate_10, mechanical_rate, equal_nan=True))

comparison = pd.read_csv(ROOT / "outputs/model_comparison.csv")
check("metrics_for_every_model_and_split", set(comparison["set"]) == {"train", "val", "test"}
      and not comparison.duplicated(["model", "set"]).any()
      and comparison.groupby("model")["set"].nunique().eq(3).all())
metrics = ["ROC-AUC", "PR-AUC", "F1", "Precision", "Recall", "Brier", "Accuracy"]
check("metrics_in_valid_range", comparison[metrics].notna().all().all()
      and comparison[metrics].ge(0).all().all() and comparison[metrics].le(1).all().all())
check("thresholds_frozen_across_splits", comparison.groupby("model").threshold.nunique().eq(1).all())

ablation = pd.read_csv(ROOT / "outputs/ablation_results.csv")
check("ablation_all_groups_and_models", ablation.groupby("model").apply(
    lambda frame: len(frame) == 1 + 2 * len(groups)
    and set(frame[frame.setting == "drop"].group) == set(groups)
    and set(frame[frame.setting == "only"].group) == set(groups)
).all())
orders = pd.read_csv(ROOT / "outputs/preprocessing_order_experiments.csv")
check("at_least_two_order_experiments", orders.experiment.nunique() >= 2)
check("two_orders_per_experiment_and_model", orders.groupby(["experiment", "model"]).order.nunique().eq(2).all())

summary = json.loads((ROOT / "outputs/run_summary.json").read_text())
eligible = ["Logistic regression (tuned)", "Random forest", "Gradient boosting", "Shallow neural network"]
selected = comparison[(comparison["set"] == "val") & comparison.model.isin(eligible)].sort_values("PR-AUC").iloc[-1].model
check("selected_model_matches_validation_winner", selected == summary["selected_model"])
for model, values in summary["test_metrics"].items():
    recorded = comparison[(comparison["set"] == "test") & (comparison.model == model)].iloc[0]
    check(f"summary_metrics_{model}", all(np.isclose(recorded[metric], value, atol=0.000051)
                                         for metric, value in values.items()))

# Verify repairs against preserved source values, and the treatment of unresolved inputs.
clean_pit = pd.read_csv(ROOT / "outputs/cleaned_pit_stops.csv")
raw_pit = pd.read_csv(ROOT / "Data/pit_stops.csv")
repair = raw_pit.raceId.eq(1128) & raw_pit.stop.gt(raw_pit.lap)
check("pit_repair_preserves_population", len(clean_pit) == len(raw_pit))
check("pit_original_stop_preserved", clean_pit.stop_original.eq(raw_pit.stop).all())
check("pit_original_lap_preserved", clean_pit.lap_original.eq(raw_pit.lap).all())
check("pit_repair_swaps_only_identified_rows",
      clean_pit.stop.eq(raw_pit.stop.where(~repair, raw_pit.lap)).all()
      and clean_pit.lap.eq(raw_pit.lap.where(~repair, raw_pit.stop)).all())
check("pit_repair_no_duplicate_keys", not clean_pit.duplicated(["raceId", "driverId", "stop"]).any())
pit_sequence = clean_pit.groupby(["raceId", "driverId"]).stop.agg(["min", "max", "size"])
check("pit_repair_no_internal_sequence_gaps",
      pit_sequence["size"].eq(pit_sequence["max"] - pit_sequence["min"] + 1).all())
check("incomplete_pit_history_stays_flagged", clean_pit[clean_pit.incomplete_stop_history]
      [["raceId", "driverId"]].drop_duplicates().shape[0] == 2)

clean_q = pd.read_csv(ROOT / "outputs/cleaned_qualifying.csv")
raw_q = pd.read_csv(ROOT / "Data/qualifying.csv", na_values="\\N")
q_metadata = clean_q.merge(history[["raceId", "driverId", "constructorId", "number"]],
                           on=["raceId", "driverId"], validate="one_to_one", suffixes=("", "_canonical"))
check("qualifying_team_reconciled", q_metadata.constructorId.eq(q_metadata.constructorId_canonical).all())
check("qualifying_number_reconciled", np.isclose(q_metadata.number, q_metadata.number_canonical, equal_nan=True).all())
check("qualifying_source_team_preserved", clean_q.constructorId_original.eq(raw_q.constructorId).all())
check("qualifying_source_number_preserved", np.isclose(clean_q.number_original, raw_q.number, equal_nan=True).all())
check("qualifying_classification_preserved", clean_q.position.eq(raw_q.position).all())

clean_cr = pd.read_csv(ROOT / "outputs/cleaned_constructor_results.csv")
raw_cr = pd.read_csv(ROOT / "Data/constructor_results.csv")
check("four_identical_constructor_alias_rows_removed", len(raw_cr) - len(clean_cr) == 4)
check("constructor_aggregate_keys_unique", not clean_cr.duplicated(["raceId", "constructorId"]).any())
check("constructor_points_preserved", np.isclose(clean_cr.points.sum(), raw_cr.points.sum()))

metadata = pd.read_csv(ROOT / "outputs/cleaned_results_metadata.csv")
raw_result_metadata = metadata.merge(results, on="resultId", suffixes=("", "_raw"), validate="one_to_one")
check("rank_zero_representation_fixed", not metadata.fastest_lap_rank.eq(0).any())
check("source_rank_unchanged", np.isclose(raw_result_metadata["rank"], raw_result_metadata.rank_raw, equal_nan=True).all())
check("grid_source_preserved", raw_result_metadata.grid_original.eq(raw_result_metadata.grid_raw).all())
check("grid_changes_identifiable", metadata.grid.ne(metadata.grid_original).eq(metadata.grid_corrected).all())
check("grid_no_slots_inferred_in_main", metadata.grid_inferred.sum() == 0)
check("grid_no_assumed_assignments_in_main", metadata.grid_assignment_assumed.sum() == 0)
repair_log = pd.read_csv(ROOT / "outputs/cleaning_repairs.csv")
grid_repairs = repair_log[repair_log.field.eq("grid")]
check("four_official_grid_repairs_logged", len(grid_repairs) == 4 and grid_repairs.source_url.notna().all())
check("grid_original_conflicts_retained", metadata.grid_conflict_source.sum() == 8)
check("grid_no_unmarked_replacements", metadata.loc[metadata.grid_corrected, "grid_external_verified"].all())
verified = pd.read_csv(ROOT / "outputs/grid_external_verification.csv")
corrections = pd.read_csv(ROOT / "outputs/grid_verified_corrections.csv")
manifest = json.loads((ROOT / "outputs/grid_verified_sources.json").read_text())
check("eight_official_grid_entries_checked", len(verified) == 8 and not verified.duplicated(["raceId", "driverId"]).any())
check("four_official_grid_entries_changed", len(corrections) == 4 and verified.changed.sum() == 4)
check("official_grid_records_embedded_in_notebook", pd.DataFrame(literal_assignment("VERIFIED_GRID_RECORDS"))
      .equals(verified.drop(columns=["changed", "used_in_main_pipeline"])))
check("official_grid_manifest_matches_notebook", manifest["records"] == literal_assignment("VERIFIED_GRID_RECORDS")
      and manifest["guidance_reported_on"] == "2026-10-10" and "TA" in manifest["ta_guidance"])
logged_corrections = grid_repairs.copy()
logged_corrections["driverId"] = logged_corrections.driverId.astype(int)
logged_corrections["cleaned"] = logged_corrections.cleaned.astype(int)
repair_evidence = logged_corrections.merge(corrections, on=["raceId", "driverId"],
                                         suffixes=("_log", "_evidence"), validate="one_to_one")
check("official_grid_log_matches_evidence", len(repair_evidence) == 4
      and repair_evidence.cleaned.eq(repair_evidence.verified_grid).all()
      and repair_evidence.source_url_log.eq(repair_evidence.source_url_evidence).all())
check("official_grid_sources_primary", verified.source_url.str.startswith(
    ("https://www.formula1.com/en/results/", "https://www.fia.com/sites/default/files/")).all()
    and verified.source_url.nunique() == 4)
expected_grids = {(119, 21): 12, (119, 35): 13, (938, 831): 11, (938, 832): 17,
                  (941, 828): 16, (941, 829): 17, (1141, 830): 17, (1141, 807): 18}
check("official_grid_expected_assignments", verified.set_index(["raceId", "driverId"]).verified_grid.to_dict() == expected_grids)
source_checks = verified.merge(results.loc[results.raceId.isin(verified.raceId), ["raceId", "driverId", "grid", "number"]],
    on=["raceId", "driverId"], validate="one_to_one").merge(races[["raceId", "date"]], on="raceId")
check("official_grid_source_values_match_csv", source_checks.source_grid.eq(source_checks.grid).all())
check("official_grid_car_numbers_match_csv", source_checks.car_number.eq(source_checks.number).all())
check("official_grid_event_dates_match_csv", source_checks.race_date.eq(source_checks.date.dt.strftime("%Y-%m-%d")).all())
check("official_grid_check_dates_recorded", verified.accessed_on.eq("2026-10-10").all())
check("official_grid_checks_used_in_main", verified.used_in_main_pipeline.all()
      and metadata.grid_external_verified.sum() == 8 and metadata.grid_corrected.sum() == 4)
grid_hypotheses = pd.read_csv(ROOT / "outputs/grid_assignment_hypotheses.csv")
check("grid_hypotheses_match_official_records", len(grid_hypotheses) == 8
      and grid_hypotheses.matches_verified_grid.all() and grid_hypotheses.verified.all())
check("grid_hypotheses_not_used_in_main", not grid_hypotheses.used_in_main_pipeline.any())
check("main_grid_policy_is_verified", summary["grid_policy"] == "Verified starting grid"
      and summary["grid_hypotheses_used_in_main"] is False
      and summary["grid_external_verified_entries"] == 8 and summary["grid_source_corrections"] == 4)
for rid, pair in grid_hypotheses.groupby("raceId"):
    source_race = results[results.raceId.eq(rid)]
    slots = source_race.loc[source_race.grid.gt(0), "grid"].astype(int)
    gaps = sorted(set(range(1, slots.max() + 1)) - set(slots))
    ordered_pair = pair.sort_values("qualifying_position")
    check(f"grid_{rid}_one_gap_and_pair", len(gaps) == 1 and len(pair) == 2 and pair.source_grid.nunique() == 1)
    check(f"grid_{rid}_candidate_slots", sorted(pair.assumed_grid.tolist()) == sorted([gaps[0], pair.source_grid.iloc[0]]))
    check(f"grid_{rid}_qualifying_order_hypothesis", ordered_pair.assumed_grid.is_monotonic_increasing)
    check(f"grid_{rid}_qualifying_evidence", ordered_pair.qualifying_position.tolist() ==
          raw_q.set_index(["raceId", "driverId"]).loc[[(rid, driver) for driver in ordered_pair.driverId], "position"].tolist())
    check(f"grid_{rid}_opposite_assignment", ordered_pair.alternative_grid.tolist() == ordered_pair.assumed_grid.tolist()[::-1])
canonical_metadata = metadata.sort_values("positionOrder").drop_duplicates(["raceId", "driverId"])
grid_check = table.merge(canonical_metadata[["raceId", "driverId", "grid", "grid_conflict", "grid_conflict_source",
                                            "grid_external_verified", "grid_verified_position"]],
                          on=["raceId", "driverId"], validate="one_to_one")
checked_inputs = grid_check[grid_check.grid_external_verified]
check("verified_grid_inputs_used", len(checked_inputs) == 8
      and checked_inputs.grid_pos.eq(checked_inputs.grid_verified_position).all()
      and checked_inputs.grid_drop.eq(checked_inputs.grid_pos - checked_inputs.quali_pos).all())
check("all_eight_source_grid_conflicts_resolved", grid_check.grid_conflict.sum() == 0
      and grid_check.grid_conflict_source.sum() == 8)
check("only_disputed_grid_positions_missing", grid_check.grid_pos.isna().eq(grid_check.grid_conflict).all())
gap_audit = pd.read_csv(ROOT / "outputs/grid_gap_audit.csv")
check("grid_gaps_not_universally_filled", len(gap_audit) == 17 and gap_audit.eligible_for_pair_hypothesis.sum() == 4)
grid_trials = pd.read_csv(ROOT / "outputs/grid_policy_sensitivity_trials.csv")
grid_sensitivity = pd.read_csv(ROOT / "outputs/grid_policy_sensitivity.csv")
check("grid_sensitivity_complete", len(grid_sensitivity) == 32 and
      grid_sensitivity.groupby(["model", "set"]).policy.nunique().eq(4).all())
check("grid_sensitivity_matched_seeds", grid_trials.groupby(["model", "policy", "set"]).seed.nunique()
      .eq([3 if name[0] == "Shallow neural network" else 1 for name in
           grid_trials.groupby(["model", "policy", "set"]).seed.nunique().index]).all())
check("grid_sensitivity_metrics_valid", grid_sensitivity[metrics].notna().all().all()
      and grid_sensitivity[metrics].ge(0).all().all() and grid_sensitivity[metrics].le(1).all().all())
for family, main_name in [("Logistic regression", "Logistic regression (tuned)"),
                          ("Random forest", "Random forest"), ("Gradient boosting", "Gradient boosting")]:
    observed = grid_sensitivity[(grid_sensitivity.model == family)
        & (grid_sensitivity.policy == "Verified starting grid") & (grid_sensitivity["set"] == "test")].iloc[0]
    main = comparison[(comparison.model == main_name) & (comparison["set"] == "test")].iloc[0]
    check(f"grid_main_matches_verified_policy_{family}", np.isclose(observed[metrics].to_numpy(dtype=float),
          main[metrics].to_numpy(dtype=float)).all())
grid_predictions = pd.read_csv(ROOT / "outputs/grid_policy_entry_predictions.csv")
check("grid_sensitivity_entry_probabilities_valid", grid_predictions.probability.between(0, 1).all())
check("grid_sensitivity_entries_are_flagged", grid_predictions.merge(
    grid_hypotheses[["raceId", "driverId"]], on=["raceId", "driverId"], how="inner").shape[0] == len(grid_predictions))
check("known_round_feature", table.round_number.eq(table["round"]).all())
check("qualifying_population_feature", table.qualifying_field_size.eq(
    table.raceId.map(raw_q.groupby("raceId").driverId.nunique())).all())
check("no_eventual_season_length_feature", "season_progress" not in features)
check("no_post_race_population_feature", "field_size" not in features)

entries = pd.read_csv(ROOT / "outputs/q3_entry_classification.csv")
check("q3_withdrawal_nonstarts_excluded", entries.loc[entries.positionText.eq("W") & entries.laps.eq(0), "start_eligibility"].eq("not started").all())
check("q3_completed_laps_are_confirmed_starts", entries.loc[entries.laps.gt(0), "start_eligibility"].eq("confirmed").all())
check("q3_ambiguous_zero_lap_retirements_marked", entries.loc[
    entries.raceId.eq(983) & entries.driverId.eq(8), "start_eligibility"].eq("uncertain").all())
sensitivity = pd.read_csv(ROOT / "outputs/q3_start_eligibility_sensitivity.csv")
check("q3_main_rates_inside_eligibility_bounds", sensitivity.assumed_start_rate.ge(
    sensitivity.eligibility_lower_bound - 1e-12).all() and sensitivity.assumed_start_rate.le(
        sensitivity.eligibility_upper_bound + 1e-12).all())
check("q3_rates_match_exported_classifications", all(
    np.isclose(row.assumed_start_rate,
               len(entries[(entries.era == row.era) & (entries.start_eligibility != "not started")
                           & (entries.status_class == "mechanical")])
               / len(entries[(entries.era == row.era) & (entries.start_eligibility != "not started")]))
    for row in sensitivity.itertuples()))

image_count = sum("image/png" in output.get("data", {})
                  for cell in code for output in cell.get("outputs", []))
report_html = ROOT / "report.html"
if report_html.exists():
    manifest = json.loads((ROOT / "outputs/report_manifest.json").read_text())
    report_text = report_html.read_text()
    gallery = (ROOT / "report_figures.html").read_text()
    check("report_manifest_matches_notebook", manifest["notebook_sha256"] == hashlib.sha256((ROOT / "f1_podium_prediction.ipynb").read_bytes()).hexdigest())
    check("report_manifest_matches_narrative", manifest["content_sha256"] == hashlib.sha256((ROOT / "report_content.md").read_bytes()).hexdigest())
    included = set(manifest["main_figures"])
    supplementary = set(manifest["supplementary_figures"])
    check("report_figure_inventory_complete", len(manifest["notebook_figures"]) == image_count and included.isdisjoint(supplementary) and included | supplementary == set(manifest["notebook_figures"]))
    check("selected_report_figures_present", report_text.count('<img src="data:image/png;') == len(included) and all(f'data-source="{name}"' in report_text for name in included))
    check("all_notebook_plots_in_report_html", len(included) == image_count and not supplementary)
    check("all_notebook_plots_in_figure_gallery", gallery.count('<img style="width:100%" src="data:image/png;') == image_count)
    for name, figure in manifest["notebook_figures"].items():
        source_images = [
            base64.b64decode(o["data"]["image/png"]) for o in nb.cells[figure["notebook_cell"]].get("outputs", []) if "image/png" in o.get("data", {})]
        check(f"report_original_image_{name}", any(hashlib.sha256(data).hexdigest() == figure["image_sha256"] for data in source_images) and f'id="{name}"' in gallery)
    pdf = PdfReader(ROOT / "report.pdf")
    check("report_pdf_page_target", len(pdf.pages) == manifest["editorial_pages"])
    check("report_pdf_no_section_overflow", all(f"{i} / {len(pdf.pages)}" in (page.extract_text() or "") for i, page in enumerate(pdf.pages, 1)))
    check("all_notebook_plots_in_report_pdf", sum(len(page.images) for page in pdf.pages) == image_count)
    pdf_text = re.sub(r"\s+", " ", "\n".join(page.extract_text() or "" for page in pdf.pages))
    for phrase in ["According to our TA", "Question 1", "Question 2", "Question 3", "Eligibility bounds", "Explanations are not causal effects", "Logistic regression achieves the highest", "9.1 Our pipeline", "9.2 Order", "predict_podium", "exploratory"]:
        check(f"report_required_content_{phrase}", phrase in pdf_text)

result = {
    "assessment_date": "2026-10-14",
    "python": sys.version.split()[0],
    "executed_code_cells": len(code),
    "modeling_rows": len(table),
    "modeling_races": int(table.raceId.nunique()),
    "modeling_features": len(features),
    "podiums": int(table.podium.sum()),
    "model_comparison_rows": len(comparison),
    "modeling_trials": len(pd.read_csv(ROOT / "outputs/all_model_trials.csv")),
    "ablation_configurations": len(ablation),
    "order_experiments": int(orders.experiment.nunique()),
    "notebook_plot_outputs": image_count,
    "selected_model": selected,
    "checks_passed": len(checks),
    "checks": checks,
    "raw_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in sorted((ROOT / "Data").glob("*.csv"))},
    "limits": "Artifact checks do not resolve the scientific and submission issues in REQUIREMENTS_AUDIT.md.",
}
(ROOT / "outputs/validation_summary.json").write_text(json.dumps(result, indent=2) + "\n")
print(f"PASS: {len(checks)} artifact checks; {len(code)} executed cells; {len(table)} rows; {image_count} plots.")
