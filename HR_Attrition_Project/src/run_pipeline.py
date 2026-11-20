"""
run_pipeline.py  -  one command to rebuild every artefact in the project.

    python src/run_pipeline.py

Steps: (1) generate raw data if missing  (2) clean  (3) EDA charts  (4) train / evaluate models
       (5) export predictions + model for Power BI.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import joblib
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data_cleaning as dc
import eda
import generate_dataset as gd
import model_training as mt

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "images"


def main():
    print("== 1/5 Raw data ==")
    if not dc.RAW_PATH.exists():
        gd.build_raw_dataset().to_csv(dc.RAW_PATH, index=False)
    print("== 2/5 Cleaning ==")
    df = dc.clean_pipeline()
    print("== 3/5 EDA charts ==")
    eda.generate_all(df, IMG / "eda")

    print("== 4/5 Modelling ==")
    X, y, num_cols, cat_cols = mt.prepare_xy(df)
    X_train, X_test, y_train, y_test = mt.split_data(X, y)
    models = mt.build_models(num_cols, cat_cols)
    fitted, cv_scores, best_params = mt.tune_models(models, X_train, y_train)
    metrics = mt.evaluate(fitted, X_test, y_test)
    metrics["CV F1 (train)"] = pd.Series(cv_scores).round(3)
    print(metrics, "\n")

    best_name = max(cv_scores, key=cv_scores.get)          # selected on CV only -> no test leakage
    best = fitted[best_name]
    thr = mt.best_threshold(best, X_train, y_train)
    tuned = mt.evaluate({best_name: best}, X_test, y_test, threshold=thr)
    print(f"Best model: {best_name}  | tuned threshold = {thr:.2f}\n{tuned}\n")

    for fn, args in [(mt.plot_confusion_matrices, (fitted, X_test, y_test)), (mt.plot_roc, (fitted, X_test, y_test)),
                     (mt.plot_model_comparison, (metrics.drop(columns="CV F1 (train)"),)),
                     (mt.plot_feature_importance, (fitted["Random Forest"], "Random Forest"))]:
        plt.close(fn(*args, IMG / "model"))

    print("== 5/5 Export ==")
    proba = mt.out_of_fold_predictions(best, X, y, thr)
    preds = mt.export_predictions(df, proba, thr, ROOT / "data" / "processed" / "attrition_predictions.csv")
    joblib.dump({"model": best, "threshold": thr, "features": list(X.columns), "name": best_name},
                ROOT / "models" / "attrition_model.joblib")
    metrics.to_csv(ROOT / "reports" / "model_metrics.csv")
    summary = {"best_model": best_name, "threshold": thr, "best_params": {k: str(v) for k, v in best_params.items()},
               "test_metrics_at_0.5": metrics.to_dict("index"), "test_metrics_tuned": tuned.to_dict("index")[best_name],
               "oof_confusion": preds["Prediction_Outcome"].value_counts().to_dict()}
    (ROOT / "reports" / "model_summary.json").write_text(json.dumps(summary, indent=2))
    print(preds["Prediction_Outcome"].value_counts(), "\n", preds["Risk_Level"].value_counts())
    print("Top drivers (Random Forest):\n", mt.feature_importance(fitted["Random Forest"], 10))


if __name__ == "__main__":
    main()
