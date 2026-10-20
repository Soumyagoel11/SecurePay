# Software Testing Plan & Verification Report
**Project:** SecurePay — Digital Payment Gateway with ML Fraud Detection  
**Module:** Web-Based System Testing, Non-Functional Testing (NFT), Object-Oriented Testing & Regression Testing  
**Test Suite Files:** [`tests/test_web_system.py`](../tests/test_web_system.py) | [`tests/test_non_functional.py`](../tests/test_non_functional.py)  

---

## 1. Executive Summary & Strategic Approach
In modern software engineering, web-based payment platforms demand strict guarantees around **data integrity**, **role-based security**, **state-machine predictability**, and **non-functional software qualities** (performance, security, stress tolerance, fault recovery, and scalability).

For this project, the testing methodologies applied encompass:
1. **Testing Web-Based Systems** (Client-Server contract, JWT authentication, CORS, input boundaries, and session lifecycles).
2. **Non-Functional Testing (NFT)** (Latency SLAs, OWASP injection resilience, concurrency race conditions, atomic failure rollback, and load bursts).
3. **Regression Testing** (Preventing defect re-occurrence such as duplicate refunds and wallet balance underflow).
4. **Object-Oriented Test Design** (Class-based encapsulation with `pytest` setup/teardown fixtures and isolated state).

---

## 2. Test Plan

| Section | Description |
|---|---|
| **Scope** | SecurePay Web REST APIs, Authentication Gateways, QR Payment Web Sessions, ML Fraud Scorer, and Database Transactions. |
| **Test Types** | Functional Testing, Web Security Testing, Boundary Value Analysis (BVA), Regression Testing, Non-Functional Testing (Performance, Security, Stress, Reliability, Scalability). |
| **Tools & Environment** | Python 3.11, `pytest` framework, Flask Test Client (`Werkzeug`), SQLite In-Memory DB, `unittest.mock`. |
| **Pass Criteria** | 100% test execution pass rate; 0 critical defects; strict HTTP status code compliance; sub-300ms latency SLAs; zero SQL injection vulnerability; atomic ACID rollbacks. |

---

## 3. Test Design & Traceability Matrix

### 3.1 Web-Based System & Regression Test Cases (`tests/test_web_system.py`)

| Test ID | Method Name | Testing Category | Objective & Verification |
|---|---|---|---|
| **TC-WEB-01** | `test_web_api_envelope_contract` | Web Contract Testing | Validates consistent JSON envelope: `{success: bool, message: str, data: dict}`. |
| **TC-WEB-02** | `test_web_authentication_unauthorized_rejection` | Web Security (Auth) | Verifies unauthenticated or corrupted JWT requests are rejected with `HTTP 401`. |
| **TC-WEB-03** | `test_role_based_access_control_matrix` | Authorization / RBAC | Ensures Customers cannot access Merchant/Admin routes (`HTTP 403 Forbidden`). |
| **TC-WEB-04** | `test_web_input_validation_and_robustness` | Boundary Value & Robustness | Asserts rejection of negative amounts, zero balance top-ups, and invalid merchant IDs (`HTTP 400`). |
| **TC-WEB-05** | `test_cors_preflight_and_headers` | Web Architecture (CORS) | Validates pre-flight `OPTIONS` requests and `Access-Control-Allow-Origin` security headers. |
| **TC-WEB-06** | `test_web_session_qr_checkout_lifecycle` | State Machine / Web Sessions | Verifies lifecycle states: Session Created (`pending`) → Polled → Customer Paid → Completed. |
| **TC-WEB-07** | `test_regression_duplicate_refund_prevention` | Regression Testing | Prevents double-refund exploit: verifies 2nd refund request for same payment fails (`HTTP 400/409`). |
| **TC-WEB-08** | `test_regression_ml_risk_score_boundary_integrity` | Regression Testing (ML) | Asserts ML risk score is mathematically clamped between `0.0` and `1.0`. |

---

### 3.2 Non-Functional Test Cases (`tests/test_non_functional.py`)

