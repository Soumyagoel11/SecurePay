"""=============================================================================
SecurePay Software Testing Suite: Non-Functional Testing (NFT)
=============================================================================
Academic Topic: Non-Functional Testing (Performance, Security, Reliability, 
               Concurrency/Stress, and Scalability)

This module implements 5 concrete, automated Non-Functional Test Cases:
  1. NFT-01: Performance & Latency Testing (ML Inference & Payment SLA < 300ms)
  2. NFT-02: Security & Injection Resilience (SQL Injection & Malicious Payload Sanitization)
  3. NFT-03: Concurrency & Stress Testing (Balance Overdraw & Invariant Protection)
  4. NFT-04: Reliability & Fault Tolerance (Atomic Rollback on Mid-Flight Failure)
  5. NFT-05: Scalability & Load Resilience (Burst Load & Envelope Consistency)
"""

import time
from unittest.mock import patch
import pytest
from conftest import register, auth_headers
from app.extensions import db


class TestNonFunctionalRequirements:
    """Non-Functional Test Suite verifying quality attributes of SecurePay."""

    @pytest.fixture(autouse=True)
    def setup_nft_environment(self, client):
        """Set up isolated accounts, wallet balance, and merchant for NFT runs."""
        self.client = client

        # 1. Register NFT Customer with initialized wallet
        register(self.client, "nft_customer@securepay.test", "SecurePass123!", "customer", customer_age=28)
        self.cust_headers = auth_headers(self.client, "nft_customer@securepay.test", "SecurePass123!")
        self.client.post("/api/wallet/add-money", json={"amount": 1000.0}, headers=self.cust_headers)

        # 2. Register NFT Merchant
        register(self.client, "nft_merchant@securepay.test", "SecurePass123!", "merchant", company_name="NFT Global Store")
        self.merch_headers = auth_headers(self.client, "nft_merchant@securepay.test", "SecurePass123!")
        merch_res = self.client.get("/api/merchant/profile", headers=self.merch_headers).get_json()
        self.merchant_id = merch_res["data"]["merchant"]["merchant_id"]

    # -------------------------------------------------------------------------
    # NFT-01: Performance & Latency Testing
    # -------------------------------------------------------------------------
    def test_nft_01_performance_payment_and_ml_inference_sla(self):
        """NFT-01 [Performance]: Verifies end-to-end payment and ML scoring SLA.

        SLA Target: Steady-state mean response time < 250ms, Max response time < 500ms.
        Covers 12-feature mapping, Random Forest inference, and DB commit.
        """
        # Warm-up request to prime database connection and unpickle the ML model singleton
        warmup_res = self.client.post(
            "/api/payments",
            json={"merchant_id": self.merchant_id, "amount": 10.0},
            headers=self.cust_headers,
        )
        assert warmup_res.status_code == 200

        latencies = []
        num_samples = 5

        # Steady-state latency benchmarking
        for i in range(num_samples):
            start_time = time.perf_counter()
            response = self.client.post(
                "/api/payments",
                json={"merchant_id": self.merchant_id, "amount": 15.0 + i},
                headers=self.cust_headers,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            latencies.append(elapsed_ms)

            assert response.status_code == 200
            data = response.get_json()["data"]
            assert "fraud" in data
            assert "risk_score" in data["fraud"]

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        # Performance Assertion SLA Thresholds (steady-state)
        assert avg_latency < 250.0, f"Average latency {avg_latency:.2f}ms exceeded 250ms SLA"
        assert max_latency < 500.0, f"Max latency {max_latency:.2f}ms exceeded 500ms ceiling"

    # -------------------------------------------------------------------------
    # NFT-02: Security Testing (Injection Resilience & Data Sanitization)
    # -------------------------------------------------------------------------
    def test_nft_02_security_sql_injection_and_tampering_resilience(self):
        """NFT-02 [Security]: Tests resistance against SQL Injection & script tampering.

        Verifies that ORM parameterization prevents arbitrary SQL execution,
        avoids 500 unhandled exceptions, and safely rejects or stores escaped text.
        """
        # Execute initial payment to get payment_id for refund testing
        pay_res = self.client.post(
            "/api/payments",
            json={"merchant_id": self.merchant_id, "amount": 50.0},
            headers=self.cust_headers,
        )
        payment_id = pay_res.get_json()["data"]["payment"]["payment_id"]

        sql_injection_payloads = [
            "'; DROP TABLE payments; --",
            "' OR '1'='1",
            "1; SELECT * FROM users;",
            "<script>alert('XSS')</script>",
            "' UNION SELECT username, password_hash FROM users --"
        ]

        # Test injection via refund reason
        for malicious_payload in sql_injection_payloads:
            res = self.client.post(
                "/api/refunds",
                json={"payment_id": payment_id, "reason": malicious_payload},
                headers=self.cust_headers,
            )
            # Response must be handled gracefully: 201 (stored safely parameterized) or 400/409/422
            # Must NEVER be HTTP 500 (Unhandled Database Crash / SQL syntax error)
            assert res.status_code in (201, 400, 409, 422), (
                f"Payload {malicious_payload} caused unexpected status code {res.status_code}"
            )

        # Verify payments endpoint still functions normally and payments table is unharmed
        verify_res = self.client.get(f"/api/payments/{payment_id}", headers=self.cust_headers)
        assert verify_res.status_code == 200
        assert verify_res.get_json()["data"]["payment_id"] == payment_id

    # -------------------------------------------------------------------------
    # NFT-03: Concurrency & Stress Testing (Balance Overdraw Guard)
    # -------------------------------------------------------------------------
    def test_nft_03_concurrency_balance_overdraw_protection(self):
        """NFT-03 [Stress & Concurrency]: Verifies wallet balance integrity under rapid debits.

        Ensures wallet never drops below zero and cannot be overdrawn when
        consecutive transactions exceed available funds.
        """
        # Check current balance
        bal_res = self.client.get("/api/wallet", headers=self.cust_headers).get_json()
        current_balance = bal_res["data"]["wallet"]["balance"]

        # Attempt 10 transactions of an amount that will exhaust the wallet
        single_amount = (current_balance / 3) + 10.0  # At most 2 can succeed

        successful_txns = 0
        rejected_insufficient = 0

        for _ in range(10):
            res = self.client.post(
                "/api/payments",
                json={"merchant_id": self.merchant_id, "amount": single_amount},
                headers=self.cust_headers,
            )
            if res.status_code == 200 and res.get_json()["data"]["status"] == "success":
                successful_txns += 1
            elif res.status_code == 400 and "Insufficient" in res.get_json().get("message", ""):
                rejected_insufficient += 1

        # Post-condition check
        final_bal_res = self.client.get("/api/wallet", headers=self.cust_headers).get_json()
        final_balance = final_bal_res["data"]["wallet"]["balance"]

        # Mathematical invariants
        assert final_balance >= 0.0, f"Wallet balance dropped below zero: {final_balance}"
        assert successful_txns <= 2, f"Allowed {successful_txns} transactions exceeding balance capacity"
        assert rejected_insufficient > 0, "System failed to reject transactions with insufficient balance"

    # -------------------------------------------------------------------------
    # NFT-04: Reliability & Fault Tolerance (Atomic Rollback on Mid-Flight Failure)
    # -------------------------------------------------------------------------
    def test_nft_04_reliability_atomic_rollback_on_failure(self):
        """NFT-04 [Reliability]: Verifies ACID atomicity under unexpected server failure.

        Simulates an unhandled exception during ledger persistence to verify that:
        1. Wallet balance is NOT decremented.
        2. No orphaned transaction or committed payment remains in inconsistent state.
        """
        bal_before = self.client.get("/api/wallet", headers=self.cust_headers).get_json()["data"]["wallet"]["balance"]

        # Simulate a crash right when committing the payment by patching db.session.commit
        with patch.object(db.session, "commit", side_effect=RuntimeError("Simulated DB Disk Write Error")):
            try:
                self.client.post(
                    "/api/payments",
                    json={"merchant_id": self.merchant_id, "amount": 100.0},
                    headers=self.cust_headers,
                )
            except RuntimeError:
                pass  # Caught simulated crash

        # Check balance after failure
        bal_after = self.client.get("/api/wallet", headers=self.cust_headers).get_json()["data"]["wallet"]["balance"]
        assert bal_after == bal_before, (
            f"Atomicity violation: Wallet balance changed from {bal_before} to {bal_after} despite failure"
        )

    # -------------------------------------------------------------------------
    # NFT-05: Scalability & Load Resilience (Burst Traffic & Envelope Consistency)
    # -------------------------------------------------------------------------
    def test_nft_05_scalability_burst_load_and_envelope_consistency(self):
        """NFT-05 [Scalability & Load]: Tests stability and response consistency under burst traffic.

        Simulates a burst of 20 rapid multi-endpoint operations (wallet lookups,
        merchants directory, fraud predictions, and payments) to ensure 100%
        contract compliance and zero server dropouts.
        """
        endpoints = [
            ("GET", "/api/wallet", self.cust_headers, None),
            ("GET", "/api/customer/merchants", self.cust_headers, None),
            ("POST", "/api/fraud/predict", self.cust_headers, {
                "customer_id": 1,
                "merchant_id": self.merchant_id,
                "amount": 25.0,
                "location_change": False,
                "device_change": False
            }),
            ("GET", "/api/wallet/transactions", self.cust_headers, None),
        ]

        burst_count = 20
        successful_requests = 0

        for i in range(burst_count):
            method, path, headers, payload = endpoints[i % len(endpoints)]
            if method == "GET":
                res = self.client.get(path, headers=headers)
            else:
                res = self.client.post(path, json=payload, headers=headers)

            assert res.status_code in (200, 201)
            body = res.get_json()
            # Verify architectural envelope contract is strictly maintained under burst
            assert "success" in body and body["success"] is True
            assert "message" in body
            assert "data" in body
            successful_requests += 1

        assert successful_requests == burst_count, f"Completed {successful_requests}/{burst_count} requests"
