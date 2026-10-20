"""Customer routes: dashboard, profile, merchant directory."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app.extensions import db
from app.models.user import User
from app.models.customer import Customer
from app.models.wallet import Wallet
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.middleware import require_role
from app.utils.response import success, error

customer_bp = Blueprint("customer", __name__)


@customer_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@require_role("customer")
def dashboard():
    user = db.session.get(User, int(get_jwt_identity()))
    cid = user.customer.customer_id
    wallet = Wallet.query.filter_by(customer_id=cid).first()

    total = Payment.query.filter_by(customer_id=cid).count()
    successful = Payment.query.filter_by(customer_id=cid, status="success").count()
    failed = Payment.query.filter(Payment.customer_id == cid,
                                 Payment.status.in_(["failed", "rejected"])).count()
    recent = (
        Payment.query.filter_by(customer_id=cid)
        .order_by(Payment.payment_date.desc()).limit(10).all()
    )
    stats = {
        "wallet_balance": round(float(wallet.balance), 2) if wallet else 0.0,
        "total_payments": total,
        "successful_payments": successful,
        "failed_payments": failed,
        "wallet_status": wallet.status if wallet else "none",
    }
    return success("OK", {
        "stats": stats,
        "recent_transactions": [p.to_dict() for p in recent],
    })


@customer_bp.route("/merchants", methods=["GET"])
@jwt_required()
@require_role("customer")
def list_merchants():
    merchants = Merchant.query.all()
    return success("OK", {"merchants": [m.to_dict() for m in merchants]})


@customer_bp.route("/profile", methods=["GET"])
@jwt_required()
@require_role("customer")
def profile():
    user = db.session.get(User, int(get_jwt_identity()))
    wallet = Wallet.query.filter_by(customer_id=user.customer.customer_id).first()
    return success("OK", {
        "customer": user.customer.to_dict(),
        "user": user.to_dict(),
        "wallet": wallet.to_dict() if wallet else None,
    })
