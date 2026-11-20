"""
generate_dataset.py
-------------------
Builds a realistic *synthetic* HR employee dataset (1,470 employees, 30+ columns)
modelled on the structure of the well-known IBM HR Analytics dataset.

Why synthetic?  The project must run offline and be fully reproducible.  Attrition
is generated from a logistic model whose drivers (overtime, low satisfaction, low pay,
short tenure, frequent travel ...) mirror findings from published HR research, so the
EDA and ML results are meaningful.  The raw file also contains deliberately injected
"dirty data" (missing values, duplicates, inconsistent text) so the cleaning stage has
real work to do.

To use the real IBM dataset instead, drop it into data/raw/ with the same file name.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_EMPLOYEES = 1470
TARGET_ATTRITION_RATE = 0.16

ROLES = {
    # department: {role: (weight, base job level)}
    "Sales": {"Sales Executive": (0.68, 2), "Sales Representative": (0.24, 1), "Sales Manager": (0.08, 4)},
    "Research & Development": {
        "Research Scientist": (0.32, 1.5), "Laboratory Technician": (0.28, 1),
        "Manufacturing Director": (0.16, 3.5), "Healthcare Representative": (0.14, 2.5),
        "Research Director": (0.10, 4.5),
    },
    "Human Resources": {"HR Executive": (0.62, 1.5), "HR Manager": (0.38, 3.5)},
}
DEPT_WEIGHTS = {"Sales": 0.31, "Research & Development": 0.60, "Human Resources": 0.09}


def _choice(rng, options, probs, n):
    probs = np.array(probs, dtype=float)
    return rng.choice(options, size=n, p=probs / probs.sum())


def generate_clean_population(n=N_EMPLOYEES, seed=SEED):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"EmployeeID": np.arange(1001, 1001 + n)})

    df["Age"] = np.clip(rng.normal(37, 9, n).round(), 18, 60).astype(int)
    df["Gender"] = _choice(rng, ["Male", "Female"], [0.60, 0.40], n)
    df["MaritalStatus"] = _choice(rng, ["Married", "Single", "Divorced"], [0.46, 0.32, 0.22], n)
    df["Education"] = _choice(rng, [1, 2, 3, 4, 5], [0.11, 0.19, 0.39, 0.27, 0.04], n).astype(int)
    df["EducationField"] = _choice(
        rng, ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Other", "Human Resources"],
        [0.41, 0.32, 0.11, 0.09, 0.055, 0.015], n)

    df["Department"] = _choice(rng, list(DEPT_WEIGHTS), list(DEPT_WEIGHTS.values()), n)
    roles, base_level = [], []
    for dept in df["Department"]:
        names = list(ROLES[dept])
        w = [ROLES[dept][r][0] for r in names]
        r = _choice(rng, names, w, 1)[0]
        roles.append(r)
        base_level.append(ROLES[dept][r][1])
    df["JobRole"] = roles
    base_level = np.array(base_level)

    # experience, tenure, promotions
    twy = np.clip(df["Age"] - 22 + rng.normal(0, 3.5, n), 0, df["Age"] - 18).round().astype(int)
    df["TotalWorkingYears"] = twy
    yac = np.minimum(twy, (twy * rng.beta(1.6, 2.2, n) + rng.exponential(1.0, n)).round()).astype(int)
    df["YearsAtCompany"] = yac
    df["YearsInCurrentRole"] = (yac * rng.uniform(0.3, 1.0, n)).round().astype(int)
    df["YearsSinceLastPromotion"] = np.minimum(yac, rng.exponential(1.8, n).round()).astype(int)
    df["YearsWithCurrManager"] = (yac * rng.uniform(0.3, 1.0, n)).round().astype(int)
    df["NumCompaniesWorked"] = np.clip(rng.poisson(2.0, n), 0, 9)

    # level & salary (monthly)
    level = np.clip((base_level + twy / 14 + rng.normal(0, 0.45, n)).round(), 1, 5).astype(int)
    df["JobLevel"] = level
    income = 1500 + 2100 * level + 110 * twy + rng.normal(0, 800, n)
    df["MonthlyIncome"] = np.clip(income, 1009, 19999).round().astype(int)
    df["PercentSalaryHike"] = np.clip(rng.normal(15.2, 3.6, n).round(), 11, 25).astype(int)
    df["StockOptionLevel"] = _choice(rng, [0, 1, 2, 3], [0.43, 0.40, 0.10, 0.07], n).astype(int)

    # work-life attributes
    df["BusinessTravel"] = _choice(rng, ["Travel_Rarely", "Travel_Frequently", "Non-Travel"], [0.71, 0.19, 0.10], n)
    df["DistanceFromHome"] = np.clip(rng.exponential(8, n).round() + 1, 1, 29).astype(int)
    df["OverTime"] = _choice(rng, ["Yes", "No"], [0.28, 0.72], n)
    df["JobSatisfaction"] = _choice(rng, [1, 2, 3, 4], [0.20, 0.19, 0.30, 0.31], n).astype(int)
    df["EnvironmentSatisfaction"] = _choice(rng, [1, 2, 3, 4], [0.19, 0.19, 0.30, 0.32], n).astype(int)
    df["RelationshipSatisfaction"] = _choice(rng, [1, 2, 3, 4], [0.19, 0.21, 0.31, 0.29], n).astype(int)
    df["WorkLifeBalance"] = _choice(rng, [1, 2, 3, 4], [0.06, 0.23, 0.60, 0.11], n).astype(int)
    df["JobInvolvement"] = _choice(rng, [1, 2, 3, 4], [0.06, 0.25, 0.59, 0.10], n).astype(int)
    df["PerformanceRating"] = _choice(rng, [3, 4], [0.85, 0.15], n).astype(int)
    df["TrainingTimesLastYear"] = np.clip(rng.poisson(2.8, n), 0, 6)

    # constant columns (typical of HR exports; removed during cleaning)
    df["EmployeeCount"] = 1
    df["Over18"] = "Y"
    df["StandardHours"] = 80
    return df


def _attrition_logit(df):
    z = (
        1.25 * (df["OverTime"] == "Yes")
        + 0.55 * (df["JobSatisfaction"] == 1) + 0.25 * (df["JobSatisfaction"] == 2)
        + 0.35 * (df["EnvironmentSatisfaction"] == 1)
        + 0.40 * (df["WorkLifeBalance"] == 1) + 0.15 * (df["WorkLifeBalance"] == 2)
        - 0.030 * (df["Age"] - 37)
        - 0.00018 * (df["MonthlyIncome"] - 6500)
        - 0.070 * np.minimum(df["YearsAtCompany"], 10)
        + 0.45 * (df["BusinessTravel"] == "Travel_Frequently") - 0.40 * (df["BusinessTravel"] == "Non-Travel")
        + 0.035 * (df["DistanceFromHome"] - 9)
        + 0.50 * (df["MaritalStatus"] == "Single")
        + 0.50 * (df["StockOptionLevel"] == 0) - 0.40 * (df["StockOptionLevel"] >= 2)
        + 0.90 * (df["JobRole"] == "Sales Representative") + 0.30 * (df["JobRole"] == "Laboratory Technician")
        - 0.50 * df["JobRole"].isin(["Research Director", "Manufacturing Director", "Sales Manager", "HR Manager"])
        + 0.08 * np.minimum(df["YearsSinceLastPromotion"], 8)
        + 0.20 * (df["NumCompaniesWorked"] >= 5)
        + 0.40 * (df["JobInvolvement"] == 1) - 0.30 * (df["JobInvolvement"] == 4)
    )
    return z.to_numpy(dtype=float)


def _calibrate_intercept(z, target, rng_seed):
    lo, hi = -8.0, 4.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if (1 / (1 + np.exp(-(z + mid)))).mean() > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def build_raw_dataset(seed=SEED):
    rng = np.random.default_rng(seed + 1)
    df = generate_clean_population(seed=seed)
    z = _attrition_logit(df)
    z = z + _calibrate_intercept(z, TARGET_ATTRITION_RATE, seed)
    p = 1 / (1 + np.exp(-z))
    df["Attrition"] = np.where(rng.random(len(df)) < p, "Yes", "No")

    # ---- inject dirty data so the cleaning notebook has something to do ----------
    n = len(df)
    for col, frac in [("MonthlyIncome", 0.018), ("JobSatisfaction", 0.012),
                      ("TotalWorkingYears", 0.010), ("BusinessTravel", 0.008)]:
        idx = rng.choice(n, int(n * frac), replace=False)
        if col != "BusinessTravel":
            df[col] = df[col].astype(float)
        df.loc[idx, col] = np.nan
    # inconsistent text formatting
    idx = rng.choice(n, 18, replace=False)
    df.loc[idx[:9], "JobRole"] = df.loc[idx[:9], "JobRole"].str.lower()
    df.loc[idx[9:], "Department"] = " " + df.loc[idx[9:], "Department"].str.upper() + " "
    # duplicate records (exact copies)
    dup = df.sample(20, random_state=seed)
    df = pd.concat([df, dup], ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)
    return df


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "data" / "raw" / "HR_Employee_Attrition.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = build_raw_dataset()
    raw.to_csv(out, index=False)
    print(f"Saved {raw.shape[0]} rows x {raw.shape[1]} cols -> {out}")
