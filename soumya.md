# SecurePay — Project Presentation & Viva Defense Guide
**Author / Presenter:** Soumya  
**Project Title:** SecurePay — Digital Payment Gateway with Real-Time ML Fraud Detection  
**Target Course:** Software Engineering / Software Testing  

---

## 1. Executive Summary & Elevator Pitch

> "SecurePay is a full-stack, monolithic FinTech payment gateway equipped with an integrated **Machine Learning Fraud Gatekeeper**. Unlike traditional gateways that inspect transactions asynchronously after funds move, SecurePay intercepts and scores every payment in real time **before** any ledger balance is updated. If the ML model flags a transaction as suspicious (`risk_score >= 0.5`), the payment is rejected immediately at the gateway, ensuring zero unauthorized money is deducted."

---

## 2. In-Depth Tech Stack Breakdown

| Component | Technology | Rationale & Software Engineering Purpose |
|---|---|---|
| **Frontend** | React 18, Vite, React Router v6, Axios, Recharts | Component-based Single Page Application (SPA). Vite provides ultra-fast Hot Module Replacement (HMR). Axios handles HTTP requests with JWT Bearer token interception. Recharts visualizes transaction trends dynamically. |
| **Backend** | Python 3.11, Flask, Flask-SQLAlchemy, Flask-JWT-Extended | Modular Blueprint architecture separating concerns. Flask-SQLAlchemy ORM prevents raw SQL injection and manages DB sessions. Flask-JWT-Extended enforces Role-Based Access Control (RBAC). |
| **Database** | SQLite (default zero-config) / MySQL (DDL provided) | Relational 3rd Normal Form (3NF) design ensuring ACID transaction compliance (Atomicity, Consistency, Isolation, Durability) for financial ledger records. |
| **Machine Learning** | Scikit-learn, Pandas, NumPy, Joblib | Supervised binary classification. **Random Forest Classifier** selected over Logistic Regression based on **F1-Score** (0.84 production, 0.89 BankSim benchmark). Joblib serializes and caches the trained model in RAM for low-latency inference. |
| **Security** | Werkzeug PBKDF2-SHA256, PyJWT (HMAC-SHA256) | Salted password hashing prevents rainbow-table attacks. Stateless Bearer tokens secure REST endpoints. CORS headers regulate cross-origin browser requests. |
| **Testing** | Pytest, Werkzeug Test Client | **47 automated test cases** covering Unit Testing, Web-Based Systems Testing, Non-Functional Testing (NFT), Security & RBAC matrix, and Regression Guards. |

---

## 3. System Architecture & Component Design

```
                      ┌─────────────────────────────────────────┐
                      │        React 18 SPA (Vite :3000)        │
                      │  Customer / Merchant / Admin Dashboards │
                      └────────────────────┬────────────────────┘
                                           │ REST API (JSON / Bearer JWT)
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │          Flask API (Port :5000)         │
                      │ ├─ Route Blueprints (Auth, Pay, QR...)  │
                      │ ├─ Service Layer (Payment & Fraud)      │
                      └─────────────┬───────────────────────────┘
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│     ML Fraud Engine (ml/)     │        │     Relational DB (SQLAlchemy)│
│  - Feature Extraction (12)    │        │  - Users, Customers, Merchants│
│  - Random Forest Scorer       │        │  - Wallets, Ledger Transactions│
│  - Risk Score: 0.0 to 1.0     │        │  - Payments, Fraud Records    │
└───────────────────────────────┘        └───────────────────────────────┘
```

### Layered Separation of Concerns
1. **Presentation Layer (`frontend/src/`):** Role-specific dashboards for Customers, Merchants, and Admins.
2. **Controller Layer (`backend/app/routes/`):** Validates HTTP requests, parses headers/parameters, and returns uniform JSON responses.
3. **Service Layer (`backend/app/services/`):** Orchestrates core business rules:
   * `payment_service.py`: Transactional workflow, balance checks, wallet debits/credits.
   * `fraud_service.py`: Feature mapping and translation between DB entities and ML vectors.
4. **Data Access Layer (`backend/app/models/`):** SQLAlchemy ORM models (`User`, `Customer`, `Merchant`, `Wallet`, `Payment`, `Transaction`, `FraudDetection`, `Refund`, `QRPaymentSession`).

---

## 4. End-to-End Transaction & Fraud Gate Workflow

