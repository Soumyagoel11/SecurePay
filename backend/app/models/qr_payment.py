"""QR Payment model: QR-based checkout sessions."""

from datetime import datetime, timezone
from app.extensions import db


class QRPayment(db.Model):
    __tablename__ = "qr_payments"

    qr_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    merchant_id = db.Column(
        db.Integer, db.ForeignKey("merchants.merchant_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customers.customer_id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_id = db.Column(
        db.Integer, db.ForeignKey("payments.payment_id", ondelete="SET NULL"),
        nullable=True,
    )
    amount = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.String(255), nullable=True, default="QR Payment")
    status = db.Column(db.String(30), nullable=False, default="pending")
    # status: pending | completed | rejected | expired
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)

    merchant = db.relationship("Merchant", backref=db.backref("qr_payments", lazy=True))
    customer = db.relationship("Customer", backref=db.backref("qr_payments", lazy=True))
    payment = db.relationship("Payment", backref=db.backref("qr_payment", uselist=False, lazy=True))

    def is_expired(self):
        if not self.expires_at:
            return False
        # Normalize to naive or timezone-aware
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp

    def to_dict(self):
        m_name = self.merchant.company_name if self.merchant else None
        m_type = self.merchant.business_type if self.merchant else None
        return {
            "qr_id": self.qr_id,
            "token": self.token,
            "merchant_id": self.merchant_id,
            "merchant_name": m_name,
            "merchant_type": m_type,
            "customer_id": self.customer_id,
            "payment_id": self.payment_id,
            "amount": round(float(self.amount), 2),
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired(),
        }
