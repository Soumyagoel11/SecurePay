"""Payment routes: create, list, and view payments (+ fraud metadata)."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.transaction import Transaction
from app.models.fraud_detection import FraudDetection
from app.middleware import require_role
from app.services.payment_service import process_payment
from app.utils.response import success, error
from app.utils.logger import get_logger

logger = get_logger()
payments_bp = Blueprint("payments", __name__)


@payments_bp.route("", methods=["POST"])
@jwt_required()
@require_role("customer")
def create_payment():
    data = request.get_json(silent=True) or {}
    try:
        merchant_id = int(data.get("merchant_id"))
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return error("merchant_id and amount are required and must be numeric", 400)

    location_change = int(data.get("location_change", 0) or 0)
    device_change = int(data.get("device_change", 0) or 0)

    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    try:
        result = process_payment(
            customer_id=user.customer.customer_id,
            merchant_id=merchant_id,
            amount=amount,
            location_change=location_change,
            device_change=device_change,
        )
    except ValueError as e:
        return error(str(e), 400)

    return success(result["message"], result, 200)


@payments_bp.route("", methods=["GET"])
@jwt_required()
def list_payments():
    user = db.session.get(User, int(get_jwt_identity()))
    query = Payment.query
    if user.role == "customer":
        query = query.filter_by(customer_id=user.customer.customer_id)
    elif user.role == "merchant":
        query = query.filter_by(merchant_id=user.merchant.merchant_id)
    # admin -> all
    payments = query.order_by(Payment.payment_date.desc()).limit(200).all()
    return success("OK", {"payments": [p.to_dict() for p in payments]})


@payments_bp.route("/<int:payment_id>", methods=["GET"])
@jwt_required()
def payment_detail(payment_id):
    user = db.session.get(User, int(get_jwt_identity()))
    payment = db.session.get(Payment, payment_id)
    if not payment:
        return error("Payment not found", 404)

    # Authorization: customer owns it, merchant receives it, or admin.
    if user.role == "customer" and payment.customer_id != user.customer.customer_id:
        return error("Forbidden", 403)
    if user.role == "merchant" and payment.merchant_id != user.merchant.merchant_id:
        return error("Forbidden", 403)

    fraud = FraudDetection.query.filter_by(payment_id=payment.payment_id).first()
    txns = Transaction.query.filter_by(payment_id=payment.payment_id).all()
    data = payment.to_dict()
    data["fraud"] = fraud.to_dict() if fraud else None
    data["transactions"] = [t.to_dict() for t in txns]
    return success("OK", data)