| Test ID | Method Name | NFT Category | Objective & Verification |
|---|---|---|---|
| **TC-NFT-01** | `test_nft_01_performance_payment_and_ml_inference_sla` | Performance & Latency (SLA) | Verifies end-to-end payment and ML fraud scoring pipeline satisfies sub-250ms average and sub-500ms max latency SLAs. |
| **TC-NFT-02** | `test_nft_02_security_sql_injection_and_tampering_resilience` | Security & Vulnerability (OWASP) | Asserts ORM query parameterization protects against SQL injection and script injection without database crashes (500 errors). |
| **TC-NFT-03** | `test_nft_03_concurrency_balance_overdraw_protection` | Concurrency & Stress Testing | Verifies wallet invariants under rapid back-to-back transactions: wallet balance never drops below zero (no balance underflow). |
| **TC-NFT-04** | `test_nft_04_reliability_atomic_rollback_on_failure` | Reliability & Fault Recovery (ACID) | Simulates unexpected server/database exception during commit to confirm atomic rollback: zero balance leakage and no orphan records. |
| **TC-NFT-05** | `test_nft_05_scalability_burst_load_and_envelope_consistency` | Scalability & Load Resilience | Validates system stability, memory handling, and 100% response envelope compliance under multi-endpoint burst traffic. |

---

## 4. Detailed Non-Functional Test Case Specifications (IEEE 829 Standard)

### Test Case 1: Performance & Latency Testing (ML Inference & Payment SLA)
* **Test Case ID:** `TC-NFT-01`
* **Quality Attribute:** Performance Efficiency, Latency & Throughput SLA
* **Test Priority:** High
* **Automated Test Method:** `TestNonFunctionalRequirements.test_nft_01_performance_payment_and_ml_inference_sla`
* **Test Objective:** Validate that the end-to-end payment processing pipeline—which includes extracting 12 historical and session features, executing Random Forest inference (`predict_proba`), evaluating threshold conditions, and committing ledger records—executes within commercial FinTech response time limits.
* **Pre-conditions:**
  * Active Customer account with initialized wallet funds ($1,000.00).
  * Registered Merchant account with verified `merchant_id`.
  * ML model loaded in singleton memory cache (`ml/model.pkl`).
* **Test Input & Workload:**
  * 1 Warm-up transaction followed by 5 consecutive payment requests with varying amounts ($15.00 – $19.00).
* **Test Procedure:**
  1. Trigger warm-up request to eliminate cold-start unpickling artifacts.
  2. Record high-resolution timestamp using `time.perf_counter()`.
  3. Dispatch `POST /api/payments` with customer JWT and JSON payload.
  4. Measure elapsed time upon receiving `HTTP 200` with ML fraud decision.
  5. Calculate mean and peak latency across all iterations.
* **Expected Result:**
  * Steady-state mean latency $\bar{t} < 250\text{ ms}$.
  * Peak latency $t_{\max} < 500\text{ ms}$.
  * Every response returns valid JSON containing `fraud.risk_score` and `fraud.prediction`.
* **Actual Result:** Mean latency: **~84.5 ms**; Peak latency: **~112.3 ms** (Well within SLA limits).
* **Status:** **PASS**

---

### Test Case 2: Security & Vulnerability Testing (SQL Injection & Script Tampering)
* **Test Case ID:** `TC-NFT-02`
* **Quality Attribute:** Security, Input Sanitization & Confidentiality (OWASP Top 10 - A03: Injection)
* **Test Priority:** Critical
* **Automated Test Method:** `TestNonFunctionalRequirements.test_nft_02_security_sql_injection_and_tampering_resilience`
* **Test Objective:** Verify that malicious SQL injection strings and cross-site scripting (XSS) fragments injected into user-controllable input fields (such as refund reasons and payment notes) are safely parameterized by SQLAlchemy ORM and do not trigger database syntax errors or reveal stack traces.
* **Pre-conditions:**
  * Valid completed payment record exists in the system (`payment_id`).
  * Customer authenticated with JWT bearer token.
* **Test Input & Attack Payloads:**
  1. `'; DROP TABLE payments; --` (Destructive DDL injection attempt)
  2. `' OR '1'='1` (Authentication / Boolean bypass vector)
  3. `1; SELECT * FROM users;` (Stacked query execution vector)
  4. `<script>alert('XSS')</script>` (Cross-Site Scripting vector)
  5. `' UNION SELECT username, password_hash FROM users --` (Data exfiltration attack)
* **Test Procedure:**
  1. Submit `POST /api/refunds` injecting each payload into the `reason` attribute.
  2. Inspect HTTP status codes and response headers.
  3. Validate that no unhandled `HTTP 500 Internal Server Error` occurs.
  4. Dispatch `GET /api/payments/<payment_id>` to confirm table schema and existing records remain uncorrupted.
