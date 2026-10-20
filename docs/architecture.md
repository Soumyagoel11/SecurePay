# SecurePay Architecture & Fraud Flow

## High-level flow

```
Customer Login
   ↓
Customer Dashboard (wallet balance, stats)
   ↓
Select Merchant  →  Enter Amount
   ↓
[Backend validation]
   • merchant exists?                 → 400 if not
   • amount > 0?                      → 400 if not
   • wallet exists & active?          → 400 if not
   • wallet balance >= amount?        → 400 "Insufficient wallet balance"
   ↓
Generate Payment record (status = pending)   ← NO money moved yet
   ↓
Build 12-feature vector (feature-mapping layer)
   from Customer / Merchant / Wallet / history
   ↓
ML Model (RandomForest) → predict_proba
   ↓
risk_score (0–1)  →  fraud_flag = (risk_score >= FRAUD_THRESHOLD)
   ↓
Store FraudDetection(payment_id, prediction, risk_score, model_version)
   ↓
┌─────────────────────┬──────────────────────────────────────────┐
│ fraud_flag = False  │ fraud_flag = True                        │
│ (Safe)              │ (Suspicious)                             │
│                      │                                          │
│ • deduct wallet       │ • payment status = "rejected"           │
│ • create Transaction  │ • NO balance change                     │
│   (debit, completed)  │ • log fraud result                      │
│ • payment status =    │                                          │
│   "success"           │                                          │
│ • update merchant_risk│                                          │
└─────────────────────┴──────────────────────────────────────────┘
   ↓
Return result to frontend (status, fraud decision, risk score)
```

## Why money is never deducted before checks
The wallet balance is only decremented **after** the ML decision returns
`Safe`. Both the payment status update and the wallet/transaction writes happen
inside a single SQLAlchemy session (`process_payment` in
`app/services/payment_service.py`), so a failure at any step rolls back and never
partially modifies balances.

## Feature-mapping layer
`app/services/fraud_service.py::build_feature_context` translates SecurePay's
domain objects into the model's 12-feature input:

| SecurePay source | ML feature |
| --- | --- |
| `payment.amount` | `transaction_amount` |
| `now.hour` | `transaction_hour` |
| count of customer txns in last 24h | `transaction_frequency` |
| `customer.customer_age` | `customer_age` |
| days since `customer.created_at` | `account_age` |
| prior successful payments | `previous_transaction_count` |
| mean prior successful amount | `average_transaction_amount` |
| `merchant.merchant_risk` (dyn. fraud rate) | `merchant_risk` |
| prior failed/rejected payments | `failed_transaction_count` |
| request flag | `location_change` |
| request flag | `device_change` |
| prior flagged payments | `previous_fraud_count` |

The same 12 feature names are used at training time (`ml/features.py`), so the
model trained on the dataset is fed the exact same vector at inference.

## Model selection
* Logistic Regression vs Random Forest, compared by **F1-score**.
* Threshold `FRAUD_THRESHOLD` (env var, default 0.5) controls the Safe/Suspicious
  boundary and is never hardcoded in business logic.
* Risk score, prediction, and fraud flag are persisted in `fraud_detections`.
