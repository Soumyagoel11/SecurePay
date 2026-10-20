"""Wallet model: customer's digital balance."""

from app.extensions import db


class Wallet(db.Model):
    __tablename__ = "wallets"

    wallet_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customers.customer_id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    balance = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False)  # active | frozen

    def to_dict(self):
        return {
            "wallet_id": self.wallet_id,
            "customer_id": self.customer_id,
            "balance": round(float(self.balance), 2),
            "status": self.status,
        }
