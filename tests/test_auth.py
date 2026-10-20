"""Authentication tests."""

from conftest import register, login, auth_headers


def test_valid_registration_and_login(client):
    r = register(client, "cust1@test.com", "secret123", "customer",
                 phone="123", customer_age=30)
    assert r.status_code == 201
    assert r.get_json()["success"] is True
    assert "access_token" in r.get_json()["data"]

    r = login(client, "cust1@test.com", "secret123")
    assert r.status_code == 200
    assert r.get_json()["success"] is True


def test_invalid_login(client):
    register(client, "cust2@test.com", "secret123", "customer")
    r = login(client, "cust2@test.com", "wrongpassword")
    assert r.status_code == 401
    assert r.get_json()["success"] is False


def test_duplicate_registration(client):
    register(client, "dup@test.com", "secret123", "customer")
    r = register(client, "dup@test.com", "secret123", "customer")
    assert r.status_code == 409


def test_weak_password_rejected(client):
    r = register(client, "weak@test.com", "123", "customer")
    assert r.status_code == 400


def test_unauthorized_access_without_token(client):
    r = client.get("/api/wallet")
    assert r.status_code == 401


def test_unauthorized_access_with_bad_token(client):
    r = client.get("/api/wallet", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code in (401, 422)


def test_role_protected_route(client):
    # Register a customer and try to access admin-only route.
    register(client, "cust3@test.com", "secret123", "customer")
    headers = auth_headers(client, "cust3@test.com", "secret123")
    r = client.get("/api/admin/dashboard", headers=headers)
    assert r.status_code == 403


def test_me_endpoint(client):
    register(client, "cust4@test.com", "secret123", "customer")
    headers = auth_headers(client, "cust4@test.com", "secret123")
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["data"]["user"]["role"] == "customer"
