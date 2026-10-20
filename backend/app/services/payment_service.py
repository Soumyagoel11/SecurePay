"""Payment orchestration service.

Enforces the required workflow: validate -> check balance -> ML fraud check ->
(safe) deduct wallet & record / (suspicious) reject without moving money.
All DB writes for a single payment happen inside one session so a failed payment
never partially modifies balances.
"""

from app.extensions import db
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.wallet import Wallet
from app.models.payment import Payment
from app.models.transaction import Transaction
from app.models.fraud_detection import FraudDetection
from app.services.fraud_service import score_payment
from app.utils.logger import get_logger, log_event

logger = get_logger()


def _update_merchant_risk(merchant_id: int):
    payments = Payment.query.filter_by(merchant_id=merchant_id).all()
    if not payments:
        return
    flagged = sum(1 for p in payments if p.fraud_flag is True)
    risk = flagged / len(payments)
    merchant = db.session.get(Merchant, merchant_id)
    if merchant:
        merchant.merchant_risk = round(risk, 3)


def process_payment(customer_id, merchant_id, amount, location_change=0, device_change=0):
    """Process a payment end-to-end. Returns a result dict on success.

    Raises ValueError with a user-friendly message on validation failure.
    """
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number")

    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero")

    customer = db.session.get(Customer, customer_id)
    if customer is None:
        raise ValueError("Customer not found")
    merchant = db.session.get(Merchant, merchant_id)
    if merchant is None:
        raise ValueError("Merchant not found")
    wallet = Wallet.query.filter_by(customer_id=customer_id).first()
    if wallet is None:
        raise ValueError("Wallet not found")
    if wallet.status != "active":
        raise ValueError("Wallet is frozen and cannot be used")
    if float(wallet.balance) < amount:
        raise ValueError("Insufficient wallet balance")

    # Create the payment record first (pending) so we can attach fraud metadata.
    payment = Payment(
        customer_id=customer_id, merchant_id=merchant_id,
        amount=amount, status="pending",
    )
    db.session.add(payment)
    db.session.flush()  # assign payment_id without committing yet

    # --- ML fraud detection (no money moved yet) ---
    fraud_result = score_payment(
        customer, merchant, amount,
        location_change=location_change, device_change=device_change,
    )
    risk_score = fraud_result["risk_score"]
    fraud_flag = fraud_result["fraud_flag"]
    decision = fraud_result["prediction"]

    fd = FraudDetection(
        payment_id=payment.payment_id,
        prediction=decision,
        risk_score=risk_score,
        model_version=fraud_result.get("model_version"),
        model_name=fraud_result.get("model_name"),
    )
    db.session.add(fd)

    log_event(logger, "fraud_check", payment_id=payment.payment_id,
              risk_score=risk_score, fraud_flag=fraud_flag, model=fraud_result.get("model_name"))

    if fraud_flag:
        # Suspicious -> reject, do NOT deduct money.
        payment.status = "rejected"
        payment.risk_score = risk_score
        payment.fraud_flag = True
        payment.fraud_decision = decision
        payment.failure_reason = "Flagged as suspicious by fraud detection model"
        db.session.commit()
        log_event(logger, "payment_rejected", payment_id=payment.payment_id,
                  customer_id=customer_id, merchant_id=merchant_id, amount=amount)
        return {
            "status": "rejected",
            "message": "Payment rejected: suspicious activity detected",
            "payment": payment.to_dict(),
            "fraud": fraud_result,
        }

    # Safe -> deduct wallet and record the transaction atomically.
    wallet.balance = float(wallet.balance) - amount
    txn = Transaction(
        payment_id=payment.payment_id,
        wallet_id=wallet.wallet_id,
        type="debit",
        amount=amount,
        status="completed",
        description=f"Payment to {merchant.company_name}",
    )
    db.session.add(txn)
    payment.status = "success"
    payment.risk_score = risk_score
    payment.fraud_flag = False
    payment.fraud_decision = decision

    _update_merchant_risk(merchant_id)

    db.session.commit()
    log_event(logger, "payment_success", payment_id=payment.payment_id,
              customer_id=customer_id, merchant_id=merchant_id, amount=amount)
    return {
        "status": "success",
        "message": "Payment processed successfully",
        "payment": payment.to_dict(),
        "fraud": fraud_result,
    }
