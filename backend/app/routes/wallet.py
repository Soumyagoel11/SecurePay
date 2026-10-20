"""Wallet routes: view balance, add demo money, view transactions."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User
from app.models.customer import Customer
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.middleware import require_role
from app.utils.response import success, error
from app.utils.logger import get_logger, log_event

logger = get_logger()
wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("", methods=["GET"])
@jwt_required()
@require_role("customer")
def get_wallet():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    customer = user.customer
    wallet = Wallet.query.filter_by(customer_id=customer.customer_id).first()
    if not wallet:
        return error("Wallet not found", 404)
    return success("OK", {"wallet": wallet.to_dict()})


@wallet_bp.route("/add-money", methods=["POST"])
@jwt_required()
@require_role("customer")
def add_money():
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return error("Amount must be a number", 400)
    if amount <= 0:
        return error("Amount must be greater than zero", 400)
    if amount > 100000:
        return error("Demo deposits are limited to 100000", 400)

    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    wallet = Wallet.query.filter_by(customer_id=user.customer.customer_id).first()
    if not wallet:
        return error("Wallet not found", 404)

    wallet.balance = float(wallet.balance) + amount
    txn = Transaction(
        wallet_id=wallet.wallet_id, type="add_money",
        amount=amount, status="completed", description="Demo wallet top-up",
    )
    db.session.add(txn)
    db.session.commit()
    log_event(logger, "wallet_add_money", user_id=user.user_id, amount=amount)
    return success("Money added", {"wallet": wallet.to_dict()}, 200)


@wallet_bp.route("/transactions", methods=["GET"])
@jwt_required()
@require_role("customer")
def wallet_transactions():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    wallet = Wallet.query.filter_by(customer_id=user.customer.customer_id).first()
    if not wallet:
        return error("Wallet not found", 404)
    txns = (
        Transaction.query.filter_by(wallet_id=wallet.wallet_id)
        .order_by(Transaction.timestamp.desc()).limit(100).all()
    )
    return success("OK", {"transactions": [t.to_dict() for t in txns]})
