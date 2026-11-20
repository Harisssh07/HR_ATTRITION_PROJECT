"""
eda.py
------
One function per chart.  Every function takes the cleaned DataFrame, returns a
matplotlib Figure and (optionally) saves a PNG into `save_dir`.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

STAY, LEAVE, ACCENT, GREY = "#2E86AB", "#E4572E", "#F6AE2D", "#8D99AE"
ORDER = {
    "AgeGroup": ["18-25", "26-35", "36-45", "46-55", "56+"],
    "SalaryBand": ["< 3K", "3K-6K", "6K-9K", "9K-12K", "12K+"],
    "ExperienceBand": ["0-2 yrs", "3-5 yrs", "6-10 yrs", "11-20 yrs", "20+ yrs"],
    "TenureBand": ["0-1 yr", "2-3 yrs", "4-5 yrs", "6-10 yrs", "10+ yrs"],
    "JobSatisfactionLevel": ["Low", "Medium", "High", "Very High"],
    "EducationLevel": ["Below College", "College", "Bachelor", "Master", "Doctor"],
}


def set_style():
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({
        "figure.dpi": 110, "axes.titleweight": "bold", "axes.titlesize": 13,
        "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans",
    })


def _save(fig, name, save_dir):
    if save_dir:
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        fig.savefig(Path(save_dir) / f"{name}.png", dpi=150, bbox_inches="tight", facecolor="white")
    return fig


def attrition_rate_table(df, col, order=None):
    t = df.groupby(col).agg(Employees=("Attrition_Flag", "size"), Left=("Attrition_Flag", "sum"))
    t["Attrition_%"] = (t["Left"] / t["Employees"] * 100).round(1)
    if order:
        t = t.reindex([o for o in order if o in t.index])
    return t


def rate_bar(df, col, title, name, save_dir=None, order=None, horizontal=False, figsize=(8, 4.5)):
    """Attrition rate (%) per category with a dashed line at the company average."""
    set_style()
    t = attrition_rate_table(df, col, order)
    if order is None:
        t = t.sort_values("Attrition_%", ascending=horizontal)
    avg = df["Attrition_Flag"].mean() * 100
    colors = [LEAVE if v > avg else STAY for v in t["Attrition_%"]]
    fig, ax = plt.subplots(figsize=figsize)
    if horizontal:
        ax.barh(t.index.astype(str), t["Attrition_%"], color=colors)
        ax.axvline(avg, ls="--", color=GREY)
        for i, (v, n) in enumerate(zip(t["Attrition_%"], t["Employees"])):
            ax.text(v + 0.3, i, f"{v:.1f}%  (n={n})", va="center", fontsize=9)
        ax.set_xlabel("Attrition rate (%)")
        ax.set_xlim(0, t["Attrition_%"].max() * 1.25)
    else:
        bars = ax.bar(t.index.astype(str), t["Attrition_%"], color=colors, width=0.62)
        ax.axhline(avg, ls="--", color=GREY, label=f"Company average {avg:.1f}%")
        for b, n in zip(bars, t["Employees"]):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.4, f"{b.get_height():.1f}%",
                    ha="center", fontsize=9, fontweight="bold")
            ax.text(b.get_x() + b.get_width() / 2, 0.4, f"n={n}", ha="center", fontsize=8, color="white")
        ax.set_ylabel("Attrition rate (%)")
        ax.set_ylim(0, t["Attrition_%"].max() * 1.2)
        ax.legend(frameon=False)
        plt.setp(ax.get_xticklabels(), rotation=0)
    ax.set_title(title, loc="left")
    fig.tight_layout()
    return _save(fig, name, save_dir)


def plot_overview(df, save_dir=None):
    set_style()
    counts = df["Attrition"].value_counts().reindex(["No", "Yes"])
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.pie(counts, labels=["Stayed", "Left"], colors=[STAY, LEAVE], autopct="%1.1f%%", startangle=90,
           wedgeprops=dict(width=0.42, edgecolor="white"), textprops={"fontsize": 11})
    ax.text(0, 0, f"{len(df):,}\nemployees", ha="center", va="center", fontsize=13, fontweight="bold")
    ax.set_title("Overall Attrition", loc="left")
    return _save(fig, "01_overview", save_dir)


def plot_department(df, save_dir=None):
    return rate_bar(df, "Department", "Attrition Rate by Department", "02_department", save_dir)


def plot_gender(df, save_dir=None):
    return rate_bar(df, "Gender", "Attrition Rate by Gender", "03_gender", save_dir, figsize=(5.5, 4.5))


def plot_job_role(df, save_dir=None):
    return rate_bar(df, "JobRole", "Attrition Rate by Job Role", "04_job_role", save_dir,
                    horizontal=True, figsize=(9, 5))


def plot_age(df, save_dir=None):
    return rate_bar(df, "AgeGroup", "Attrition Rate by Age Group", "05_age_group", save_dir, ORDER["AgeGroup"])


def plot_salary(df, save_dir=None):
    return rate_bar(df, "SalaryBand", "Attrition Rate by Monthly Salary Band", "06_salary_band",
                    save_dir, ORDER["SalaryBand"])


def plot_job_satisfaction(df, save_dir=None):
    return rate_bar(df, "JobSatisfactionLevel", "Attrition Rate by Job Satisfaction", "07_job_satisfaction",
                    save_dir, ORDER["JobSatisfactionLevel"])


def plot_overtime(df, save_dir=None):
    return rate_bar(df, "OverTime", "Attrition Rate: Overtime vs No Overtime", "08_overtime",
                    save_dir, ["No", "Yes"], figsize=(5.5, 4.5))


def plot_experience(df, save_dir=None):
    set_style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    avg = df["Attrition_Flag"].mean() * 100
    for ax, (col, title) in zip(axes, [("ExperienceBand", "by Total Work Experience"),
                                       ("TenureBand", "by Tenure at Company")]):
        t = attrition_rate_table(df, col, ORDER[col])
        colors = [LEAVE if v > avg else STAY for v in t["Attrition_%"]]
        bars = ax.bar(t.index, t["Attrition_%"], color=colors, width=0.62)
        ax.axhline(avg, ls="--", color=GREY)
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.4, f"{b.get_height():.1f}%",
                    ha="center", fontsize=9, fontweight="bold")
        ax.set_title(f"Attrition Rate {title}", loc="left")
        ax.set_ylabel("Attrition rate (%)")
    fig.tight_layout()
    return _save(fig, "09_experience", save_dir)


def plot_education(df, save_dir=None):
    return rate_bar(df, "EducationLevel", "Attrition Rate by Education Level", "10_education",
                    save_dir, ORDER["EducationLevel"])


def plot_distributions(df, save_dir=None):
    set_style()
    cols = [("Age", "Age"), ("MonthlyIncome", "Monthly Income"), ("YearsAtCompany", "Years at Company"),
            ("DistanceFromHome", "Distance From Home (km)")]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (c, label) in zip(axes.ravel(), cols):
        sns.kdeplot(data=df, x=c, hue="Attrition", fill=True, common_norm=False, alpha=0.35,
                    palette={"No": STAY, "Yes": LEAVE}, hue_order=["No", "Yes"], ax=ax)
        ax.set_xlabel(label)
        ax.set_title(f"{label} distribution", loc="left")
    fig.suptitle("Who leaves?  Numeric profile of leavers vs stayers", x=0.01, ha="left",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    return _save(fig, "11_distributions", save_dir)


def plot_overtime_satisfaction_heatmap(df, save_dir=None):
    set_style()
    pv = df.pivot_table(index="JobSatisfactionLevel", columns="OverTime", values="Attrition_Flag",
                        aggfunc="mean").reindex(ORDER["JobSatisfactionLevel"]) * 100
    fig, ax = plt.subplots(figsize=(5.8, 4.3))
    sns.heatmap(pv, annot=True, fmt=".1f", cmap="OrRd", cbar_kws={"label": "Attrition rate (%)"},
                linewidths=1, ax=ax)
    ax.set_title("Attrition % : Job Satisfaction x Overtime", loc="left")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    return _save(fig, "12_overtime_satisfaction", save_dir)


def plot_correlation(df, save_dir=None):
    set_style()
    num = df.select_dtypes(include="number").drop(
        columns=[c for c in df.columns if c.endswith("_Sort") or c == "EmployeeID"], errors="ignore")
    corr = num.corr()
    fig, ax = plt.subplots(figsize=(11, 9))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, cmap="RdBu_r", center=0, annot=True, fmt=".2f", annot_kws={"size": 6.5},
                linewidths=0.4, cbar_kws={"shrink": 0.7}, ax=ax)
    ax.set_title("Correlation Matrix (numeric features)", loc="left")
    fig.tight_layout()
    return _save(fig, "13_correlation", save_dir)


def attrition_correlations(df, top=12):
    num = df.select_dtypes(include="number").drop(
        columns=[c for c in df.columns if c.endswith("_Sort") or c == "EmployeeID"], errors="ignore")
    c = num.corr()["Attrition_Flag"].drop("Attrition_Flag").sort_values(key=abs, ascending=False)
    return c.head(top).round(3)


ALL_PLOTS = [plot_overview, plot_department, plot_gender, plot_job_role, plot_age, plot_salary,
             plot_job_satisfaction, plot_overtime, plot_experience, plot_education, plot_distributions,
             plot_overtime_satisfaction_heatmap, plot_correlation]


def generate_all(df, save_dir):
    for fn in ALL_PLOTS:
        fig = fn(df, save_dir)
        plt.close(fig)
