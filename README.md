# SecurePay — Digital Payment Gateway with ML Fraud Detection

SecurePay is a full-stack, monolithic web application that lets customers hold a
digital wallet, pay merchants, and have **every transaction scored by a Machine
Learning fraud-detection model**. It includes role-based dashboards for
Customers, Merchants, and Admins, a refund workflow, and a clean REST API.

> This is a **simulation / college demo** payment system. No real banking or
> payment processing is integrated, and no real financial data is used.

---

## 1. Project Overview

* Customers register, hold a wallet, add demo money, and pay merchants.
* Every payment is run through an ML fraud model that returns a **risk score**,
  a **prediction** (`Safe` / `Suspicious`), and a **fraud flag**.
* Payments flagged as suspicious are **rejected before any money moves**.
* Merchants see received payments, transaction stats, and suspicious activity.
* Admins manage users/merchants/transactions, review fraud reports, and approve
  or reject refund requests.

---

## 2. Features

| Area | Highlights |
| --- | --- |
| Auth | JWT login/register, password hashing (Werkzeug PBKDF2), role-based access control |
| Wallet | Balances, demo top-up, transaction ledger |
| Payments | Full validated workflow with ML fraud gate |
| QR Payments | Merchant POS terminal, dynamic & store QR codes, **Google Lens / mobile camera scan**, dual-screen live sync |
| Fraud ML | Trained classifier, configurable threshold, risk scoring |
| Refunds | Customer request → Admin approve/reject, single-refund guard |
| Dashboards | Per-role statistics and tables |
| Security | Input validation, 401/403/404/409/422/500 handling, no secret leakage |

---

## 3. Technology Stack

| Layer | Tech |
| --- | --- |
| Frontend | React 18, React Router, Axios, Vite |
| Backend | Python, Flask, Flask-RESTful-style Blueprints, Flask-JWT-Extended, Flask-SQLAlchemy |
| Database | MySQL (schema provided) — also runs on SQLite out of the box |
| ML | scikit-learn, pandas, numpy, joblib |
| Tooling | Git, pytest, Postman (API collection optional) |

---

## 4. System Architecture

```
React SPA (Vite)
      │  HTTPS / REST (Axios, JWT Bearer)
      ▼
Flask API (Blueprints)
  ├─ Auth / Wallet / Payments / Fraud / Refunds / Admin / Merchant / Customer
  ├─ Services
  │    ├─ payment_service  → validation + DB transaction + fraud gate
  │    └─ fraud_service    → feature-mapping layer (SecurePay → ML features)
  ├─ ML module (ml/)
  │    ├─ datasets.py  (real BankSim loader + documented synthetic fallback)
  │    ├─ train_model.py (Train + benchmark)
  │    └─ predict.py  (load model, score transaction)
  └─ SQLAlchemy models → MySQL / SQLite
```

The **feature-mapping layer** is the key integration point: a SecurePay payment
is converted into the model's 12-feature vector before scoring.

---

## 5. Database Structure

Entities (see `database/schema.sql` for the canonical MySQL DDL):

`users` → `customers` / `merchants` / `admins` (1:1)
`wallets` (1:1 with customer)
`payments` (customer → merchant)
`transactions` (wallet ledger)
`fraud_detections` (1:1 with payment)
`refunds` (1:1 with payment)

Primary keys, foreign keys, indexes, NOT NULL and UNIQUE constraints are all
defined. The schema matches the SQLAlchemy models in `backend/app/models/`.

---

## 6. ML Fraud Detection Approach

