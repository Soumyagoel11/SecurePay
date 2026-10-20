"""Merchant profile model (extends User)."""

from app.extensions import db
from app.models.user import User


class Merchant(db.Model):
    __tablename__ = "merchants"

    merchant_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    company_name = db.Column(db.String(255), nullable=False)
    business_type = db.Column(db.String(100), nullable=True)
    # Historical fraud rate derived from flagged payments (0.0 - 1.0).
    merchant_risk = db.Column(db.Float, default=0.1, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User", backref=db.backref("merchant", uselist=False))

    def to_dict(self):
        return {
            "merchant_id": self.merchant_id,
            "user_id": self.user_id,
            "company_name": self.company_name,
            "business_type": self.business_type,
            "merchant_risk": self.merchant_risk,
            "email": self.user.email if self.user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
