"""
model_training.py
-----------------
Feature preparation, model training (Logistic Regression, Decision Tree, Random Forest),
evaluation, charts and prediction export for Power BI.

Design decisions
* Stratified 80/20 split - attrition is imbalanced (~15 % leavers).
* class_weight="balanced" so the minority class (leavers) is not ignored.
* Scaling + one-hot for Logistic Regression; one-hot only for tree models (scale-invariant).
* Hyper-parameters tuned with 5-fold GridSearchCV on the TRAIN set only (scoring = F1).
* Final decision threshold chosen on out-of-fold TRAIN probabilities (never on the test set).
* Dashboard predictions are OUT-OF-FOLD (each employee is scored by a model that never saw
  that employee), so the numbers shown in Power BI are honest rather than memorised.
"""
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, classification_report, f1_score,
                             precision_score, recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from eda import GREY, LEAVE, STAY, set_style

ROOT = Path(__file__).resolve().parents[1]
RANDOM_STATE = 42
TARGET = "Attrition_Flag"

# columns that must never be used as features (IDs, target, redundant labels / bands / sort keys)
DROP_COLS = ["EmployeeID", "Attrition", "Attrition_Flag", "AgeGroup", "SalaryBand", "ExperienceBand",
             "TenureBand", "EducationLevel", "JobSatisfactionLevel", "EnvironmentSatisfactionLevel",
             "WorkLifeBalanceLevel", "AgeGroup_Sort", "SalaryBand_Sort", "ExperienceBand_Sort", "Education_Sort"]


def prepare_xy(df):
    X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
    y = df[TARGET]
    cat_cols = [c for c in X.columns if not pd.api.types.is_numeric_dtype(X[c])]
    num_cols = [c for c in X.columns if c not in cat_cols]
    return X, y, num_cols, cat_cols


def split_data(X, y, test_size=0.2):
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=RANDOM_STATE)


def _preprocessor(num_cols, cat_cols, scale):
    num = StandardScaler() if scale else "passthrough"
    return ColumnTransformer([("num", num, num_cols),
                              ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)])


def build_models(num_cols, cat_cols):
    """Return {name: (Pipeline, param_grid)}."""
    return {
        "Logistic Regression": (
            Pipeline([("prep", _preprocessor(num_cols, cat_cols, scale=True)),
                      ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE))]),
            {"clf__C": [0.03, 0.1, 0.3, 1, 3]}),
        "Decision Tree": (
            Pipeline([("prep", _preprocessor(num_cols, cat_cols, scale=False)),
                      ("clf", DecisionTreeClassifier(class_weight="balanced", random_state=RANDOM_STATE))]),
            {"clf__max_depth": [3, 4, 5, 6, 8], "clf__min_samples_leaf": [5, 10, 20, 40]}),
        "Random Forest": (
            Pipeline([("prep", _preprocessor(num_cols, cat_cols, scale=False)),
                      ("clf", RandomForestClassifier(class_weight="balanced_subsample", random_state=RANDOM_STATE,
                                                     n_jobs=-1))]),
            {"clf__n_estimators": [300], "clf__max_depth": [6, 10, None],
             "clf__min_samples_leaf": [3, 8], "clf__max_features": ["sqrt"]}),
    }


def tune_models(models, X_train, y_train):
    cv = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    fitted, cv_scores, best_params = {}, {}, {}
    for name, (pipe, grid) in models.items():
        gs = GridSearchCV(pipe, grid, scoring="f1", cv=cv, n_jobs=-1)
        gs.fit(X_train, y_train)
        fitted[name], cv_scores[name], best_params[name] = gs.best_estimator_, gs.best_score_, gs.best_params_
    return fitted, cv_scores, best_params


def evaluate(fitted, X_test, y_test, threshold=0.5):
    rows = []
    for name, model in fitted.items():
        proba = model.predict_proba(X_test)[:, 1]
        pred = (proba >= threshold).astype(int)
        rows.append({"Model": name, "Accuracy": accuracy_score(y_test, pred),
                     "Precision": precision_score(y_test, pred, zero_division=0),
                     "Recall": recall_score(y_test, pred), "F1-Score": f1_score(y_test, pred),
                     "ROC-AUC": roc_auc_score(y_test, proba)})
    return pd.DataFrame(rows).set_index("Model").round(3)


def best_threshold(model, X_train, y_train):
    """Threshold maximising F1 on out-of-fold training probabilities."""
    cv = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    oof = cross_val_predict(model, X_train, y_train, cv=cv, method="predict_proba")[:, 1]
    grid = np.arange(0.20, 0.71, 0.01)
    scores = [f1_score(y_train, oof >= t) for t in grid]
    return float(grid[int(np.argmax(scores))])


def out_of_fold_predictions(model, X, y, threshold):
    cv = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    return cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]


