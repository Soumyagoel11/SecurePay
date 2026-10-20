"""Wallet tests."""

from conftest import register, auth_headers


def _make_customer(client):
    register(client, "wal@test.com", "secret123", "customer", customer_age=30)
    return auth_headers(client, "wal@test.com", "secret123")


def test_add_money_success(client):
    headers = _make_customer(client)
    r = client.post("/api/wallet/add-money", json={"amount": 500}, headers=headers)
    assert r.status_code == 200
    assert r.get_json()["data"]["wallet"]["balance"] == 500.0


def test_add_money_invalid_amount(client):
    headers = _make_customer(client)
    r = client.post("/api/wallet/add-money", json={"amount": -50}, headers=headers)
    assert r.status_code == 400


def test_add_money_zero_amount(client):
    headers = _make_customer(client)
    r = client.post("/api/wallet/add-money", json={"amount": 0}, headers=headers)
    assert r.status_code == 400


def test_get_wallet_balance(client):
    headers = _make_customer(client)
    client.post("/api/wallet/add-money", json={"amount": 200}, headers=headers)
    r = client.get("/api/wallet", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["data"]["wallet"]["balance"] == 200.0


def test_insufficient_balance_payment(client):
    # Customer with 0 balance attempts a payment.
    register(client, "wal2@test.com", "secret123", "customer")
    headers = auth_headers(client, "wal2@test.com", "secret123")
    register(client, "merch@test.com", "secret123", "merchant", company_name="ShopX")
    mh = auth_headers(client, "merch@test.com", "secret123")
    mid = mh  # placeholder
    # get merchant id via merchant profile
    mp = client.get("/api/merchant/profile", headers=mh).get_json()["data"]["merchant"]["merchant_id"]
    r = client.post("/api/payments", json={"merchant_id": mp, "amount": 100}, headers=headers)
    assert r.status_code == 400
    assert "Insufficient" in r.get_json()["message"]
