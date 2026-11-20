"""
make_dashboard_preview.py
-------------------------
Renders a 3-page *design preview* of the Power BI dashboard from the real prediction file, so the
target layout, colours and numbers are visible before building in Power BI Desktop.
(Power BI .pbix files can only be authored inside Power BI Desktop - follow powerbi/PowerBI_Dashboard_Guide.md.)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "powerbi" / "preview"
OUT.mkdir(parents=True, exist_ok=True)

NAVY, BLUE, RED, GOLD, GREEN, BG, GREY = "#1F2A44", "#2E86AB", "#E4572E", "#F6AE2D", "#76B041", "#F3F6FA", "#8D99AE"
df = pd.read_csv(ROOT / "data" / "processed" / "attrition_predictions.csv")
AVG = df["Attrition_Flag"].mean() * 100


def rate(g):
    return g["Attrition_Flag"].mean() * 100


def new_page(title, subtitle):
    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    fig.patches.append(Rectangle((0, 0.925), 1, 0.075, transform=fig.transFigure, color=NAVY, zorder=0))
    fig.text(0.02, 0.962, title, color="white", fontsize=19, fontweight="bold", va="center")
    fig.text(0.98, 0.962, subtitle, color="#C9D3E6", fontsize=10.5, ha="right", va="center")
    return fig


def slicers(fig, y=0.875):
    labels = ["Department: All", "Gender: All", "Job Role: All", "Age Group: All", "Education: All"]
    for i, t in enumerate(labels):
        x = 0.02 + i * 0.196
        fig.patches.append(FancyBboxPatch((x, y), 0.18, 0.033, boxstyle="round,pad=0.002,rounding_size=0.008",
                                          transform=fig.transFigure, facecolor="white", edgecolor="#D5DCE8"))
        fig.text(x + 0.012, y + 0.0165, t + "   v", fontsize=9.5, color="#4A5568", va="center")


def kpi(fig, x, y, w, h, label, value, color=NAVY, sub=None):
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.002,rounding_size=0.01",
                                      transform=fig.transFigure, facecolor="white", edgecolor="#E3E8EF"))
    fig.patches.append(Rectangle((x, y), 0.005, h, transform=fig.transFigure, color=color))
    fig.text(x + 0.018, y + h - 0.03, label, fontsize=10, color="#4A5568", va="center")
    fig.text(x + 0.018, y + h * (0.42 if h < 0.11 else 0.38), value, fontsize=(21 if h < 0.11 else 26), fontweight="bold", color=color, va="center")
    if sub:
        fig.text(x + 0.018, y + 0.016, sub, fontsize=8.5, color=GREY, va="center")


def panel(fig, rect, title):
    ax = fig.add_axes(rect, facecolor="white")
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#D5DCE8")
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=10)
    ax.tick_params(colors="#4A5568", labelsize=8.5, length=0)
    return ax


def bars(ax, labels, vals, horizontal=False, fmt="{:.1f}%", color_rule=True, base=AVG):
    colors = [RED if (color_rule and v > base) else BLUE for v in vals]
    if horizontal:
        ax.barh(labels, vals, color=colors, height=0.62)
        for i, v in enumerate(vals):
            ax.text(v + max(vals) * 0.015, i, fmt.format(v), va="center", fontsize=8.5, color=NAVY)
        ax.set_xlim(0, max(vals) * 1.18)
        ax.set_xticks([])
        ax.invert_yaxis()
    else:
        ax.bar(labels, vals, color=colors, width=0.6)
        for i, v in enumerate(vals):
            ax.text(i, v + max(vals) * 0.02, fmt.format(v), ha="center", fontsize=8.5, color=NAVY, fontweight="bold")
        ax.set_ylim(0, max(vals) * 1.2)
        ax.set_yticks([])


# --------------------------------------------------------------------------------------- page 1
def page1():
    fig = new_page("HR Analytics  |  Employee Attrition Overview", "Page 1 of 3   -   Executive Summary")
    slicers(fig)
    n, left = len(df), int(df["Attrition_Flag"].sum())
    kpi(fig, 0.02, 0.73, 0.23, 0.12, "Total Employees", f"{n:,}", NAVY, "active + former employees")
    kpi(fig, 0.265, 0.73, 0.23, 0.12, "Employees Who Left", f"{left}", RED, "attrition = Yes")
    kpi(fig, 0.51, 0.73, 0.23, 0.12, "Attrition Rate", f"{AVG:.1f}%", RED, "employees left / total")
    kpi(fig, 0.755, 0.73, 0.225, 0.12, "Average Employee Age", f"{df['Age'].mean():.1f}", BLUE, "years")

    d = df.groupby("Department").apply(rate, include_groups=False).sort_values(ascending=False)
    ax = panel(fig, [0.04, 0.09, 0.27, 0.56], "Department-wise Attrition (%)")
    bars(ax, [x.replace("Research & Development", "R&D").replace("Human Resources", "HR") for x in d.index], d.values)
    ax.axhline(AVG, color=GREY, ls="--", lw=1)

    g = df.groupby("Gender")["Attrition_Flag"].agg(["sum", "size"])
    ax = fig.add_axes([0.355, 0.09, 0.24, 0.56], facecolor="white")
    ax.pie(g["sum"], labels=[f"{i}\n{int(v)} left" for i, v in g["sum"].items()], colors=[RED, BLUE], startangle=90,
           wedgeprops=dict(width=0.42, edgecolor="white"), textprops={"fontsize": 9, "color": NAVY},
           autopct="%1.0f%%", pctdistance=0.79)
    ax.set_title("Gender-wise Attrition (employees who left)", loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=10)

    r = df.groupby("JobRole").apply(rate, include_groups=False).sort_values(ascending=False)
    ax = panel(fig, [0.70, 0.09, 0.28, 0.56], "Job Role-wise Attrition (%)")
    bars(ax, list(r.index), r.values, horizontal=True)
    return fig


# --------------------------------------------------------------------------------------- page 2
def page2():
    fig = new_page("HR Analytics  |  Attrition Drivers", "Page 2 of 3   -   Salary, Satisfaction, Overtime, Experience")
    slicers(fig)
    ot = df.groupby("OverTime").apply(rate, include_groups=False)
    kpi(fig, 0.02, 0.76, 0.23, 0.10, "Overtime Attrition", f"{ot['Yes']:.1f}%", RED, "employees working overtime")
    kpi(fig, 0.265, 0.76, 0.23, 0.10, "No-Overtime Attrition", f"{ot['No']:.1f}%", BLUE, "")
    kpi(fig, 0.51, 0.76, 0.23, 0.10, "Overtime Impact", f"{ot['Yes'] / ot['No']:.1f}x", GOLD, "higher attrition with overtime")
    kpi(fig, 0.755, 0.76, 0.225, 0.10, "Avg Monthly Income", f"{df['MonthlyIncome'].mean():,.0f}", NAVY, "")

    sal = df.groupby("SalaryBand_Sort").apply(rate, include_groups=False)
    labs = ["< 3K", "3K-6K", "6K-9K", "9K-12K", "12K+"]
    ax = panel(fig, [0.04, 0.42, 0.20, 0.28], "Salary-wise Attrition (%)")
    bars(ax, labs, sal.values)
    js = df.groupby("JobSatisfaction").apply(rate, include_groups=False)
    ax = panel(fig, [0.29, 0.42, 0.20, 0.28], "Job Satisfaction Analysis (%)")
    bars(ax, ["Low", "Medium", "High", "Very High"], js.values)
    ax = panel(fig, [0.54, 0.42, 0.20, 0.28], "Overtime Impact on Attrition (%)")
    bars(ax, ["No OT", "Overtime"], [ot["No"], ot["Yes"]])
    ex = df.groupby("ExperienceBand_Sort").apply(rate, include_groups=False)
    ax = panel(fig, [0.79, 0.42, 0.19, 0.28], "Experience Analysis (%)")
    bars(ax, ["0-2", "3-5", "6-10", "11-20", "20+"], ex.values)

    pv = df.pivot_table(index="JobSatisfaction", columns="OverTime", values="Attrition_Flag", aggfunc="mean") * 100
    ax = fig.add_axes([0.04, 0.06, 0.30, 0.27], facecolor="white")
    im = ax.imshow(pv.values, cmap="OrRd", aspect="auto")
    ax.set_xticks([0, 1], ["No overtime", "Overtime"], fontsize=8.5)
    ax.set_yticks(range(4), ["Low", "Medium", "High", "Very High"], fontsize=8.5)
    for i in range(4):
        for j in range(2):
            ax.text(j, i, f"{pv.values[i, j]:.0f}%", ha="center", va="center", fontsize=10, fontweight="bold")
    ax.set_title("Satisfaction x Overtime (matrix visual)", loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=10)
    for s in ax.spines.values():
        s.set_visible(False)

    ed = df.groupby("Education_Sort").apply(rate, include_groups=False)
    ax = panel(fig, [0.40, 0.06, 0.26, 0.27], "Education-wise Attrition (%)")
    bars(ax, ["Below\nCollege", "College", "Bachelor", "Master", "Doctor"], ed.values)
    ax = panel(fig, [0.72, 0.06, 0.26, 0.27], "Attrition by Age Group (%)")
    ag = df.groupby("AgeGroup_Sort").apply(rate, include_groups=False)
    bars(ax, ["18-25", "26-35", "36-45", "46-55", "56+"], ag.values)
    return fig


# --------------------------------------------------------------------------------------- page 3
def page3():
    fig = new_page("HR Analytics  |  Predicted Attrition (ML)", "Page 3 of 3   -   Random Forest, out-of-fold predictions")
    slicers(fig)
    hi = df[df["Risk_Level"] == "High"]
    tp, fn, fp = [(df["Prediction_Outcome"] == k).sum() for k in ["True Positive", "False Negative", "False Positive"]]
    kpi(fig, 0.02, 0.76, 0.23, 0.10, "Predicted Leavers", f"{int((df['Predicted_Attrition'] == 'Yes').sum())}", RED, "model flags")
    kpi(fig, 0.265, 0.76, 0.23, 0.10, "High-Risk Employees", f"{len(hi)}", RED, f"{len(hi) / len(df):.1%} of workforce")
    kpi(fig, 0.51, 0.76, 0.23, 0.10, "Model Recall", f"{tp / (tp + fn):.0%}", BLUE, "share of real leavers caught")
    kpi(fig, 0.755, 0.76, 0.225, 0.10, "Model Precision", f"{tp / (tp + fp):.0%}", BLUE, "share of flags that are right")

    ax = panel(fig, [0.04, 0.38, 0.22, 0.32], "Employees by Risk Tier")
    rc = df["Risk_Level"].value_counts().reindex(["Low", "Medium", "High"])
    ax.bar(rc.index, rc.values, color=[GREEN, GOLD, RED], width=0.6)
    for i, v in enumerate(rc.values):
        ax.text(i, v + 12, str(v), ha="center", fontsize=9, fontweight="bold", color=NAVY)
    ax.set_yticks([])
    ax = panel(fig, [0.31, 0.38, 0.22, 0.32], "Actual Attrition Rate by Risk Tier (%)")
    ar = df.groupby("Risk_Level").apply(rate, include_groups=False).reindex(["Low", "Medium", "High"])
    ax.bar(ar.index, ar.values, color=[GREEN, GOLD, RED], width=0.6)
    for i, v in enumerate(ar.values):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=9, fontweight="bold", color=NAVY)
    ax.set_yticks([])
    ax = panel(fig, [0.58, 0.38, 0.40, 0.32], "Actual vs Predicted Attrition by Department")
    dd = df.groupby("Department").agg(Actual=("Attrition_Flag", "sum"),
                                      Predicted=("Predicted_Attrition_Flag", "sum"))
    x = np.arange(len(dd))
    ax.bar(x - 0.18, dd["Actual"], 0.36, color=BLUE, label="Actual")
    ax.bar(x + 0.18, dd["Predicted"], 0.36, color=RED, label="Predicted")
    ax.set_xticks(x, [i.replace("Research & Development", "R&D").replace("Human Resources", "HR") for i in dd.index])
    ax.legend(frameon=False, fontsize=8.5)

    ax = fig.add_axes([0.04, 0.04, 0.93, 0.27], facecolor="white")
    ax.axis("off")
    ax.set_title("Top High-Risk Employees (retention watch-list)", loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=6)
    top = hi.sort_values("Attrition_Probability", ascending=False).head(7)
    cols = ["EmployeeID", "Department", "JobRole", "Age", "MonthlyIncome", "OverTime", "JobSatisfactionLevel", "Attrition_Probability"]
    t = top[cols].copy()
    t["Attrition_Probability"] = (t["Attrition_Probability"] * 100).round(0).astype(int).astype(str) + "%"
    tb = ax.table(cellText=t.values, colLabels=["Employee ID", "Department", "Job Role", "Age", "Monthly Income",
                                                "Overtime", "Job Satisfaction", "Risk Score"],
                  loc="upper center", cellLoc="left", bbox=[0, 0, 1, 0.92])
    tb.auto_set_font_size(False)
    tb.set_fontsize(8.5)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor("#E3E8EF")
        if r == 0:
            cell.set_facecolor(NAVY)
            cell.set_text_props(color="white", fontweight="bold")
        elif c == 7:
            cell.set_text_props(color=RED, fontweight="bold")
    return fig


if __name__ == "__main__":
    for i, fn in enumerate([page1, page2, page3], 1):
        f = fn()
        f.savefig(OUT / f"dashboard_page{i}_preview.png", dpi=110, facecolor=BG)
        plt.close(f)
        print("saved page", i)
