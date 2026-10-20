"""Refund model: customer refund requests reviewed by admin."""

from datetime import datetime, timezone

from app.extensions import db


class Refund(db.Model):
    __tablename__ = "refunds"

    refund_id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(
        db.Integer, db.ForeignKey("payments.payment_id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,  # one refund per payment
    )
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customers.customer_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="pending", nullable=False)
    # status: pending | approved | rejected
    admin_id = db.Column(
        db.Integer, db.ForeignKey("admins.admin_id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self, payment=None, customer=None):
        return {
            "refund_id": self.refund_id,
            "payment_id": self.payment_id,
            "customer_id": self.customer_id,
            "amount": round(float(self.amount), 2),
            "reason": self.reason,
            "status": self.status,
            "admin_id": self.admin_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "payment": payment,
            "customer": customer,
        }