```
Customer Submits Payment
         │
         ▼
[1] Validation: Amount > 0? Merchant exists? Wallet active & sufficient balance?
         │
         ├─── (No) ──► Return HTTP 400 Validation Error
         │
         ▼ (Yes)
[2] Stage Payment Record in DB (Status: 'pending')
         │
         ▼
[3] Extract 12 Real-Time Features from DB & Session
         │
         ▼
[4] ML Random Forest Model Scores Risk (0.0 to 1.0)
         │
         ├─────────────────────────────────────────────┐
         ▼                                             ▼
If Risk Score >= 0.5 (SUSPICIOUS)             If Risk Score < 0.5 (SAFE)
         │                                             │
• Payment status -> 'rejected'                • Debit Customer Wallet
• Failure reason -> 'ML Fraud Flag'            • Credit Merchant Wallet
• Fraud log record saved                       • Insert Ledger Transaction Records
• ZERO money deducted from Wallet              • Payment status -> 'success'
• DB session committed                         • DB session committed
```

---

## 5. The 12 Machine Learning Features

The model evaluates transactions across 12 behavioral, temporal, and risk dimensions:

| # | Feature Name | Description & FinTech Context |
|---|---|---|
| 1 | `transaction_amount` | Payment amount in dollars/currency. |
| 2 | `transaction_hour` | Hour of day (0–23). Anomalous late-night activity increases risk. |
| 3 | `transaction_frequency` | Number of payments initiated by this customer in the past 24 hours. |
| 4 | `customer_age` | Demographic age of the account holder. |
| 5 | `account_age` | Days elapsed since account registration (brand-new accounts carry higher risk). |
| 6 | `previous_transaction_count` | Lifetime successful transactions (established history lowers risk). |
| 7 | `average_transaction_amount` | Customer's historical mean payment value (detects sudden spending spikes). |
| 8 | `merchant_risk` | Historical fraud ratio associated with the recipient merchant. |
| 9 | `failed_transaction_count` | Prior failed/declined attempts (signals brute-force attempts). |
| 10 | `location_change` | Binary flag (0 or 1) indicating sudden geo-location disparity. |
| 11 | `device_change` | Binary flag (0 or 1) indicating an unfamiliar user agent or device hardware. |
| 12 | `previous_fraud_count` | Number of times this customer was previously flagged for fraud. |

---

## 6. QR Code Payment & Real-Time Sync (Google Lens / Camera)

1. **Merchant POS Terminal:** The merchant specifies an amount (e.g., `$45.00`).
2. **Session Generation:** Server generates an ephemeral token and returns a base64 QR code pointing to `http://<LAN_IP>:3000/pay/qr/<token>`.
3. **Mobile Scan:** A customer scans the screen with Google Lens or any phone camera app on the local network.
4. **Mobile Checkout:** The responsive page loads customer wallet details with 1-tap confirmation.
5. **Real-Time Dual-Screen Polling:** The merchant screen polls `/api/qr-payments/<token>/status` every 1.5 seconds. The moment the customer pays on mobile, the merchant screen automatically flips to **"Payment Received!"**.

---

## 7. Software Engineering & Testing Principles

### Software Engineering Concepts Applied:
* **Principle of Least Privilege (RBAC):** Customer, Merchant, and Admin accounts are isolated by cryptographic JWT claims.
* **ACID Transactions:** Financial operations use `db.session` to guarantee atomicity—if any step fails, money is never lost or duplicated.
* **Singleton Pattern:** The ML model (`model.pkl`) is loaded once into memory upon boot (`load_model()`) to eliminate disk I/O overhead on every payment.

### Software Testing Implementation (`tests/test_web_system.py` & `tests/test_non_functional.py`):
SecurePay includes **47 automated tests**, including dedicated suites for **Testing Web-Based Systems**, **Non-Functional Testing (NFT)**, and **Regression Testing**:
1. **Contract Testing:** Asserts standardized JSON envelopes: `{success, message, data}`.
2. **Security & Session Testing:** Rejects forged/missing JWT tokens with `HTTP 401`.
3. **RBAC Matrix Testing:** Confirms Customers cannot access Admin endpoints (`HTTP 403`).
4. **Boundary Value Testing:** Rejects zero and negative amounts (`HTTP 400`).
5. **CORS Testing:** Validates preflight `OPTIONS` requests and security headers.
6. **State Lifecycle Testing:** Verifies QR payment session transitions (`pending` → `completed`).
7. **Regression Guards:** Prevents duplicate refund exploitation and ensures ML risk scores are clamped between `0.0` and `1.0`.
8. **Non-Functional Testing (NFT):** Enforces sub-250ms payment & ML latency SLAs, OWASP injection parameterization resilience, concurrent wallet balance overdraw protection, ACID atomic rollback on fault injection, and burst load stability.

