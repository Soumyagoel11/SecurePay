"""Admin routes: dashboard statistics, user/merchant/transaction management."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.transaction import Transaction
from app.models.fraud_detection import FraudDetection
from app.models.refund import Refund
from app.middleware import require_role
from app.utils.response import success, error

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@require_role("admin")
def dashboard():
    total_users = User.query.count()
    total_customers = Customer.query.count()
    total_merchants = Merchant.query.count()
    total_transactions = Payment.query.count()
    successful = Payment.query.filter_by(status="success").count()
    suspicious = Payment.query.filter_by(fraud_flag=True).count()
    pending_refunds = Refund.query.filter_by(status="pending").count()
    total_refunds = Refund.query.count()

    stats = {
        "total_users": total_users,
        "total_customers": total_customers,
        "total_merchants": total_merchants,
        "total_transactions": total_transactions,
        "successful_payments": successful,
        "suspicious_transactions": suspicious,
        "pending_refund_requests": pending_refunds,
        "total_refunds": total_refunds,
    }
    return success("OK", {"stats": stats})


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@require_role("admin")
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return success("OK", {"users": [u.to_dict() for u in users]})


@admin_bp.route("/customers", methods=["GET"])
@jwt_required()
@require_role("admin")
def list_customers():
    customers = Customer.query.all()
    return success("OK", {"customers": [c.to_dict() for c in customers]})


@admin_bp.route("/merchants", methods=["GET"])
@jwt_required()
@require_role("admin")
def list_merchants():
    merchants = Merchant.query.all()
    return success("OK", {"merchants": [m.to_dict() for m in merchants]})


@admin_bp.route("/transactions", methods=["GET"])
@jwt_required()
@require_role("admin")
def list_transactions():
    payments = Payment.query.order_by(Payment.payment_date.desc()).limit(300).all()
    out = []
    for p in payments:
        d = p.to_dict()
        d["customer"] = p.customer.to_dict() if p.customer else None
        d["merchant"] = p.merchant.to_dict() if p.merchant else None
        out.append(d)
    return success("OK", {"transactions": out})


@admin_bp.route("/fraud-reports", methods=["GET"])
@jwt_required()
@require_role("admin")
def fraud_reports():
    reports = FraudDetection.query.order_by(FraudDetection.created_at.desc()).limit(300).all()
    out = []
    for r in reports:
        d = r.to_dict()
        p = db.session.get(Payment, r.payment_id)
        d["payment"] = p.to_dict() if p else None
        out.append(d)
    return success("OK", {"reports": out})


@admin_bp.route("/refunds", methods=["GET"])
@jwt_required()
@require_role("admin")
def list_refunds():
    refunds = Refund.query.order_by(Refund.created_at.desc()).limit(300).all()
    out = []
    for r in refunds:
        d = r.to_dict()
        p = db.session.get(Payment, r.payment_id)
        d["payment"] = p.to_dict() if p else None
        out.append(d)
    return success("OK", {"refunds": out})
