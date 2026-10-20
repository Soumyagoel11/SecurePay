"""
Train and evaluate the SecurePay fraud detection model.

Two datasets are involved, following the recommended "real data for evaluation,
application data for the workflow" approach:

1. PRODUCTION MODEL  -> trained on the documented synthetic generator
   (ml.datasets.generate_synthetic). Its 12 features are engineered with the
   SAME semantics as the features we build at inference time from SecurePay's
   database context, so the model is well-calibrated for live payments.

2. REAL-DATA BENCHMARK -> if the real BankSim CSV (bs140513_032310.csv) is
   present in ml/dataset/, we ALSO train/evaluate on it and report metrics.
   BankSim's strongest fraud signal is the transaction `category`, which is not
   part of SecurePay's 12-feature model, so it is used here for transparent
   benchmarking rather than as the production model.

Model selection uses the F1-score (appropriate for imbalanced fraud data), not
raw accuracy.

Why precision and recall both matter for fraud detection:
    - Precision: of the transactions we flag as fraud, how many truly are.
      Low precision => legitimate customers get blocked (bad UX, lost revenue).
    - Recall: of all actual frauds, how many we catch.
      Low recall => fraudsters slip through (direct financial loss).
    Accuracy is misleading on imbalanced data, so we rely on F1 for selection.
"""

import os
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
)

from ml.features import FEATURES, TARGET
from ml.datasets import generate_synthetic, load_banksim, BANKSIM_PATH

MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.txt")
BENCHMARK_PATH = os.path.join(MODEL_DIR, "banksim_benchmark.txt")
MODEL_VERSION = "securepay-fraud-v1"


def evaluate(name, y_true, y_pred):
    return {
        "model": name,
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def _train_and_select(X, y, max_rows=150000):
    if len(X) > max_rows:
        fraud = y == 1
        keep = np.where(fraud)[0]
        legit_sample = np.random.RandomState(42).choice(
            np.where(~fraud)[0], size=min(max_rows - len(keep), int((~fraud).sum())), replace=False
        )
        idx = np.concatenate([keep, legit_sample])
        X, y = X[idx], y[idx]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    lr.fit(X_train_s, y_train)
    lr_pred = lr.predict(X_test_s)
    lr_metrics = evaluate("LogisticRegression", y_test, lr_pred)

    rf = RandomForestClassifier(
        n_estimators=120, max_depth=12, class_weight="balanced",
        random_state=42, n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_metrics = evaluate("RandomForest", y_test, rf_pred)

    best = lr_metrics if lr_metrics["f1"] >= rf_metrics["f1"] else rf_metrics
    if best["model"] == "LogisticRegression":
        chosen, uses_scaler = lr, True
        joblib.dump(scaler, SCALER_PATH)
    else:
        chosen, uses_scaler = rf, False
    return chosen, uses_scaler, best, lr_metrics, rf_metrics


def main():
    # ---- 1. Production model (synthetic, feature-aligned) ----
    df = generate_synthetic()
    X = df[FEATURES].values
    y = df[TARGET].values
    chosen, uses_scaler, best, lr_m, rf_m = _train_and_select(X, y)

    artifact = {
        "model": chosen,
        "features": FEATURES,
        "model_name": best["model"],
        "model_version": MODEL_VERSION,
        "uses_scaler": uses_scaler,
        "metrics": {k: best[k] for k in ("accuracy", "precision", "recall", "f1")},
        "threshold": 0.5,
    }
    joblib.dump(artifact, MODEL_PATH)

    lines = []
    lines.append("=== PRODUCTION MODEL (documented synthetic dataset) ===")
    lines.append(f"Selected: {best['model']}  F1={best['f1']:.4f}")
    lines.append(f"LogisticRegression: {lr_m}")
    lines.append(f"RandomForest: {rf_m}")
    print("\n".join(lines))

    # ---- 2. Real-data benchmark (BankSim) ----
    if os.path.exists(BANKSIM_PATH):
        print("\nBenchmarking on REAL BankSim dataset...")
        bdf = load_banksim()
        bx = bdf[FEATURES].values
        by = bdf[TARGET].values
        bchosen, bscaler, bbest, blr, brf = _train_and_select(bx, by)
        b_lines = ["", "=== REAL-DATA BENCHMARK (BankSim) ===",
                   f"Selected: {bbest['model']}  F1={bbest['f1']:.4f}",
                   f"LogisticRegression: {blr}", f"RandomForest: {brf}"]
        lines.extend(b_lines)
        print("\n".join(b_lines))
        with open(BENCHMARK_PATH, "w") as f:
            f.write("\n".join(b_lines))

    with open(METRICS_PATH, "w") as f:
        f.write("\n".join(lines))

    print(f"\nProduction model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
