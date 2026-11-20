"""
build_notebooks.py
------------------
Creates the two Jupyter notebooks as .ipynb files, executes every code cell (stdout, tables and
figures are captured and stored as cell outputs) so the notebooks open fully rendered on GitHub.
A lightweight executor is used because the notebooks are authored programmatically.
"""
import base64
import contextlib
import io
import json
import sys
import traceback
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(True)}


def run_cells(cells, workdir):
    """Execute code cells sequentially in one namespace and attach outputs."""
    ns, count = {"__name__": "__main__"}, 0
    import os
    os.chdir(workdir)
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        count += 1
        src = "".join(cell["source"])
        buf = io.StringIO()
        outputs = []
        plt.close("all")
        try:
            with contextlib.redirect_stdout(buf):
                last_expr = None
                import ast
                tree = ast.parse(src)
                if tree.body and isinstance(tree.body[-1], ast.Expr):
                    last_expr = ast.Expression(tree.body.pop().value)
                exec(compile(tree, "<cell>", "exec"), ns)
                result = eval(compile(last_expr, "<cell>", "eval"), ns) if last_expr else None
        except Exception:
            traceback.print_exc()
            raise
        if buf.getvalue():
            outputs.append({"output_type": "stream", "name": "stdout", "text": buf.getvalue().splitlines(True)})
        if result is not None and not isinstance(result, plt.Figure):
            data = {"text/plain": [repr(result)]}
            if hasattr(result, "to_html"):
                data["text/html"] = [result.to_html(max_rows=30, max_cols=30)]
                data["text/plain"] = [result.to_string(max_rows=30, max_cols=14)]
            outputs.append({"output_type": "execute_result", "execution_count": count, "metadata": {}, "data": data})
        for num in plt.get_fignums():
            fig = plt.figure(num)
            b = io.BytesIO()
            fig.savefig(b, format="png", dpi=110, bbox_inches="tight", facecolor="white")
            outputs.append({"output_type": "display_data", "metadata": {},
                            "data": {"image/png": base64.b64encode(b.getvalue()).decode(),
                                     "text/plain": ["<Figure>"]}})
        plt.close("all")
        cell["outputs"], cell["execution_count"] = outputs, count


