"""Fraud detection service: feature-mapping layer + model scoring.

This is the bridge between SecurePay's domain objects (Customer, Merchant,
Wallet, Payment history) and the ML model's 12-feature input vector.

SecurePay Payment context  ->  Feature Engineering  ->  ML features  ->  Model
"""

from datetime import datetime, timezone

from app.extensions import db
from app.models.payment import Payment
from ml.predict import predict as ml_predict
from config import Config


def build_feature_context(customer, merchant, amount, db_session=None,
                          location_change=0, device_change=0):
    """Construct the 12-feature ML vector from SecurePay database context."""
    session = db_session or db.session
    # SQLite stores timestamps without tz info, so use naive UTC for arithmetic.
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Customer history
    if customer.created_at:
        account_age_days = max(1, (now - customer.created_at).days)
    else:
        account_age_days = 365

    prior_payments = (
        session.query(Payment)
        .filter_by(customer_id=customer.customer_id)
        .all()
    )
    successful = [p for p in prior_payments if p.status == "success"]
    rejected = [p for p in prior_payments if p.status in ("failed", "rejected")]

    previous_transaction_count = len(successful)
    failed_transaction_count = len(rejected)
    previous_fraud_count = len([p for p in prior_payments if p.fraud_flag is True])

    if successful:
        average_transaction_amount = sum(p.amount for p in successful) / len(successful)
    else:
        average_transaction_amount = 0.0

    # Frequency: number of THIS customer's payments in the last 24h.
    day_ago = now.timestamp() - 24 * 3600
    transaction_frequency = sum(
        1 for p in prior_payments
        if p.payment_date and p.payment_date.timestamp() >= day_ago
    )

    transaction_hour = now.hour
    customer_age = customer.customer_age or 30
    merchant_risk = float(merchant.merchant_risk) if merchant.merchant_risk is not None else 0.1

    return {
        "transaction_amount": float(amount),
        "transaction_hour": int(transaction_hour),
        "transaction_frequency": int(transaction_frequency),
        "customer_age": float(customer_age),
        "account_age": float(account_age_days),
        "previous_transaction_count": int(previous_transaction_count),
        "average_transaction_amount": float(average_transaction_amount),
        "merchant_risk": float(merchant_risk),
        "failed_transaction_count": int(failed_transaction_count),
        "location_change": int(location_change),
        "device_change": int(device_change),
        "previous_fraud_count": int(previous_fraud_count),
    }


def score_payment(customer, merchant, amount, location_change=0, device_change=0,
                  threshold=None):
    """Run the ML model on a payment and return the fraud decision."""
    threshold = threshold if threshold is not None else Config.FRAUD_THRESHOLD
    context = build_feature_context(
        customer, merchant, amount,
        location_change=location_change, device_change=device_change,
    )
    result = ml_predict(context, threshold=threshold)
    result["feature_context"] = context
    return result
