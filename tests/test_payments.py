"""Payment processing tests."""

from conftest import register, auth_headers


def _setup_customer_merchant(client):
    register(client, "payc@test.com", "secret123", "customer", customer_age=30)
    ch = auth_headers(client, "payc@test.com", "secret123")
    client.post("/api/wallet/add-money", json={"amount": 1000}, headers=ch)

    register(client, "paym@test.com", "secret123", "merchant", company_name="ShopY")
    mh = auth_headers(client, "paym@test.com", "secret123")
    mid = client.get("/api/merchant/profile", headers=mh).get_json()["data"]["merchant"]["merchant_id"]
    return ch, mid


def test_successful_payment(client):
    ch, mid = _setup_customer_merchant(client)
    r = client.post("/api/payments", json={"merchant_id": mid, "amount": 200}, headers=ch)
    assert r.status_code == 200
    data = r.get_json()["data"]
    # Money moved only after a SAFE decision; either way a fraud record exists.
    assert data["fraud"]["fraud_flag"] in (True, False)
    if data["status"] == "success":
        w = client.get("/api/wallet", headers=ch).get_json()["data"]["wallet"]
        assert w["balance"] == 800.0


def test_negative_amount_payment(client):
    ch, mid = _setup_customer_merchant(client)
    r = client.post("/api/payments", json={"merchant_id": mid, "amount": -10}, headers=ch)
    assert r.status_code == 400


def test_invalid_merchant_payment(client):
    ch, _ = _setup_customer_merchant(client)
    r = client.post("/api/payments", json={"merchant_id": 999999, "amount": 10}, headers=ch)
    assert r.status_code == 400
    assert "Merchant" in r.get_json()["message"]


def test_payment_creates_fraud_record(client):
    ch, mid = _setup_customer_merchant(client)
    r = client.post("/api/payments", json={"merchant_id": mid, "amount": 50}, headers=ch)
    pid = r.get_json()["data"]["payment"]["payment_id"]
    detail = client.get(f"/api/payments/{pid}", headers=ch).get_json()["data"]
    assert detail["fraud"] is not None
    assert "risk_score" in detail["fraud"]


def test_customer_cannot_view_other_payments(client):
    ch, mid = _setup_customer_merchant(client)
    r = client.post("/api/payments", json={"merchant_id": mid, "amount": 30}, headers=ch)
    pid = r.get_json()["data"]["payment"]["payment_id"]

    # Another customer tries to view it.
    register(client, "otherc@test.com", "secret123", "customer")
    oh = auth_headers(client, "otherc@test.com", "secret123")
    r2 = client.get(f"/api/payments/{pid}", headers=oh)
    assert r2.status_code == 403
