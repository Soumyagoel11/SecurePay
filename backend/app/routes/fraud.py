"""Fraud detection routes: standalone prediction + fraud reports."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.fraud_detection import FraudDetection
from app.middleware import require_role
from app.services.fraud_service import build_feature_context, score_payment
from app.utils.response import success, error
from config import Config

fraud_bp = Blueprint("fraud", __name__)


@fraud_bp.route("/predict", methods=["POST"])
@jwt_required()
def predict():
    data = request.get_json(silent=True) or {}

    # Option A: explicit feature vector supplied (research / testing use).
    if "features" in data and isinstance(data["features"], dict):
        from ml.predict import predict as ml_predict
        try:
            result = ml_predict(data["features"], threshold=Config.FRAUD_THRESHOLD)
        except Exception as e:
            return error(f"Prediction failed: {e}", 400)
        return success("Prediction complete", result)

    # Option B: build features from a real SecurePay context.
    if "merchant_id" not in data or "amount" not in data:
        return error("Provide 'features' or 'merchant_id' and 'amount'", 400)
    user = db.session.get(User, int(get_jwt_identity()))
    if user.role != "customer":
        return error("Only customers can score a payment context", 403)
    merchant = db.session.get(Merchant, int(data["merchant_id"]))
    if not merchant:
        return error("Merchant not found", 404)
    try:
        result = score_payment(
            user.customer, merchant, float(data["amount"]),
            location_change=int(data.get("location_change", 0) or 0),
            device_change=int(data.get("device_change", 0) or 0),
        )
    except ValueError as e:
        return error(str(e), 400)
    return success("Prediction complete", result)


@fraud_bp.route("/reports", methods=["GET"])
@jwt_required()
def fraud_reports():
    user = db.session.get(User, int(get_jwt_identity()))
    query = FraudDetection.query.join(Payment, Payment.payment_id == FraudDetection.payment_id)
    if user.role == "merchant":
        query = query.filter(Payment.merchant_id == user.merchant.merchant_id)
    elif user.role == "customer":
        query = query.filter(Payment.customer_id == user.customer.customer_id)
    # admin -> all
    reports = query.order_by(FraudDetection.created_at.desc()).limit(200).all()
    out = []
    for r in reports:
        d = r.to_dict()
        p = db.session.get(Payment, r.payment_id)
        d["payment"] = p.to_dict() if p else None
        out.append(d)
    return success("OK", {"reports": out})