---

## 8. Professor Viva Defense — Questions & Answers

### Domain & Architecture
**Q1: Why choose a monolithic REST API over Microservices for this project?**  
> *"For a payment simulation system of this scale, a modular monolith using Flask Blueprints provides low latency, simplifies ACID transaction handling within a single database, avoids distributed transaction complexity (like 2-Phase Commit or Saga patterns), and eliminates network serialization overhead between services."*

**Q2: How do you prevent the Double-Spending problem?**  
> *"All checks, deductions, credits, and ledger insertions are executed inside an atomic database transaction (`db.session`). If any step or fraud check fails, the transaction is aborted before being committed to the database, ensuring no balance inconsistencies occur."*

**Q3: How does your refund mechanism handle race conditions or abuse?**  
> *"We enforce a single-refund invariant. Before creating a refund request, the system checks whether an existing refund record already exists for that `payment_id`. If one exists, the request is rejected with `HTTP 400/409`. This is strictly guarded by automated regression tests."*

### Machine Learning & Data Science
**Q4: Why Random Forest over Logistic Regression or Deep Learning?**  
> *"Financial transaction fraud exhibits non-linear relationships and high feature cross-interactions (e.g., high transaction amount combined with an odd hour and unfamiliar device). Logistic Regression struggles with non-linear boundaries without extensive manual polynomial transformations. Deep learning would introduce unnecessary latency and require massive datasets. Random Forest offers high predictive power, resistance to overfitting, and sub-10ms inference latency."*

**Q5: Why evaluate with F1-Score instead of Accuracy?**  
> *"Fraud datasets are severely imbalanced—fraudulent cases make up less than 5% of all transactions. A naive model that predicts 'Safe' 100% of the time would have over 95% accuracy while catching zero fraud. F1-score balances Precision (minimizing false accusations against legit users) and Recall (catching actual thieves). Our Random Forest model achieves an F1-score of 0.84 on production synthetic data and 0.89 on the real BankSim benchmark."*

### Security & Web Standards
**Q6: How does JWT authentication protect the system?**  
> *"When a user logs in, the backend signs a stateless token using HMAC-SHA256 containing user ID and role. On subsequent requests, the `@jwt_required` decorator validates the cryptographic signature. The server decodes the role claim to enforce Role-Based Access Control without querying the database for authorization on every route."*

**Q7: How are passwords protected?**  
> *"Passwords are salted and hashed using PBKDF2 with SHA-256 via Werkzeug. Passwords are never stored in plaintext, guarding against rainbow-table attacks in case of database leaks."*

### Software Testing
**Q8: How did you test the system according to the software engineering syllabus?**  
> *"We designed object-oriented test suites covering Web-Based System Testing, Non-Functional Testing (NFT), and Regression Testing (`tests/test_web_system.py` and `tests/test_non_functional.py`). It verifies client-server contracts, HTTP status code specifications (401, 403, 400, 200), boundary values, performance/latency SLAs (<250ms), SQL injection defenses, concurrent wallet invariant preservation, atomic failure rollback, and regression guards for duplicate refunds and ML boundary clamping. In total, 47 automated test cases pass with a 100% pass rate."*

---

## 9. 3-Minute Live Demonstration Script

When presenting to your professor, follow these 4 steps:

1. **Launch the Application:**
   * Open Command Prompt, run `D:`, `cd SecurePay`, and run `start.bat`.
   * *"This automated batch script seeds our relational database and starts both the Flask API server (port 5000) and Vite React frontend (port 3000)."*
2. **Demonstrate Customer & Merchant Workflow:**
   * Open `http://localhost:3000`.
   * Log in as `customer1@securepay.com` (`password123`).
   * Show wallet balance, add $100 demo funds, and make a standard safe payment.
3. **Demonstrate the Machine Learning Fraud Gate:**
   * Make a payment with simulated anomaly flags (or high amount).
   * Show the real-time response: **Decision: Suspicious**, **Risk Score > 0.5**.
   * Highlight that **zero funds were deducted** from the customer wallet.
4. **Demonstrate Automated Testing:**
   * In Command Prompt, run:
     ```cmd
     python -m pytest tests/test_web_system.py -v
     ```
   * Show the 8 green `PASSED` test cases verifying web architecture and regression integrity.
