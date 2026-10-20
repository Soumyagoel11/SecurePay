"""Payment model: a customer-to-merchant payment with fraud metadata."""

from datetime import datetime, timezone

from app.extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    payment_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customers.customer_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    merchant_id = db.Column(
        db.Integer, db.ForeignKey("merchants.merchant_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status = db.Column(db.String(20), default="pending", nullable=False)
    # status: pending | success | failed | rejected | refunded
    risk_score = db.Column(db.Float, nullable=True)
    fraud_flag = db.Column(db.Boolean, nullable=True)
    fraud_decision = db.Column(db.String(20), nullable=True)  # Safe | Suspicious
    failure_reason = db.Column(db.String(255), nullable=True)

    def to_dict(self, customer=None, merchant=None):
        return {
            "payment_id": self.payment_id,
            "customer_id": self.customer_id,
            "merchant_id": self.merchant_id,
            "amount": round(float(self.amount), 2),
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "status": self.status,
            "risk_score": self.risk_score,
            "fraud_flag": self.fraud_flag,
            "fraud_decision": self.fraud_decision,
            "failure_reason": self.failure_reason,
            "customer": customer,
            "merchant": merchant,
        }
