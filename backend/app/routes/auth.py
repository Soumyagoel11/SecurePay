"""Authentication routes: register, login, current user."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt,
)
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.user import User
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.admin import Admin
from app.models.wallet import Wallet
from app.utils.response import success, error
from app.utils.logger import get_logger, log_event

logger = get_logger()
auth_bp = Blueprint("auth", __name__)

VALID_ROLES = {"customer", "merchant", "admin"}


def _create_role_profile(user, data):
    if user.role == "customer":
        cust = Customer(
            user_id=user.user_id,
            phone=data.get("phone"),
            address=data.get("address"),
            customer_age=data.get("customer_age"),
        )
        db.session.add(cust)
        db.session.flush()  # assign customer_id before creating the wallet
        wallet = Wallet(
            customer_id=cust.customer_id,
            balance=float(data.get("initial_balance", 0.0)),
        )
        db.session.add(wallet)
    elif user.role == "merchant":
        merch = Merchant(
            user_id=user.user_id,
            company_name=data.get("company_name", "Unnamed Merchant"),
            business_type=data.get("business_type"),
            merchant_risk=0.1,
        )
        db.session.add(merch)
    elif user.role == "admin":
        adm = Admin(
            user_id=user.user_id,
            department=data.get("department", "Operations"),
        )
        db.session.add(adm)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "").strip().lower()

    if not email or not password:
        return error("Email and password are required", 400)
    if role not in VALID_ROLES:
        return error("Role must be one of: customer, merchant, admin", 400)
    if len(password) < 6:
        return error("Password must be at least 6 characters", 400)
    if User.query.filter_by(email=email).first():
        return error("Email already registered", 409)

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.flush()
    _create_role_profile(user, data)
    db.session.commit()

    token = create_access_token(
        identity=str(user.user_id),
        additional_claims={"role": user.role, "email": user.email},
    )
    return success("Registration successful", {
        "access_token": token,
        "user": user.to_dict(),
    }, 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if user is None or not check_password_hash(user.password_hash, password):
        log_event(logger, "login_failed", email=email)
        return error("Invalid email or password", 401)

    token = create_access_token(
        identity=str(user.user_id),
        additional_claims={"role": user.role, "email": user.email},
    )
    log_event(logger, "login_success", user_id=user.user_id, role=user.role)
    return success("Login successful", {
        "access_token": token,
        "user": user.to_dict(),
    })


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = get_jwt_identity()
    db_user = db.session.get(User, int(user))
    if not db_user:
        return error("User not found", 404)
    profile = None
    if db_user.role == "customer" and db_user.customer:
        profile = db_user.customer.to_dict()
    elif db_user.role == "merchant" and db_user.merchant:
        profile = db_user.merchant.to_dict()
    elif db_user.role == "admin" and db_user.admin:
        profile = db_user.admin.to_dict()
    return success("OK", {"user": db_user.to_dict(), "profile": profile})
