"""=============================================================================
SecurePay Software Testing Suite: Testing Web-Based Systems & Regression Testing
=============================================================================
Topic: Testing Web-Based System (with Object-Oriented Test Design & Regression Guards)

This module implements a dedicated academic test suite covering:
  1. Client-Server API Response Specification (Contract Testing)
  2. Web Session Authentication & Authorization (JWT Security & 401/403)
  3. Role-Based Access Control (RBAC Matrix)
  4. Web Input Boundary & Payload Validation (Robustness Testing)
  5. Cross-Origin Resource Sharing (CORS Headers)
  6. Web Session Lifecycle (QR Dynamic Payment Session State Machine)
  7. Regression Testing Guards (Defect Re-occurrence Prevention)
"""

import pytest
from conftest import register, auth_headers


class TestWebBasedSystem:
    """Object-Oriented Test Suite for Web-Based Payment Architecture."""

    @pytest.fixture(autouse=True)
    def setup_system(self, client):
        """Fixture providing isolated setup state for each test method."""
        self.client = client

        # Provision a sample Customer
        register(self.client, "web_customer@securepay.test", "pass12345", "customer", customer_age=29)
        self.cust_headers = auth_headers(self.client, "web_customer@securepay.test", "pass12345")
        self.client.post("/api/wallet/add-money", json={"amount": 500}, headers=self.cust_headers)

        # Provision a sample Merchant
        register(self.client, "web_merchant@securepay.test", "pass12345", "merchant", company_name="Campus Tech Store")
        self.merch_headers = auth_headers(self.client, "web_merchant@securepay.test", "pass12345")
        merch_res = self.client.get("/api/merchant/profile", headers=self.merch_headers).get_json()
        self.merchant_id = merch_res["data"]["merchant"]["merchant_id"]

        # Provision a sample Admin
        register(self.client, "web_admin@securepay.test", "admin12345", "admin")
        self.admin_headers = auth_headers(self.client, "web_admin@securepay.test", "admin12345")

    # -------------------------------------------------------------------------
    # 1. Client-Server Contract Testing: Uniform Response Envelope
    # -------------------------------------------------------------------------
    def test_web_api_envelope_contract(self):
        """Verifies that web endpoints adhere strictly to the REST JSON contract."""
        response = self.client.get("/api/wallet", headers=self.cust_headers)
        assert response.status_code == 200
        payload = response.get_json()

        # Contract assertion: All responses must follow {success, message, data}
        assert "success" in payload and isinstance(payload["success"], bool)
        assert "message" in payload and isinstance(payload["message"], str)
        assert "data" in payload and isinstance(payload["data"], dict)
        assert payload["success"] is True

    # -------------------------------------------------------------------------
    # 2. Web Session Authentication & Authorization (JWT Security)
    # -------------------------------------------------------------------------
    def test_web_authentication_unauthorized_rejection(self):
        """Verifies that unauthenticated web requests are rejected with HTTP 401."""
        # Missing Authorization header
        response = self.client.get("/api/wallet")
        assert response.status_code == 401
        assert response.get_json()["success"] is False

        # Malformed Authorization header
        bad_response = self.client.get("/api/wallet", headers={"Authorization": "Bearer invalid_token_xyz"})
        assert bad_response.status_code in (401, 422)
        assert bad_response.get_json()["success"] is False

    # -------------------------------------------------------------------------
    # 3. Role-Based Access Control (RBAC) Matrix
    # -------------------------------------------------------------------------
    def test_role_based_access_control_matrix(self):
        """Verifies that customers cannot access merchant or admin protected routes."""
        # Customer attempting to access Admin Dashboard -> HTTP 403 Forbidden
        admin_route_res = self.client.get("/api/admin/dashboard", headers=self.cust_headers)
        assert admin_route_res.status_code == 403
        assert admin_route_res.get_json()["success"] is False

        # Customer attempting to access Merchant Dashboard -> HTTP 403 Forbidden
        merchant_route_res = self.client.get("/api/merchant/dashboard", headers=self.cust_headers)
        assert merchant_route_res.status_code == 403
        assert merchant_route_res.get_json()["success"] is False

        # Admin accessing Admin Dashboard -> HTTP 200 OK
        admin_ok_res = self.client.get("/api/admin/dashboard", headers=self.admin_headers)
        assert admin_ok_res.status_code == 200
        assert admin_ok_res.get_json()["success"] is True

    # -------------------------------------------------------------------------
    # 4. Web Input Boundary & Robustness Testing
    # -------------------------------------------------------------------------
    def test_web_input_validation_and_robustness(self):
        """Verifies robust rejection of boundary anomalies, invalid types, and malformed inputs."""
        # Case A: Negative transaction amount
        res_neg = self.client.post(
            "/api/payments",
            json={"merchant_id": self.merchant_id, "amount": -75.0},
            headers=self.cust_headers
        )
        assert res_neg.status_code == 400
        assert res_neg.get_json()["success"] is False

        # Case B: Non-existent merchant ID
        res_bad_id = self.client.post(
            "/api/payments",
            json={"merchant_id": 9999999, "amount": 50.0},
            headers=self.cust_headers
        )
        assert res_bad_id.status_code == 400
        assert res_bad_id.get_json()["success"] is False

        # Case C: Zero amount top-up boundary
        res_zero = self.client.post(
            "/api/wallet/add-money",
            json={"amount": 0},
            headers=self.cust_headers
        )
        assert res_zero.status_code == 400
        assert res_zero.get_json()["success"] is False

    # -------------------------------------------------------------------------
    # 5. Cross-Origin Resource Sharing (CORS) Web Headers
    # -------------------------------------------------------------------------
    def test_cors_preflight_and_headers(self):
        """Verifies that CORS pre-flight OPTIONS request is handled correctly for web clients."""
        res = self.client.options(
            "/api/payments",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
        )
        assert res.status_code in (200, 204)
        assert "Access-Control-Allow-Origin" in res.headers

    # -------------------------------------------------------------------------
    # 6. Web Session Lifecycle: QR Dynamic Checkout State Machine
    # -------------------------------------------------------------------------
    def test_web_session_qr_checkout_lifecycle(self):
        """Verifies end-to-end web session transition: creation -> pending -> completed."""
        # Step A: Merchant creates QR payment session
        res_create = self.client.post(
            "/api/qr-payments/create",
            json={"amount": 45.0, "description": "Lab Manual & Stationery"},
            headers=self.merch_headers
        )
        assert res_create.status_code == 201
        session_data = res_create.get_json()["data"]
        token = session_data["qr"]["token"]
        assert session_data["qr"]["status"] == "pending"

        # Step B: Web polling check returns 'pending'
        res_poll = self.client.get(f"/api/qr-payments/{token}/status")
        assert res_poll.status_code == 200
        assert res_poll.get_json()["data"]["status"] == "pending"

        # Step C: Customer completes payment
        res_pay = self.client.post(
            f"/api/qr-payments/{token}/pay",
            json={},
            headers=self.cust_headers
        )
        assert res_pay.status_code == 200
        assert res_pay.get_json()["data"]["status"] == "success"

        # Step D: Web polling check reflects 'completed' state
        res_poll_after = self.client.get(f"/api/qr-payments/{token}/status")
        assert res_poll_after.status_code == 200
        assert res_poll_after.get_json()["data"]["status"] == "completed"

    # -------------------------------------------------------------------------
    # 7. Regression Testing Guards (Defect Prevention)
    # -------------------------------------------------------------------------
    def test_regression_duplicate_refund_prevention(self):
        """Regression Guard: Ensure a transaction cannot have duplicate refund requests."""
        # 1. Execute payment
        pay_res = self.client.post(
            "/api/payments",
            json={"merchant_id": self.merchant_id, "amount": 60.0},
            headers=self.cust_headers
        )
        assert pay_res.status_code == 200
        payment_id = pay_res.get_json()["data"]["payment"]["payment_id"]

        # 2. First refund request -> Accepted (HTTP 201)
        r1 = self.client.post(
            "/api/refunds",
            json={"payment_id": payment_id, "reason": "Defective item returned"},
            headers=self.cust_headers
        )
        assert r1.status_code == 201
        assert r1.get_json()["success"] is True

        # 3. Second refund request for same payment -> Must be rejected (Regression guard)
        r2 = self.client.post(
            "/api/refunds",
            json={"payment_id": payment_id, "reason": "Attempting second refund"},
            headers=self.cust_headers
        )
        assert r2.status_code in (400, 409)
        assert r2.get_json()["success"] is False

    def test_regression_ml_risk_score_boundary_integrity(self):
        """Regression Guard: Ensure ML risk score output is strictly bounded between 0.0 and 1.0."""
        res = self.client.post(
            "/api/fraud/predict",
            json={
                "customer_id": 1,
                "merchant_id": self.merchant_id,
                "amount": 120.0,
                "location_change": False,
                "device_change": False
            },
            headers=self.cust_headers
        )
        assert res.status_code == 200
        fraud_data = res.get_json()["data"]
        risk_score = fraud_data["risk_score"]
        # Mathematical invariant: 0.0 <= risk_score <= 1.0
        assert 0.0 <= risk_score <= 1.0
        assert fraud_data["prediction"] in ("Safe", "Suspicious")