def write_nb(cells, name):
    nb = {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python", "version": "3.12"}}}
    path = NB_DIR / name
    path.write_text(json.dumps(nb, indent=1))
    print("wrote", path)


# =============================================================================== NOTEBOOK 1
NB1 = [
md("""
# HR Analytics - Employee Attrition
## Notebook 1: Data Cleaning & Exploratory Data Analysis

**Goal:** understand *who* leaves the organisation and *why*, before building any model.

**Workflow**
1. Load & inspect the raw data
2. Data-quality audit (missing values, duplicates, inconsistent text)
3. Cleaning & feature engineering
4. Exploratory Data Analysis - age, gender, department, job role, salary, satisfaction, overtime, experience
5. Key insights

> **Data note:** the dataset is a *synthetic* 1,470-employee HR dataset modelled on the IBM HR Analytics structure
> (see `src/generate_dataset.py`). Replace `data/raw/HR_Employee_Attrition.csv` with a real export to re-run on live data.
"""),
code("""
import sys, warnings
sys.path.insert(0, "../src")
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import data_cleaning as dc
import eda

eda.set_style()
IMG = "../images/eda"
pd.set_option("display.max_columns", 50)
"""),
md("## 1. Load & inspect the raw data"),
code("""
raw = pd.read_csv("../data/raw/HR_Employee_Attrition.csv")
print(f"Shape: {raw.shape[0]:,} rows x {raw.shape[1]} columns")
raw.head()
"""),
code("raw.describe().T.round(1)"),
md("## 2. Data-quality audit"),
code("""
audit = dc.audit(raw)
audit[audit["missing"] > 0]
"""),
code("""
print("Exact duplicate rows      :", raw.duplicated().sum())
print("Duplicate EmployeeIDs     :", raw["EmployeeID"].duplicated().sum())
print("Constant columns          :", [c for c in raw.columns if raw[c].nunique() <= 1])
print()
print("Department spellings found:", raw["Department"].unique().tolist())
print("Job roles (sample)        :", sorted(raw["JobRole"].dropna().unique())[:6])
"""),
md("""
**Findings**
- 68 missing cells across `MonthlyIncome`, `JobSatisfaction`, `TotalWorkingYears`, `BusinessTravel`
- 20 duplicated employee records
- Inconsistent text (`" SALES "`, lower-case job roles)
- 3 constant columns (`EmployeeCount`, `Over18`, `StandardHours`) carry no information
"""),
md("## 3. Cleaning - step by step"),
code("""
df = dc.remove_duplicates(raw)
print(f"Duplicates removed: {len(raw) - len(df)}  ->  {len(df):,} unique employees")
"""),
code("""
df = dc.standardize_text(df)
print("Department values now:", df["Department"].unique().tolist())
"""),
code("""
df, dropped = dc.drop_constant_columns(df)
print("Dropped constant columns:", dropped)
"""),
md("""
**Missing values strategy**
- `MonthlyIncome` -> median of the employee's *job level* (pay is driven by level)
- `TotalWorkingYears` -> median of the employee's *age band*
- Other numeric -> median, categorical -> mode
"""),
code("""
print("Missing before:", int(df.isna().sum().sum()))
df = dc.impute_missing(df)
df = dc.fix_dtypes_and_logic(df)
print("Missing after :", int(df.isna().sum().sum()))
"""),
md("### Feature engineering\nBands and readable labels are created here so they can be reused directly in Power BI."),
code("""
df = dc.engineer_features(df)
df[["Age", "AgeGroup", "MonthlyIncome", "SalaryBand", "TotalWorkingYears", "ExperienceBand",
    "JobSatisfaction", "JobSatisfactionLevel", "Attrition_Flag"]].head()
"""),
code("""
df.to_csv("../data/processed/cleaned_hr_data.csv", index=False)
print("Saved cleaned dataset:", df.shape)
"""),
md("## 4. Exploratory Data Analysis"),
md("### 4.1 Overall attrition"),
code("""
total, left = len(df), int(df["Attrition_Flag"].sum())
print(f"Total employees : {total:,}")
print(f"Employees left  : {left}")
print(f"Attrition rate  : {left/total:.1%}")
print(f"Average age     : {df['Age'].mean():.1f}")
eda.plot_overview(df, IMG);
"""),
md("### 4.2 Department & gender"),
code("""
display_tbl = eda.attrition_rate_table(df, "Department")
eda.plot_department(df, IMG)
display_tbl
"""),
code("""
tbl = eda.attrition_rate_table(df, "Gender")
eda.plot_gender(df, IMG)
tbl
"""),
md("""
> Gender shows a small gap, but with ~600 female employees a 3-point difference is within normal sampling noise;
> it should be monitored, not treated as a driver.
"""),
md("### 4.3 Job role"),
code("""
tbl = eda.attrition_rate_table(df, "JobRole").sort_values("Attrition_%", ascending=False)
eda.plot_job_role(df, IMG)
tbl
"""),
md("### 4.4 Age"),
code("""
tbl = eda.attrition_rate_table(df, "AgeGroup", eda.ORDER["AgeGroup"])
eda.plot_age(df, IMG)
tbl
"""),
md("### 4.5 Salary"),
code("""
tbl = eda.attrition_rate_table(df, "SalaryBand", eda.ORDER["SalaryBand"])
eda.plot_salary(df, IMG)
tbl
"""),
md("### 4.6 Job satisfaction"),
code("""
tbl = eda.attrition_rate_table(df, "JobSatisfactionLevel", eda.ORDER["JobSatisfactionLevel"])
eda.plot_job_satisfaction(df, IMG)
tbl
"""),
md("### 4.7 Overtime"),
code("""
tbl = eda.attrition_rate_table(df, "OverTime", ["No", "Yes"])
eda.plot_overtime(df, IMG)
tbl
"""),
code("""
eda.plot_overtime_satisfaction_heatmap(df, IMG);
"""),
md("### 4.8 Experience & tenure"),
code("""
eda.plot_experience(df, IMG);
"""),
md("### 4.9 Education"),
code("""
eda.plot_education(df, IMG);
"""),
md("### 4.10 Numeric profile of leavers vs stayers"),
code("""
eda.plot_distributions(df, IMG);
"""),
code("""
df.groupby("Attrition")[["Age", "MonthlyIncome", "TotalWorkingYears", "YearsAtCompany", "DistanceFromHome"]].mean().round(1)
"""),
md("### 4.11 Correlation analysis"),
code("""
eda.plot_correlation(df, IMG);
"""),
code("""
eda.attrition_correlations(df)
"""),
md("""
## 5. Key insights

| # | Insight | Evidence |
|---|---------|----------|
| 1 | **Overtime more than doubles attrition** | 26.0 % (overtime) vs 11.3 % (no overtime) |
| 2 | **Low pay is the strongest financial signal** | 35-38 % attrition below 6K/month vs 5.6 % above 12K |
| 3 | **Young employees leave the most** | 34 % for ages 18-25 vs 4 % for 46+ |
| 4 | **New joiners are the flight risk** | ~31 % attrition for employees with <= 5 years of experience |
| 5 | **Sales Representatives and Lab Technicians** are the hottest roles | 28 % and 22 % vs 15 % company average |
| 6 | **Low job satisfaction** lifts attrition | 22 % vs 12-14 % for other levels |
| 7 | **Senior / managerial roles are stable** | 3-6 % attrition |

**Next:** `02_Attrition_Prediction_Model.ipynb` turns these patterns into a predictive model.
"""),
]

# =============================================================================== NOTEBOOK 2
NB2 = [
md("""
# HR Analytics - Employee Attrition
## Notebook 2: Machine Learning - Attrition Prediction

**Goal:** predict which employees are likely to leave, rank the drivers, and export predictions for Power BI.

**Workflow**
1. Prepare features (encoding & scaling)
2. Train Logistic Regression, Decision Tree and Random Forest
3. Evaluate: accuracy, precision, recall, F1, confusion matrix, ROC-AUC
4. Feature importance
5. Predict and export to CSV for the Power BI dashboard
"""),
code("""
import sys, warnings
sys.path.insert(0, "../src")
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report

import eda, model_training as mt
eda.set_style()
IMG = "../images/model"
df = pd.read_csv("../data/processed/cleaned_hr_data.csv")
print(df.shape)
"""),
md("""
## 1. Feature preparation
- **Target:** `Attrition_Flag` (1 = left, 0 = stayed)
- **Removed:** `EmployeeID`, the target itself, and engineered label/band columns (they duplicate raw features)
- **Encoding:** one-hot encoding for categorical features
- **Scaling:** `StandardScaler` for Logistic Regression (distance-based); tree models are scale-invariant so they are left unscaled
"""),
code("""
X, y, num_cols, cat_cols = mt.prepare_xy(df)
print(f"{X.shape[1]} features -> {len(num_cols)} numeric, {len(cat_cols)} categorical")
print("Categorical:", cat_cols)
print()
print("Class balance:")
y.value_counts(normalize=True).rename({0: "Stayed", 1: "Left"}).round(3)
"""),
md("""
The classes are **imbalanced (~15 % leavers)**, so:
- the split is **stratified**
- models use **`class_weight='balanced'`**
- accuracy alone is misleading (predicting "everyone stays" gives ~85 %), so **recall and F1 on the "Left" class** are the main metrics
"""),
code("""
X_train, X_test, y_train, y_test = mt.split_data(X, y)
print(f"Train: {len(X_train)} rows ({y_train.mean():.1%} left)  |  Test: {len(X_test)} rows ({y_test.mean():.1%} left)")
"""),
md("## 2. Train & tune the models\n5-fold cross-validated grid search on the **training set only**, optimising F1."),
code("""
models = mt.build_models(num_cols, cat_cols)
fitted, cv_scores, best_params = mt.tune_models(models, X_train, y_train)
for name, p in best_params.items():
    print(f"{name:20s} CV F1 = {cv_scores[name]:.3f}   best params: {p}")
"""),
md("## 3. Evaluation on the unseen test set"),
code("""
metrics = mt.evaluate(fitted, X_test, y_test)
metrics
"""),
code("""
mt.plot_model_comparison(metrics, IMG);
"""),
code("""
mt.plot_confusion_matrices(fitted, X_test, y_test, IMG);
"""),
code("""
for name, m in fitted.items():
    pred = (m.predict_proba(X_test)[:, 1] >= 0.5).astype(int)
    print(f"--- {name} ---")
    print(classification_report(y_test, pred, target_names=["Stayed", "Left"], digits=3))
"""),
code("""
mt.plot_roc(fitted, X_test, y_test, IMG);
"""),
md("""
**Reading the results**
- **Random Forest** gives the best balance of precision, recall and ROC-AUC, so it is selected (selection is based on cross-validation F1 on the training data, not on the test set).
- The Decision Tree is the most interpretable but the weakest; Logistic Regression is a solid, explainable baseline.
- Precision for the "Left" class is moderate: for every 10 employees flagged, roughly 4 genuinely leave. That is acceptable for an *early-warning list* where the cost of a retention conversation is low, but the list should not be used for punitive decisions.
"""),
md("## 4. Decision threshold"),
code("""
best_name = max(cv_scores, key=cv_scores.get)
best = fitted[best_name]
thr = mt.best_threshold(best, X_train, y_train)
print(f"Selected model: {best_name}")
print(f"F1-optimal threshold (from out-of-fold TRAIN predictions): {thr:.2f}")
mt.evaluate({best_name: best}, X_test, y_test, threshold=thr)
"""),
md("## 5. Feature importance - what drives attrition?"),
code("""
mt.plot_feature_importance(fitted["Random Forest"], "Random Forest", IMG);
"""),
code("""
mt.feature_importance(fitted["Random Forest"], 10)
"""),
md("""
Pay and seniority (`MonthlyIncome`, `JobLevel`, `TotalWorkingYears`, `Age`) dominate, followed by **overtime**,
commute distance and manager tenure - consistent with the EDA findings.
"""),
md("""
## 6. Generate predictions for every employee
Each employee is scored with **out-of-fold** probabilities (5-fold): the model scoring an employee never saw that employee during training, so the dashboard figures are not inflated by memorisation.
"""),
code("""
proba = mt.out_of_fold_predictions(best, X, y, thr)
preds = mt.export_predictions(df, proba, thr, "../data/processed/attrition_predictions.csv")
preds[["EmployeeID", "Department", "JobRole", "Attrition", "Attrition_Probability",
       "Predicted_Attrition", "Risk_Level", "Prediction_Outcome"]].head(10)
"""),
code("""
print(preds["Risk_Level"].value_counts().to_string())
print()
print(preds["Prediction_Outcome"].value_counts().to_string())
"""),
code("""
# Actual attrition rate by predicted risk tier - a quick calibration check
(preds.groupby("Risk_Level")["Attrition_Flag"].agg(Employees="size", Actual_Attrition_Rate="mean")
      .reindex(["Low", "Medium", "High"]).round(3))
"""),
md("""
The risk tiers separate well: the *High* tier has several times the real attrition rate of the *Low* tier - the property HR actually needs to prioritise retention conversations.
"""),
code("""
import joblib
joblib.dump({"model": best, "threshold": thr, "features": list(X.columns), "name": best_name},
            "../models/attrition_model.joblib")
print("Model saved -> models/attrition_model.joblib")
"""),
md("""
## 7. Scoring a new employee (demo)
"""),
code("""
bundle = joblib.load("../models/attrition_model.joblib")
new_emp = X.iloc[[0]].copy()
new_emp.loc[:, "OverTime"] = "Yes"; new_emp.loc[:, "MonthlyIncome"] = 3200; new_emp.loc[:, "Age"] = 24
p = bundle["model"].predict_proba(new_emp)[0, 1]
print(f"Attrition probability: {p:.1%}  ->  {'LEAVE' if p >= bundle['threshold'] else 'STAY'} (threshold {bundle['threshold']:.2f})")
"""),
]


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    for cells, name in [(NB1, "01_Data_Cleaning_and_EDA.ipynb"), (NB2, "02_Attrition_Prediction_Model.ipynb")]:
        run_cells(cells, NB_DIR)
        write_nb(cells, name)
