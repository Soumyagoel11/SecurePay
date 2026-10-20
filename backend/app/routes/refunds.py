"""Refund routes: request, list, approve, reject."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User
from app.models.customer import Customer
from app.models.wallet import Wallet
from app.models.payment import Payment
from app.models.transaction import Transaction
from app.models.refund import Refund
from app.middleware import require_role
from app.utils.response import success, error
from app.utils.logger import get_logger, log_event

logger = get_logger()
refunds_bp = Blueprint("refunds", __name__)


@refunds_bp.route("", methods=["POST"])
@jwt_required()
@require_role("customer")
def request_refund():
    data = request.get_json(silent=True) or {}
    try:
        payment_id = int(data.get("payment_id"))
    except (TypeError, ValueError):
        return error("payment_id is required and must be numeric", 400)
    reason = (data.get("reason") or "").strip()

    user = db.session.get(User, int(get_jwt_identity()))
    payment = db.session.get(Payment, payment_id)
    if not payment:
        return error("Payment not found", 404)
    if payment.customer_id != user.customer.customer_id:
        return error("Forbidden: not your payment", 403)
    if payment.status != "success":
        return error("Only successful payments can be refunded", 409)

    existing = Refund.query.filter_by(payment_id=payment_id).first()
    if existing:
        return error("This payment has already been refunded or has a pending request", 409)

    refund = Refund(
        payment_id=payment_id,
        customer_id=user.customer.customer_id,
        amount=float(payment.amount),
        reason=reason or "No reason provided",
        status="pending",
    )
    db.session.add(refund)
    db.session.commit()
    log_event(logger, "refund_requested", payment_id=payment_id,
              customer_id=user.customer.customer_id, amount=refund.amount)
    return success("Refund request submitted", {"refund": refund.to_dict()}, 201)


@refunds_bp.route("", methods=["GET"])
@jwt_required()
def list_refunds():
    user = db.session.get(User, int(get_jwt_identity()))
    query = Refund.query
    if user.role == "customer":
        query = query.filter_by(customer_id=user.customer.customer_id)
    elif user.role == "merchant":
        # merchants see refunds on their payments
        query = query.join(Payment, Payment.payment_id == Refund.payment_id).filter(
            Payment.merchant_id == user.merchant.merchant_id
        )
    refunds = query.order_by(Refund.created_at.desc()).limit(200).all()
    out = []
    for r in refunds:
        d = r.to_dict()
        p = db.session.get(Payment, r.payment_id)
        d["payment"] = p.to_dict() if p else None
        out.append(d)
    return success("OK", {"refunds": out})


@refunds_bp.route("/<int:refund_id>/approve", methods=["PUT"])
@jwt_required()
@require_role("admin")
def approve_refund(refund_id):
    user = db.session.get(User, int(get_jwt_identity()))
    refund = db.session.get(Refund, refund_id)
    if not refund:
        return error("Refund not found", 404)
    if refund.status != "pending":
        return error("Refund is not pending", 409)

    payment = db.session.get(Payment, refund.payment_id)
    wallet = Wallet.query.filter_by(customer_id=refund.customer_id).first()
    if not wallet:
        return error("Customer wallet not found", 404)

    # Credit the refund back to the customer's wallet.
    wallet.balance = float(wallet.balance) + float(refund.amount)
    txn = Transaction(
        wallet_id=wallet.wallet_id, payment_id=payment.payment_id,
        type="refund", amount=float(refund.amount),
        status="completed", description="Refund credited to wallet",
    )
    db.session.add(txn)
    payment.status = "refunded"
    refund.status = "approved"
    refund.admin_id = user.admin.admin_id
    refund.resolved_at = db.func.now()
    db.session.commit()
    log_event(logger, "refund_approved", refund_id=refund_id,
              admin_id=user.admin.admin_id, amount=refund.amount)
    return success("Refund approved", {"refund": refund.to_dict()})


@refunds_bp.route("/<int:refund_id>/reject", methods=["PUT"])
@jwt_required()
@require_role("admin")
def reject_refund(refund_id):
    user = db.session.get(User, int(get_jwt_identity()))
    refund = db.session.get(Refund, refund_id)
    if not refund:
        return error("Refund not found", 404)
    if refund.status != "pending":
        return error("Refund is not pending", 409)
    refund.status = "rejected"
    refund.admin_id = user.admin.admin_id
    refund.resolved_at = db.func.now()
    db.session.commit()
    log_event(logger, "refund_rejected", refund_id=refund_id,
              admin_id=user.admin.admin_id)
    return success("Refund rejected", {"refund": refund.to_dict()})