def risk_band(p):
    return pd.cut(p, [-0.01, 0.30, 0.60, 1.01], labels=["Low", "Medium", "High"]).astype(str)


# ----------------------------------------------------------------------------- charts
def plot_confusion_matrices(fitted, X_test, y_test, save_dir=None, threshold=0.5):
    set_style()
    fig, axes = plt.subplots(1, len(fitted), figsize=(5 * len(fitted), 4.4))
    for ax, (name, m) in zip(np.atleast_1d(axes), fitted.items()):
        pred = (m.predict_proba(X_test)[:, 1] >= threshold).astype(int)
        ConfusionMatrixDisplay.from_predictions(y_test, pred, display_labels=["Stayed", "Left"],
                                                cmap="Blues", colorbar=False, ax=ax)
        ax.set_title(name)
        ax.grid(False)
    fig.suptitle("Confusion Matrices (test set)", x=0.01, ha="left", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return _save(fig, "20_confusion_matrices", save_dir)


def plot_roc(fitted, X_test, y_test, save_dir=None):
    set_style()
    fig, ax = plt.subplots(figsize=(6, 5))
    for (name, m), c in zip(fitted.items(), [STAY, "#F6AE2D", LEAVE]):
        fpr, tpr, _ = roc_curve(y_test, m.predict_proba(X_test)[:, 1])
        ax.plot(fpr, tpr, color=c, lw=2.2, label=f"{name} (AUC {roc_auc_score(y_test, m.predict_proba(X_test)[:, 1]):.2f})")
    ax.plot([0, 1], [0, 1], ls="--", color=GREY)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("ROC Curves (test set)", loc="left")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    return _save(fig, "21_roc_curves", save_dir)


def plot_model_comparison(metrics, save_dir=None):
    set_style()
    ax = metrics.drop(columns="ROC-AUC").plot(kind="bar", figsize=(9, 4.8), color=[STAY, "#F6AE2D", LEAVE, "#6C757D"], width=0.8)
    ax.set_title("Model Comparison (test set, threshold 0.5)", loc="left")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("")
    plt.xticks(rotation=0)
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    for c in ax.containers:
        ax.bar_label(c, fmt="%.2f", fontsize=7, padding=2)
    fig = ax.get_figure()
    fig.tight_layout()
    return _save(fig, "22_model_comparison", save_dir)


def feature_importance(model, top=15):
    """Importance on the original-feature level (one-hot columns are summed back to their parent)."""
    prep, clf = model.named_steps["prep"], model.named_steps["clf"]
    names = prep.get_feature_names_out()
    imp = clf.feature_importances_ if hasattr(clf, "feature_importances_") else np.abs(clf.coef_[0])
    s = pd.Series(imp, index=names)
    parent = s.index.str.replace(r"^(num|cat)__", "", regex=True)
    cat_cols = prep.transformers_[1][2]
    parent = pd.Series([next((c for c in cat_cols if p.startswith(c + "_")), p) for p in parent], index=s.index)
    out = s.groupby(parent).sum().sort_values(ascending=False)
    return (out / out.sum() * 100).round(2).head(top)


def plot_feature_importance(model, model_name, save_dir=None, top=15):
    set_style()
    imp = feature_importance(model, top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(imp.index, imp.values, color=[LEAVE if i >= len(imp) - 3 else STAY for i in range(len(imp))])
    for i, v in enumerate(imp.values):
        ax.text(v + 0.1, i, f"{v:.1f}%", va="center", fontsize=9)
    ax.set_xlabel("Share of total importance (%)")
    ax.set_title(f"Top {top} Drivers of Attrition - {model_name}", loc="left")
    fig.tight_layout()
    return _save(fig, "23_feature_importance", save_dir)


def _save(fig, name, save_dir):
    if save_dir:
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        fig.savefig(Path(save_dir) / f"{name}.png", dpi=150, bbox_inches="tight", facecolor="white")
    return fig


# ----------------------------------------------------------------------------- export
def export_predictions(df, proba, threshold, path):
    out = df.copy()
    out["Attrition_Probability"] = proba.round(4)
    out["Predicted_Attrition_Flag"] = (proba >= threshold).astype(int)
    out["Predicted_Attrition"] = np.where(out["Predicted_Attrition_Flag"] == 1, "Yes", "No")
    out["Risk_Level"] = risk_band(proba)
    out["Risk_Sort"] = out["Risk_Level"].map({"Low": 1, "Medium": 2, "High": 3})
    out["Prediction_Outcome"] = np.select(
        [(out[TARGET] == 1) & (out["Predicted_Attrition_Flag"] == 1),
         (out[TARGET] == 0) & (out["Predicted_Attrition_Flag"] == 0),
         (out[TARGET] == 0) & (out["Predicted_Attrition_Flag"] == 1)],
        ["True Positive", "True Negative", "False Positive"], default="False Negative")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)
    return out
