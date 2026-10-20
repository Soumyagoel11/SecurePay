"""Transaction model: ledger entries for wallet movements (credit/debit)."""

from datetime import datetime, timezone

from app.extensions import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    transaction_id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(
        db.Integer, db.ForeignKey("payments.payment_id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    wallet_id = db.Column(
        db.Integer, db.ForeignKey("wallets.wallet_id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    type = db.Column(db.String(20), nullable=False)  # debit | credit | refund | add_money
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="completed", nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    description = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "payment_id": self.payment_id,
            "wallet_id": self.wallet_id,
            "type": self.type,
            "amount": round(float(self.amount), 2),
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "description": self.description,
        }
