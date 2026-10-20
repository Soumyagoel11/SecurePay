"""QR payment processing tests."""

from conftest import register, auth_headers


def _setup_actors(client):
    register(client, "qrcust@test.com", "secret123", "customer", customer_age=29)
    ch = auth_headers(client, "qrcust@test.com", "secret123")
    client.post("/api/wallet/add-money", json={"amount": 800}, headers=ch)

    register(client, "qrmerch@test.com", "secret123", "merchant", company_name="QR Cafe")
    mh = auth_headers(client, "qrmerch@test.com", "secret123")
    return ch, mh


def test_network_info(client):
    r = client.get("/api/qr-payments/network-info")
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert "lan_ip" in data
    assert data["frontend_port"] == 3000


def test_demo_customers_list(client):
    _setup_actors(client)
    r = client.get("/api/qr-payments/demo-customers")
    assert r.status_code == 200
    customers = r.get_json()["data"]["customers"]
    assert len(customers) >= 1
    assert "balance" in customers[0]
    assert "customer_id" in customers[0]


def test_create_and_fetch_qr_session(client):
    ch, mh = _setup_actors(client)
    r = client.post("/api/qr-payments/create", json={"amount": 45.5, "description": "Table 12"}, headers=mh)
    assert r.status_code == 201
    data = r.get_json()["data"]
    token = data["qr"]["token"]
    assert data["qr"]["amount"] == 45.5
    assert data["qr"]["status"] == "pending"
    assert "/pay/qr/" in data["pay_url"]
    assert data["qr_image"].startswith("data:image/png;base64,")

    # Fetch public session info
    r_pub = client.get(f"/api/qr-payments/{token}")
    assert r_pub.status_code == 200
    pub_data = r_pub.get_json()["data"]
    assert pub_data["merchant_name"] == "QR Cafe"
    assert pub_data["amount"] == 45.5
    assert pub_data["status"] == "pending"


def test_pay_qr_session_success_and_status_polling(client):
    ch, mh = _setup_actors(client)
    r = client.post("/api/qr-payments/create", json={"amount": 50.0, "description": "Order #101"}, headers=mh)
    token = r.get_json()["data"]["qr"]["token"]

    # Customer pays via the QR endpoint
    r_pay = client.post(f"/api/qr-payments/{token}/pay", json={}, headers=ch)
    assert r_pay.status_code == 200
    pay_data = r_pay.get_json()["data"]
    assert pay_data["status"] in ("success", "rejected")

    # If safe (normal test case), check that status polling on merchant side shows completed
    if pay_data["status"] == "success":
        r_poll = client.get(f"/api/qr-payments/{token}/status")
        assert r_poll.status_code == 200
        poll_data = r_poll.get_json()["data"]
        assert poll_data["status"] == "completed"
        assert poll_data["payment_id"] is not None
        assert poll_data["payment"]["amount"] == 50.0

        # Attempting to pay again returns conflict
        r_double = client.post(f"/api/qr-payments/{token}/pay", json={}, headers=ch)
        assert r_double.status_code == 409


def test_pay_qr_session_with_demo_customer_id(client):
    ch, mh = _setup_actors(client)
    # Get customer id
    cust_list = client.get("/api/qr-payments/demo-customers").get_json()["data"]["customers"]
    target_cust = cust_list[0]

    r_qr = client.post("/api/qr-payments/create", json={"amount": 15.0}, headers=mh)
    token = r_qr.get_json()["data"]["qr"]["token"]

    # Pay without headers, using demo_customer_id (simulating phone scanner)
    r_pay = client.post(f"/api/qr-payments/{token}/pay", json={"customer_id": target_cust["customer_id"]})
    assert r_pay.status_code == 200
    assert r_pay.get_json()["data"]["qr"]["status"] in ("completed", "rejected")


def test_customer_cannot_create_qr(client):
    ch, mh = _setup_actors(client)
    r = client.post("/api/qr-payments/create", json={"amount": 25.0}, headers=ch)
    assert r.status_code == 403
