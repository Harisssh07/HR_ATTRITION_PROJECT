"""
data_cleaning.py
----------------
Reusable, individually testable cleaning steps for the HR attrition dataset.
Each function takes a DataFrame and returns a new DataFrame, so the notebook can
show before/after results for every step.  `clean_pipeline` chains them together.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "HR_Employee_Attrition.csv"
CLEAN_PATH = ROOT / "data" / "processed" / "cleaned_hr_data.csv"

EDUCATION_LABELS = {1: "Below College", 2: "College", 3: "Bachelor", 4: "Master", 5: "Doctor"}
SATISFACTION_LABELS = {1: "Low", 2: "Medium", 3: "High", 4: "Very High"}
AGE_BINS, AGE_LABELS = [17, 25, 35, 45, 55, 100], ["18-25", "26-35", "36-45", "46-55", "56+"]
SALARY_BINS = [0, 3000, 6000, 9000, 12000, np.inf]
SALARY_LABELS = ["< 3K", "3K-6K", "6K-9K", "9K-12K", "12K+"]
EXP_BINS, EXP_LABELS = [-1, 2, 5, 10, 20, 100], ["0-2 yrs", "3-5 yrs", "6-10 yrs", "11-20 yrs", "20+ yrs"]
TENURE_BINS, TENURE_LABELS = [-1, 1, 3, 5, 10, 100], ["0-1 yr", "2-3 yrs", "4-5 yrs", "6-10 yrs", "10+ yrs"]


def load_raw(path=RAW_PATH):
    return pd.read_csv(path)


def audit(df):
    """Return a one-table data-quality summary (dtype, missing, unique)."""
    return pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "missing_%": (df.isna().mean() * 100).round(2),
        "unique": df.nunique(),
    })


def remove_duplicates(df):
    return df.drop_duplicates().drop_duplicates(subset="EmployeeID").reset_index(drop=True)


def standardize_text(df):
    """Trim whitespace and unify casing variants (e.g. ' SALES ' / 'sales' -> 'Sales')."""
    df = df.copy()
    text_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    for col in text_cols:
        stripped = df[col].str.strip()
        # canonical spelling = most frequent variant for each case-insensitive key
        canon = (stripped.dropna().groupby(stripped.dropna().str.casefold())
                 .agg(lambda s: s.value_counts().index[0]))
        df[col] = stripped.str.casefold().map(canon)
    return df


def drop_constant_columns(df):
    const = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
    return df.drop(columns=const), const


def impute_missing(df):
    """Median (grouped by JobLevel/JobRole where sensible) for numerics, mode for categoricals."""
    df = df.copy()
    # salary depends strongly on job level -> group median is more accurate than global median
    df["MonthlyIncome"] = df["MonthlyIncome"].fillna(df.groupby("JobLevel")["MonthlyIncome"].transform("median"))
    # experience depends on age
    age_band = pd.cut(df["Age"], AGE_BINS, labels=AGE_LABELS)
    df["TotalWorkingYears"] = df["TotalWorkingYears"].fillna(
        df.groupby(age_band, observed=True)["TotalWorkingYears"].transform("median"))
    for col in df.columns[df.isna().any()]:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = df[col].fillna(df[col].mode()[0])
    return df


def fix_dtypes_and_logic(df):
    """Cast ordinal codes to int and repair logically impossible values."""
    df = df.copy()
    for col in ["MonthlyIncome", "TotalWorkingYears", "JobSatisfaction"]:
        df[col] = df[col].round().astype(int)
    # tenure cannot exceed total experience
    df["TotalWorkingYears"] = np.maximum(df["TotalWorkingYears"], df["YearsAtCompany"])
    for col in ["YearsInCurrentRole", "YearsWithCurrManager", "YearsSinceLastPromotion"]:
        df[col] = np.minimum(df[col], df["YearsAtCompany"])
    return df


def engineer_features(df):
    """Create target flag, readable labels and the bands used by EDA and Power BI."""
    df = df.copy()
    df["Attrition_Flag"] = (df["Attrition"] == "Yes").astype(int)
    df["AgeGroup"] = pd.cut(df["Age"], AGE_BINS, labels=AGE_LABELS).astype(str)
    df["SalaryBand"] = pd.cut(df["MonthlyIncome"], SALARY_BINS, labels=SALARY_LABELS, right=False).astype(str)
    df["ExperienceBand"] = pd.cut(df["TotalWorkingYears"], EXP_BINS, labels=EXP_LABELS).astype(str)
    df["TenureBand"] = pd.cut(df["YearsAtCompany"], TENURE_BINS, labels=TENURE_LABELS).astype(str)
    df["EducationLevel"] = df["Education"].map(EDUCATION_LABELS)
    df["JobSatisfactionLevel"] = df["JobSatisfaction"].map(SATISFACTION_LABELS)
    df["EnvironmentSatisfactionLevel"] = df["EnvironmentSatisfaction"].map(SATISFACTION_LABELS)
    df["WorkLifeBalanceLevel"] = df["WorkLifeBalance"].map({1: "Bad", 2: "Good", 3: "Better", 4: "Best"})
    # sort keys so Power BI can order bands correctly
    df["AgeGroup_Sort"] = df["AgeGroup"].map({k: i for i, k in enumerate(AGE_LABELS, 1)})
    df["SalaryBand_Sort"] = df["SalaryBand"].map({k: i for i, k in enumerate(SALARY_LABELS, 1)})
    df["ExperienceBand_Sort"] = df["ExperienceBand"].map({k: i for i, k in enumerate(EXP_LABELS, 1)})
    df["Education_Sort"] = df["Education"]
    return df


def clean_pipeline(df=None, save=True, verbose=True):
    df = load_raw() if df is None else df
    n0 = len(df)
    df = remove_duplicates(df)
    n1 = len(df)
    df = standardize_text(df)
    df, const = drop_constant_columns(df)
    missing_before = int(df.isna().sum().sum())
    df = impute_missing(df)
    df = fix_dtypes_and_logic(df)
    df = engineer_features(df)
    if verbose:
        print(f"Rows: {n0} -> {n1} (removed {n0 - n1} duplicates)")
        print(f"Constant columns dropped: {const}")
        print(f"Missing cells imputed: {missing_before}")
        print(f"Final shape: {df.shape}")
    if save:
        CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(CLEAN_PATH, index=False)
    return df


if __name__ == "__main__":
    clean_pipeline()