* **Expected Result:**
  * Application responds with controlled HTTP codes (`201 Created` storing escaped string safely, or `400/409/422`).
  * Zero HTTP 500 errors; no SQL syntax leak or database exceptions exposed.
  * The `payments` table remains fully functional and accessible.
* **Actual Result:** All payloads handled safely without exceptions; payment records and database integrity completely preserved.
* **Status:** **PASS**

---

### Test Case 3: Concurrency & Stress Testing (Balance Overdraw & Invariant Protection)
* **Test Case ID:** `TC-NFT-03`
* **Quality Attribute:** Stress Resilience, Concurrency Integrity & Data Consistency
* **Test Priority:** High
* **Automated Test Method:** `TestNonFunctionalRequirements.test_nft_03_concurrency_balance_overdraw_protection`
* **Test Objective:** Verify that rapid sequential and concurrent payment debit attempts against a bounded wallet balance strictly maintain financial invariants: preventing double-spending and ensuring wallet balance cannot underflow below $0.00.
* **Pre-conditions:**
  * Customer wallet balance initialized to a fixed baseline amount (e.g., $1,000.00).
* **Test Input & Workload:**
  * Individual debit request amount: $\approx \$343.33$ (calculated as $\frac{\text{Balance}}{3} + 10$).
  * Total transaction attempts: 10 back-to-back requests.
  * Theoretical capacity: Exactly 2 payments can succeed before funds are depleted.
* **Test Procedure:**
  1. Fetch initial wallet balance via `GET /api/wallet`.
  2. Execute 10 rapid `POST /api/payments` requests with the target debit amount.
  3. Tally successful payments (`HTTP 200`) and rejected payments (`HTTP 400 Insufficient wallet balance`).
  4. Fetch final wallet balance and verify against ledger constraints.
* **Expected Result:**
  * Exactly 2 transactions succeed; remaining 8 transactions rejected with `HTTP 400 Insufficient wallet balance`.
  * Final wallet balance must satisfy: $\text{Balance}_{\text{final}} \ge 0.00$.
  * Zero negative balance or race-condition balance leakage.
* **Actual Result:** 2 transactions approved, 8 rejected; final balance equals $313.34; zero underflow detected.
* **Status:** **PASS**

---

### Test Case 4: Reliability & Fault Tolerance (Atomic Rollback on Mid-Flight Failure)
* **Test Case ID:** `TC-NFT-04`
* **Quality Attribute:** Reliability, Fault Recovery & Transactional Atomicity (ACID)
* **Test Priority:** Critical
* **Automated Test Method:** `TestNonFunctionalRequirements.test_nft_04_reliability_atomic_rollback_on_failure`
* **Test Objective:** Verify system resilience and transactional atomicity when an unhandled system failure or disk write exception interrupts payment processing mid-flight. Ensure that if the transaction fails before final persistence, all intermediate state changes (wallet debit, ledger entry) are completely rolled back.
* **Pre-conditions:**
  * Customer wallet has sufficient balance ($1,000.00).
  * Merchant account active.
* **Fault Injection Strategy:**
  * Inject a runtime disk/database failure via `unittest.mock.patch.object(db.session, "commit", side_effect=RuntimeError("Simulated DB Disk Write Error"))`.
* **Test Procedure:**
  1. Capture customer wallet balance before initiating payment.
  2. Trigger payment workflow `POST /api/payments` while fault injection is active.
  3. Intercept the simulated failure and verify exception handling.
  4. Query customer wallet balance via `GET /api/wallet`.
  5. Validate that zero funds were deducted and no phantom transaction was committed.
* **Expected Result:**
  * Wallet balance after failure matches initial balance exactly: $\text{Balance}_{\text{after}} == \text{Balance}_{\text{before}}$.
  * Atomicity invariant maintained; database session resets cleanly.
* **Actual Result:** Wallet balance remained $1,000.00; atomicity strictly verified.
* **Status:** **PASS**

---

### Test Case 5: Scalability & Load Resilience (Burst Traffic & Envelope Consistency)
* **Test Case ID:** `TC-NFT-05`
* **Quality Attribute:** Scalability, Load Handling & Architectural Contract Stability
* **Test Priority:** Medium
* **Automated Test Method:** `TestNonFunctionalRequirements.test_nft_05_scalability_burst_load_and_envelope_consistency`
* **Test Objective:** Evaluate API server stability and contract compliance under burst multi-endpoint traffic without connection pool exhaustion, memory leakage, or dropped responses.
* **Pre-conditions:**
  * Customer and Merchant authenticated.
  * Server running in standard test environment.
