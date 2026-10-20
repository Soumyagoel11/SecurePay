"""Refund tests."""

from conftest import register, auth_headers


def _successful_payment(client):
    register(client, "refc@test.com", "secret123", "customer", customer_age=30)
    ch = auth_headers(client, "refc@test.com", "secret123")
    client.post("/api/wallet/add-money", json={"amount": 1000}, headers=ch)

    register(client, "refm@test.com", "secret123", "merchant", company_name="ShopR")
    mh = auth_headers(client, "refm@test.com", "secret123")
    mid = client.get("/api/merchant/profile", headers=mh).get_json()["data"]["merchant"]["merchant_id"]

    r = client.post("/api/payments", json={"merchant_id": mid, "amount": 200}, headers=ch)
    data = r.get_json()["data"]
    # If it was flagged suspicious, top up and retry until we get a successful one.
    attempts = 0
    while data["status"] != "success" and attempts < 5:
        client.post("/api/wallet/add-money", json={"amount": 1000}, headers=ch)
        r = client.post("/api/payments", json={"merchant_id": mid, "amount": 200}, headers=ch)
        data = r.get_json()["data"]
        attempts += 1
    assert data["status"] == "success", "Expected a successful payment for refund test"
    return ch, data["payment"]["payment_id"], data["payment"]["amount"]


def _admin(client):
    register(client, "admin@test.com", "secret123", "admin", department="Risk")
    return auth_headers(client, "admin@test.com", "secret123")


def test_valid_refund_flow(client):
    ch, pid, amount = _successful_payment(client)
    r = client.post("/api/refunds", json={"payment_id": pid, "reason": "Changed mind"},
                   headers=ch)
    assert r.status_code == 201
    refund_id = r.get_json()["data"]["refund"]["refund_id"]

    ah = _admin(client)
    r2 = client.put(f"/api/refunds/{refund_id}/approve", headers=ah)
    assert r2.status_code == 200
    assert r2.get_json()["data"]["refund"]["status"] == "approved"


def test_admin_rejection(client):
    ch, pid, amount = _successful_payment(client)
    r = client.post("/api/refunds", json={"payment_id": pid}, headers=ch)
    refund_id = r.get_json()["data"]["refund"]["refund_id"]
    ah = _admin(client)
    r2 = client.put(f"/api/refunds/{refund_id}/reject", headers=ah)
    assert r2.status_code == 200
    assert r2.get_json()["data"]["refund"]["status"] == "rejected"


def test_duplicate_refund_rejected(client):
    ch, pid, amount = _successful_payment(client)
    r1 = client.post("/api/refunds", json={"payment_id": pid}, headers=ch)
    assert r1.status_code == 201
    r2 = client.post("/api/refunds", json={"payment_id": pid}, headers=ch)
    assert r2.status_code == 409


def test_refund_nonexistent_payment(client):
    register(client, "refc2@test.com", "secret123", "customer", customer_age=30)
    ch = auth_headers(client, "refc2@test.com", "secret123")
    r = client.post("/api/refunds", json={"payment_id": 999999}, headers=ch)
    assert r.status_code == 404


def test_refund_requires_customer_role(client):
    # A merchant trying to request a refund on a payment they receive.
    register(client, "refm2@test.com", "secret123", "merchant", company_name="ShopR2")
    mh = auth_headers(client, "refm2@test.com", "secret123")
    r = client.post("/api/refunds", json={"payment_id": 1}, headers=mh)
    assert r.status_code == 403
