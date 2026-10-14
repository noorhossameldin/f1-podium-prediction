# Formula 1 Podium Prediction — Milestone 1

Predicts whether a driver finishes on the podium (`positionOrder <= 3`) using only information available
after qualifying and before the race start. Data: Formula 1 World Championship 1950–2024 (Kaggle / Ergast).

## Team members

**Team 63**

| Student ID | Name |
|---|---|
| 58-20196 | Mohamed Ahmed Mohamed Abdelaziz |
| 58-3004 | Daniel Maged Shehata Youssef |
| 58-7146 | Marwan Montasser Morad Hassan Metwally |
| 58-2686 | Noor Hossameldin Ahmed Aboouf Ali |

## Contents

| Path | What it is |
|---|---|
| `f1_podium_prediction.ipynb` | The single run-all notebook: audit, cleaning, EDA, data-engineering answers, features, models, ablation, XAI, inference |
| `report.pdf` | 24-page analytical report: main analysis and explained Appendices A–I, including all 48 notebook plots |
| `report_content.md` | Curated report narrative; figures and comparison tables are inserted by the builder |
| `report_figures.html` | Browsable gallery of the same 48 plots included in the report PDF |
| `make_report.py` | Rebuilds the complete PDF, HTML, figure gallery and source manifest |
| `Data/` | The 14 raw CSV files (never modified; the notebook verifies this with file hashes) |
| `figures/` | Every figure, saved by the notebook |
| `outputs/` | Modeling table, model comparison, all hyperparameter trials, ablation and order-experiment results |

## How to run

The local environment is `.venv` (Python 3.12). In VS Code, open the notebook,
click **Select Kernel → Python Environments**, and select `.venv/bin/python`.
The named Jupyter kernel is **F1 Podium (.venv, Python 3.12)**.

To run the environment already installed in this folder:

```bash
source .venv/bin/activate
python scripts/run_notebook.py   # prints progress; saves the notebook after a successful run
python make_report.py           # rebuilds the PDF using Google Chrome
```

To recreate the verified package versions on another Python 3.12 installation:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python -m ipykernel install --prefix .venv --name f1-podium --display-name 'F1 Podium (.venv, Python 3.12)'
python scripts/run_notebook.py
python make_report.py
```

`requirements.txt` lists the direct dependencies; `requirements.lock.txt` records the
installed versions, including transitive dependencies. Full execution includes many
training runs and can take several minutes, depending on the machine.

On Kaggle: attach the dataset `rohanrao/formula-1-world-championship-1950-2020`, turn Internet on (the notebook
installs `shap` / `lime` if they are missing), select Kaggle's Python kernel, and Run All.
The data folder is detected automatically. Local execution does not establish that
the notebook has been successfully run or published on Kaggle.

## Understanding and reviewing the project

- `PROJECT_WALKTHROUGH.md`: a guided explanation, with worked examples and reading checkpoints.
- `REQUIREMENTS_AUDIT.md`: requirement-by-requirement assessment and issues to address before submission.
- `DATA_CONSISTENCY_AUDIT.md`: CSV-based findings, applied repairs, and unresolved disagreements; four grid corrections additionally use official sources after TA guidance.
- `GRID_RECONSTRUCTION.md`: TA guidance, four verified grid corrections with official links, preserved source values, and sensitivity experiments.
- `FIXES_AND_REMAINING_ISSUES.md`: what was repaired, why, and what still needs better evidence.
- `outputs/validation_summary.json`: independently checked artifact counts and consistency results.

Read the audit before treating the generated report's conclusions as final.
After running the notebook and rebuilding the report, rerun `python scripts/validate_artifacts.py`
to check the exported tables and report plot coverage.
For the additional CSV consistency checks, run `python scripts/audit_data_consistency.py`,
or `%run scripts/audit_data_consistency.py` in a notebook cell.

## Notebook sections

1. Setup and raw data load
2. EDA before cleaning and data audit (sentinels, formats, primary / foreign keys, duplicates)
3. Cleaning (sentinels, semantic typing, value fixes, one row per driver–race)
4. EDA after cleaning (impact of cleaning, coverage, target, grid)
5. Data-engineering questions 1–3
6. Leakage audit and feature engineering (with a scramble-the-future leakage test)
7. Train / validation / test split (chronological)
8. Feature selection evidence
9. Pre-processing and three order experiments
10. Models: grid rule, logistic regression (baseline + tuned), random forest, gradient boosting, shallow neural network
11. Model comparison on train / validation / test
12. Feature-group ablation
13. Explainability: permutation importance, SHAP, LIME
14. Inference function
15. Limitations and summary
