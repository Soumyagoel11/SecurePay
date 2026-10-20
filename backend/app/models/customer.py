"""Customer profile model (extends User)."""

from datetime import datetime, timezone

from app.extensions import db
from app.models.user import User


class Customer(db.Model):
    __tablename__ = "customers"

    customer_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    customer_age = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("customer", uselist=False))

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "user_id": self.user_id,
            "phone": self.phone,
            "address": self.address,
            "customer_age": self.customer_age,
            "email": self.user.email if self.user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
