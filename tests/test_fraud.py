"""Fraud detection tests (uses the real trained model)."""

from ml.predict import predict, load_model


def test_model_loading():
    artifact = load_model()
    assert artifact is not None
    assert "model" in artifact


def test_legitimate_transaction():
    ctx = {
        "transaction_amount": 40.0, "transaction_hour": 14,
        "transaction_frequency": 1, "customer_age": 35, "account_age": 400,
        "previous_transaction_count": 20, "average_transaction_amount": 50.0,
        "merchant_risk": 0.05, "failed_transaction_count": 0,
        "location_change": 0, "device_change": 0, "previous_fraud_count": 0,
    }
    res = predict(ctx)
    assert "risk_score" in res
    assert res["prediction"] in ("Safe", "Suspicious")
    assert 0.0 <= res["risk_score"] <= 1.0


def test_suspicious_transaction():
    ctx = {
        "transaction_amount": 9500.0, "transaction_hour": 3,
        "transaction_frequency": 12, "customer_age": 22, "account_age": 3,
        "previous_transaction_count": 1, "average_transaction_amount": 40.0,
        "merchant_risk": 0.95, "failed_transaction_count": 5,
        "location_change": 1, "device_change": 1, "previous_fraud_count": 3,
    }
    res = predict(ctx)
    assert res["fraud_flag"] is True
    assert res["risk_score"] >= 0.5


def test_risk_score_generation():
    ctx = {k: 0 for k in [
        "transaction_amount", "transaction_hour", "transaction_frequency",
        "customer_age", "account_age", "previous_transaction_count",
        "average_transaction_amount", "merchant_risk", "failed_transaction_count",
        "location_change", "device_change", "previous_fraud_count"]}
    ctx["transaction_amount"] = 100.0
    res = predict(ctx)
    assert isinstance(res["risk_score"], float)


def test_fraud_predict_api(client):
    from conftest import register, auth_headers
    register(client, "fraudc@test.com", "secret123", "customer", customer_age=30)
    headers = auth_headers(client, "fraudc@test.com", "secret123")
    legit = {
        "transaction_amount": 40.0, "transaction_hour": 14,
        "transaction_frequency": 1, "customer_age": 35, "account_age": 400,
        "previous_transaction_count": 20, "average_transaction_amount": 50.0,
        "merchant_risk": 0.05, "failed_transaction_count": 0,
        "location_change": 0, "device_change": 0, "previous_fraud_count": 0,
    }
    r = client.post("/api/fraud/predict", json={"features": legit}, headers=headers)
    assert r.status_code == 200
    assert "risk_score" in r.get_json()["data"]
