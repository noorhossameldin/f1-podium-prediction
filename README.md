# Formula 1 Podium Prediction — Milestone 1

Predicts whether a driver finishes on the podium (`positionOrder <= 3`) using only information available
after qualifying and before the race start. Data: Formula 1 World Championship 1950–2024 (Kaggle / Ergast).

## Contents

| Path | What it is |
|---|---|
| `f1_podium_prediction.ipynb` | The single run-all notebook: audit, cleaning, EDA, data-engineering answers, features, models, ablation, XAI, inference |
| `report.pdf` | Analytical report, generated from the executed notebook |
| `make_report.py` | Rebuilds `report.pdf` from the executed notebook |
| `Data/` | The 14 raw CSV files (never modified; the notebook verifies this with file hashes) |
| `figures/` | Every figure, saved by the notebook |
| `outputs/` | Modeling table, model comparison, all hyperparameter trials, ablation and order-experiment results |

## How to run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace f1_podium_prediction.ipynb   # or open it and Run All (about 2 minutes)
python make_report.py                                                            # needs Google Chrome for the PDF step
```

On Kaggle: attach the dataset `rohanrao/formula-1-world-championship-1950-2020`, turn Internet on (the notebook
installs `shap` / `lime` if they are missing) and Run All. The data folder is detected automatically.

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
