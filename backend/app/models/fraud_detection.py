"""FraudDetection model: persisted ML fraud decision for each payment."""

from datetime import datetime, timezone

from app.extensions import db


class FraudDetection(db.Model):
    __tablename__ = "fraud_detections"

    fraud_id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(
        db.Integer, db.ForeignKey("payments.payment_id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    prediction = db.Column(db.String(20), nullable=False)  # Safe | Suspicious
    risk_score = db.Column(db.Float, nullable=False)
    model_version = db.Column(db.String(50), nullable=True)
    model_name = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "fraud_id": self.fraud_id,
            "payment_id": self.payment_id,
            "prediction": self.prediction,
            "risk_score": self.risk_score,
            "model_version": self.model_version,
            "model_name": self.model_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
