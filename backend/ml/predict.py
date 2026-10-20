"""
Fraud prediction module for SecurePay.

Loads the serialized model artifact produced by train_model.py and exposes a
clean API to score a transaction.

Public API:
    load_model()                 -> loads artifact (cached)
    build_features(context)      -> numpy vector from transaction context
    predict(context)             -> {"prediction", "risk_score", "fraud_flag",
                                      "model_version", "model_name"}
"""

import os
import joblib
import numpy as np

from ml.features import FEATURES

MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

# Configurable business threshold. risk_score >= THRESHOLD => Suspicious.
DEFAULT_THRESHOLD = 0.5

_ARTIFACT = None


def load_model():
    """Load and cache the trained model artifact."""
    global _ARTIFACT
    if _ARTIFACT is not None:
        return _ARTIFACT
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "Model not found. Run `python -m ml.train_model` from the backend "
            "directory to train and serialize the fraud model."
        )
    _ARTIFACT = joblib.load(MODEL_PATH)
    if _ARTIFACT.get("uses_scaler") and os.path.exists(SCALER_PATH):
        _ARTIFACT["scaler"] = joblib.load(SCALER_PATH)
    return _ARTIFACT


def build_features(context: dict):
    """Construct the 12-feature vector expected by the model.

    `context` keys (all numeric):
        transaction_amount, transaction_hour, transaction_frequency,
        customer_age, account_age, previous_transaction_count,
        average_transaction_amount, merchant_risk, failed_transaction_count,
        location_change, device_change, previous_fraud_count
    Missing values are defaulted to 0 (safe, neutral) so the pipeline never
    crashes on partial data.
    """
    artifact = load_model()
    feature_names = FEATURES
    row = []
    for name in feature_names:
        val = context.get(name, 0)
        try:
            val = float(val)
        except (TypeError, ValueError):
            val = 0.0
        row.append(val)
    return [row]


def predict(context: dict, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Return a fraud decision for a single transaction context."""
    artifact = load_model()
    features = build_features(context)

    model = artifact["model"]
    if artifact.get("uses_scaler") and artifact.get("scaler") is not None:
        import numpy as np
        X = artifact["scaler"].transform(np.array(features))
    else:
        X = features

    # probability of the positive (fraud) class
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        risk_score = float(proba[1]) if proba.shape[0] > 1 else float(proba[0])
    else:
        risk_score = float(model.decision_function(X)[0])

    fraud_flag = risk_score >= threshold
    prediction = "Suspicious" if fraud_flag else "Safe"

    return {
        "prediction": prediction,
        "risk_score": round(risk_score, 4),
        "fraud_flag": bool(fraud_flag),
        "threshold": threshold,
        "model_version": artifact.get("model_version"),
        "model_name": artifact.get("model_name"),
    }


if __name__ == "__main__":
    load_model()
    sample_legit = {
        "transaction_amount": 50.0,
        "transaction_hour": 14,
        "transaction_frequency": 1,
        "customer_age": 34,
        "account_age": 400,
        "previous_transaction_count": 20,
        "average_transaction_amount": 60.0,
        "merchant_risk": 0.1,
        "failed_transaction_count": 0,
        "location_change": 0,
        "device_change": 0,
        "previous_fraud_count": 0,
    }
    sample_fraud = {
        "transaction_amount": 9000.0,
        "transaction_hour": 3,
        "transaction_frequency": 12,
        "customer_age": 23,
        "account_age": 5,
        "previous_transaction_count": 1,
        "average_transaction_amount": 50.0,
        "merchant_risk": 0.9,
        "failed_transaction_count": 4,
        "location_change": 1,
        "device_change": 1,
        "previous_fraud_count": 2,
    }
    print("Legit sample:", predict(sample_legit))
    print("Fraud sample:", predict(sample_fraud))