**Real dataset, not a toy rule.** The pipeline supports the real
[BankSim](https://www.kaggle.com/ntnu-testimon/banksim1) dataset
(`bs140513_032310.csv`) for training/evaluation. Two models are compared —
**Logistic Regression** and **Random Forest** — and the better one is selected by
**F1-score** (not raw accuracy, because fraud is highly imbalanced).

> Why not accuracy? A model that always predicts "not fraud" can look 98%
> accurate while catching zero fraud. We rely on **precision** (of flagged
> transactions, how many are truly fraud → fewer blocked legit users) and
> **recall** (of actual fraud, how much we catch → less money lost). F1 balances
> both.

**Production model:** trained on a clearly-documented synthetic generator whose
12 features use the *same semantics* as the features built at inference time from
SecurePay's database. This keeps the model well-calibrated for live payments
while remaining fully reproducible. The real BankSim dataset is used for
transparent benchmarking (`ml/banksim_benchmark.txt`), following the
"real data for evaluation, application data for the workflow" pattern.

**Features (12):** transaction_amount, transaction_hour, transaction_frequency,
customer_age, account_age, previous_transaction_count, average_transaction_amount,
merchant_risk, failed_transaction_count, location_change, device_change,
previous_fraud_count.

**Outputs:** `prediction`, `risk_score` (0–1), `fraud_flag`. A configurable
threshold (`FRAUD_THRESHOLD`, default `0.5`) maps `risk_score >= threshold`
→ `Suspicious`.

---

## 6.1. QR Code Payment & Google Lens Workflow

SecurePay provides an end-to-end QR code payment workflow designed for in-person and digital transactions:

1. **Merchant POS Terminal (`/merchant/qr-terminal`):**
   * Merchant inputs an amount (e.g. `$50.00`) and order note/reference.
   * A dynamic payment session is generated, creating a scannable QR code.
   * Auto-detects the computer's LAN IP address (e.g. `172.20.10.4:3000`) so phones on the same Wi-Fi can scan and open it effortlessly.
   * Displays live status radar: `"Waiting for customer scan and payment..."`.

2. **Google Lens & Mobile Camera Scanning:**
   * Customer scans the QR code on the screen using **Google Lens** or any native phone camera app.
   * Google Lens detects the URL and opens the mobile-optimized checkout page (`/pay/qr/<token>`).
   * Customer sees the merchant name, order amount, and can pay via their wallet in 1 tap (supports demo 1-tap customer switcher or direct login).
   * Includes optional toggles to simulate location/device anomalies and test the ML fraud engine.

3. **Instant Mobile Confirmation:**
   * When approved, the mobile/Google Lens screen immediately displays **"Payment Successful!"** with an animated checkmark, transaction receipt, and ML Fraud Safety verification badge (`Decision: Safe, Risk Score: 0.04`).
   * If flagged suspicious by the ML gate, the mobile screen alerts the customer that the payment was blocked and zero funds were deducted.

4. **Real-Time Dual-Screen Web Update:**
   * The Merchant Terminal polls the session status in the background.
   * The exact moment payment completes on the phone, the Merchant's screen instantly flips to **"Payment Received!"**, showing the amount, customer ID, timestamp, and ML fraud score in real time.

---

## 7. Quick Start & Installation

### Easy 1-Click Run (Windows)
Double-click or run:
```cmd
start.bat
```
This automatically sets up demo data and launches both backend (`http://localhost:5000`) and frontend (`http://localhost:3000`).

---

### Manual Setup (Step-by-Step)

#### Prerequisites
* Python 3.10+
* Node.js 18+ and npm
* (Optional) MySQL 8 — the app runs on SQLite by default without setup

#### 1. Backend
```bash
cd backend
python -m venv venv && venv\Scripts\activate      # or: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit secrets / DATABASE_URL if using MySQL
```

### 2. Train the ML model
```bash
python -m ml.train_model
# → writes ml/model.pkl (production model) and benchmarks on real BankSim if present
```
To use the **real BankSim dataset**, drop `bs140513_032310.csv` into
`backend/ml/dataset/`. (Optional — the synthetic fallback is used otherwise.)

### 3. Database
* **SQLite (default):** tables are auto-created on first run.
* **MySQL:** create the database and tables:
  ```bash
  mysql -u root -p < ../database/schema.sql
  ```
  then set `DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/securepay` in `.env`.

### 4. Seed demo data
```bash
python seed.py
```
Creates 1 admin, 2 merchants, 5 customers (with wallets), sample payments, a
fraud record, and a pending refund.

### 5. Run backend
```bash
python run.py
# → http://localhost:5000
```

### 6. Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
# → http://localhost:3000  (proxies /api to localhost:5000)
```

---

## 8. Environment Variables (`backend/.env`)
| Variable | Purpose | Default |
| --- | --- | --- |
| `SECRET_KEY` | Flask secret | dev value |
| `JWT_SECRET_KEY` | JWT signing key | dev value |
| `DATABASE_URL` | DB connection string | `sqlite:///securepay.db` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `FRAUD_THRESHOLD` | Risk threshold → "Suspicious" | `0.5` |

Never commit `.env`. Secrets are loaded from the environment only.

---

## 9. Database Setup
See `database/schema.sql` (MySQL) and `backend/seed.py` (populates demo data for
either database).

---

## 10. Backend Setup
Covered in §7. Blueprints live in `backend/app/routes/`, services in
`backend/app/services/`, models in `backend/app/models/`.

---

## 11. Frontend Setup
Covered in §7. Components in `frontend/src/components/`, pages under
`frontend/src/pages/{customer,merchant,admin}/`, API client in
`frontend/src/services/api.js`, auth context in `frontend/src/context/`.

---

## 12. Model Training
```bash
python -m ml.train_model
```
* Loads BankSim if present, otherwise the documented synthetic generator.
* Trains Logistic Regression + Random Forest.
* Selects the best by F1-score and serializes it with joblib to `ml/model.pkl`.
* Prints accuracy / precision / recall / F1 / confusion matrix and benchmarks on
  real BankSim (if available).

Decision rationale and metrics are written to `ml/metrics.txt` and
`ml/banksim_benchmark.txt`.

---

## 13. API Documentation

Base URL: `/api`

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| POST | `/auth/register` | – | Register (role: customer/merchant/admin) |
| POST | `/auth/login` | – | Login → JWT |
| GET | `/auth/me` | JWT | Current user + profile |
| GET | `/wallet` | Customer | Wallet balance |
| POST | `/wallet/add-money` | Customer | Demo top-up |
| GET | `/wallet/transactions` | Customer | Wallet ledger |
| GET | `/customer/dashboard` | Customer | Stats + recent txns |
| GET | `/customer/merchants` | Customer | Merchant directory |
| POST | `/payments` | Customer | **Create + fraud-score payment** |
| GET | `/payments` | JWT | List (role-filtered) |
| GET | `/payments/<id>` | JWT | Payment detail + fraud + ledger |
| POST | `/fraud/predict` | JWT | Score a transaction context |
| GET | `/fraud/reports` | JWT | Fraud reports (role-filtered) |
| POST | `/refunds` | Customer | Request refund |
| GET | `/refunds` | JWT | List refunds |
| PUT | `/refunds/<id>/approve` | Admin | Approve + credit wallet |
| PUT | `/refunds/<id>/reject` | Admin | Reject |
| GET | `/merchant/dashboard` | Merchant | Revenue + stats |
| GET | `/merchant/suspicious` | Merchant | Flagged payments |
| GET | `/admin/dashboard` | Admin | System stats |
| GET | `/admin/users` | Admin | All users |
| GET | `/admin/merchants` | Admin | All merchants |
| GET | `/admin/transactions` | Admin | All payments |
| GET | `/admin/fraud-reports` | Admin | All fraud records |
| GET | `/admin/refunds` | Admin | All refunds |

All responses follow:
```json
{ "success": true, "message": "...", "data": { ... } }
```

---

## 14. Demo Credentials
Password for **all** demo accounts: `password123`

| Role | Email |
| --- | --- |
| Admin | `admin@securepay.com` |
| Merchant 1 | `merchant1@securepay.com` |
| Merchant 2 | `merchant2@securepay.com` |
| Customer 1 | `customer1@securepay.com` |
| Customer 2 | `customer2@securepay.com` |
| Customer 3 | `customer3@securepay.com` |
| Customer 4 | `customer4@securepay.com` |
| Customer 5 | `customer5@securepay.com` |

---

## 15. Testing

### Run All Tests (47 Passing)
```bash
python -m pytest tests -q
```

### Run Web-Based System & Regression Testing Suite
```bash
python -m pytest tests/test_web_system.py -v
```

### Run Non-Functional Testing (NFT) Suite
```bash
python -m pytest tests/test_non_functional.py -v
```
Covers:
* **Testing Web-Based Systems**: Client-Server API JSON contract, JWT session auth/rejection, RBAC access matrix, boundary/robustness validation, CORS headers, and real-time QR checkout session lifecycles.
* **Non-Functional Testing (NFT)**: Performance & ML inference latency SLAs (<250ms), OWASP SQL injection resilience, concurrency balance overdraw guards, ACID atomic rollback on failure, and burst load consistency.
* **Regression Testing**: Duplicate refund exploit prevention, wallet underflow guards, and ML risk score invariants.
* Complete documentation: see [`docs/SOFTWARE_TESTING_REPORT.md`](docs/SOFTWARE_TESTING_REPORT.md).

---

## 16. Future Improvements
* Replace SQLite with MySQL in production and add DB connection pooling.
* Add async model scoring / queued payments for scale.
* Improve feature engineering with richer session/device signals.
* Add admin-level merchant risk tuning and explainability (SHAP).
* Rate-limit auth endpoints and add CAPTCHA.
* Add end-to-end tests for the React UI (e.g., Playwright).

---

## License
Educational / college project. Use freely for learning.