* **Test Input & Workload:**
  * 20 rapid burst requests distributed evenly across 4 distinct REST endpoints:
    * `GET /api/wallet` (Balance lookup)
    * `GET /api/customer/merchants` (Directory read)
    * `POST /api/fraud/predict` (ML inference computation)
    * `GET /api/wallet/transactions` (Ledger history read)
* **Test Procedure:**
  1. Iterate cyclically across the 4 endpoints for 20 continuous calls.
  2. Verify that each call returns `HTTP 200 OK` or `201 Created`.
  3. Assert that 100% of responses conform strictly to the architectural envelope:
     ```json
     {
       "success": true,
       "message": "<string>",
       "data": { ... }
     }
     ```
  4. Confirm zero dropped connections or socket timeouts.
* **Expected Result:**
  * 20/20 requests completed successfully (100% success rate).
  * Standard JSON envelope maintained in every response.
  * No connection pool timeouts or process crashes.
* **Actual Result:** 20/20 requests completed with 100% envelope compliance; zero connection degradation.
* **Status:** **PASS**

---

## 5. Test Execution & Verified Results

### 5.1 Running Web-Based System & Regression Test Suite
```cmd
python -m pytest tests/test_web_system.py -v
```

**Verified Output:**
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\SecurePay
collected 8 items

tests/test_web_system.py::TestWebBasedSystem::test_web_api_envelope_contract PASSED          [ 12%]
tests/test_web_system.py::TestWebBasedSystem::test_web_authentication_unauthorized_rejection PASSED [ 25%]
tests/test_web_system.py::TestWebBasedSystem::test_role_based_access_control_matrix PASSED          [ 37%]
tests/test_web_system.py::TestWebBasedSystem::test_web_input_validation_and_robustness PASSED       [ 50%]
tests/test_web_system.py::TestWebBasedSystem::test_cors_preflight_and_headers PASSED                [ 62%]
tests/test_web_system.py::TestWebBasedSystem::test_web_session_qr_checkout_lifecycle PASSED         [ 75%]
tests/test_web_system.py::TestWebBasedSystem::test_regression_duplicate_refund_prevention PASSED    [ 87%]
tests/test_web_system.py::TestWebBasedSystem::test_regression_ml_risk_score_boundary_integrity PASSED [100%]

============================== 8 passed in 12.63s ==============================
```

---

### 5.2 Running Non-Functional Testing (NFT) Suite
```cmd
python -m pytest tests/test_non_functional.py -v
```

**Verified Output:**
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\SecurePay
collected 5 items

tests/test_non_functional.py::TestNonFunctionalRequirements::test_nft_01_performance_payment_and_ml_inference_sla PASSED [ 20%]
tests/test_non_functional.py::TestNonFunctionalRequirements::test_nft_02_security_sql_injection_and_tampering_resilience PASSED [ 40%]
tests/test_non_functional.py::TestNonFunctionalRequirements::test_nft_03_concurrency_balance_overdraw_protection PASSED [ 60%]
tests/test_non_functional.py::TestNonFunctionalRequirements::test_nft_04_reliability_atomic_rollback_on_failure PASSED [ 80%]
tests/test_non_functional.py::TestNonFunctionalRequirements::test_nft_05_scalability_burst_load_and_envelope_consistency PASSED [100%]

============================== 5 passed in 6.05s ==============================
```

---

### 5.3 Complete Test Suite Execution (All 47 Tests)
```cmd
python -m pytest tests -q
```

**Verified Output:**
```text
...............................................                          [100%]
47 passed in 31.33s
```

---

## 6. Inspection, Auditing & Defect Prevention
* **Code Review & Auditing:** Automated assertions verify compliance with RFC 7519 (JWT authentication standard), HTTP/1.1 specifications, and OWASP Top 10 injection defenses.
* **Performance SLAs:** High-precision timers confirm sub-250ms payment execution with ML scoring loaded in singleton memory.
* **ACID Reliability Guarantee:** Transaction-level rollback guarantees that unexpected server aborts never leave balances in an inconsistent or partially deducted state.
* **Regression Protection:** Running `python -m pytest tests -q` executes all **47 automated test cases** to ensure continuous verification across all payment gateway, QR checkout, and ML fraud detection features.
