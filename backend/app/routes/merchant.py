"""Merchant routes: dashboard, profile, suspicious transactions."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app.extensions import db
from app.models.user import User
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.fraud_detection import FraudDetection
from app.middleware import require_role
from app.utils.response import success, error

merchant_bp = Blueprint("merchant", __name__)


@merchant_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@require_role("merchant")
def dashboard():
    user = db.session.get(User, int(get_jwt_identity()))
    mid = user.merchant.merchant_id

    total_payments = Payment.query.filter_by(merchant_id=mid).count()
    successful = Payment.query.filter_by(merchant_id=mid, status="success").count()
    suspicious = Payment.query.filter_by(merchant_id=mid, fraud_flag=True).count()
    revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0.0)).filter_by(
        merchant_id=mid, status="success"
    ).scalar()

    recent = (
        Payment.query.filter_by(merchant_id=mid)
        .order_by(Payment.payment_date.desc()).limit(10).all()
    )
    stats = {
        "total_revenue": round(float(revenue), 2),
        "total_payments": total_payments,
        "successful_payments": successful,
        "suspicious_payments": suspicious,
    }
    return success("OK", {
        "stats": stats,
        "recent_transactions": [p.to_dict() for p in recent],
    })


@merchant_bp.route("/profile", methods=["GET"])
@jwt_required()
@require_role("merchant")
def profile():
    user = db.session.get(User, int(get_jwt_identity()))
    return success("OK", {"merchant": user.merchant.to_dict(), "user": user.to_dict()})


@merchant_bp.route("/suspicious", methods=["GET"])
@jwt_required()
@require_role("merchant")
def suspicious():
    user = db.session.get(User, int(get_jwt_identity()))
    mid = user.merchant.merchant_id
    rows = (
        FraudDetection.query.join(Payment, Payment.payment_id == FraudDetection.payment_id)
        .filter(Payment.merchant_id == mid, Payment.fraud_flag == True)  # noqa: E712
        .order_by(FraudDetection.created_at.desc()).limit(200).all()
    )
    out = []
    for r in rows:
        d = r.to_dict()
        p = db.session.get(Payment, r.payment_id)
        d["payment"] = p.to_dict() if p else None
        out.append(d)
    return success("OK", {"suspicious": out})
