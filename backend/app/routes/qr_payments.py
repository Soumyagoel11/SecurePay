"""QR Payment routes: dynamic and static QR generation, scanning, and checkout."""

import os
import io
import base64
import uuid
import socket
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.models.user import User
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.wallet import Wallet
from app.models.fraud_detection import FraudDetection
from app.models.qr_payment import QRPayment
from app.middleware import require_role
from app.services.payment_service import process_payment
from app.utils.response import success, error
from app.utils.logger import get_logger, log_event

logger = get_logger()
qr_bp = Blueprint("qr_payments", __name__)


def _get_lan_ip():
    """Detect the local machine's LAN IP address for phone/Google Lens scanning."""
    ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    return ip


def _generate_qr_base64(data_string: str) -> str:
    """Generate a high-contrast QR code PNG encoded as base64 data URL."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.warning(f"Could not generate QR base64: {e}")
        return ""


@qr_bp.route("/network-info", methods=["GET"])
def get_network_info():
    """Return local network IP and port info for generating scannable QR URLs."""
    lan_ip = _get_lan_ip()
    return success("OK", {
        "lan_ip": lan_ip,
        "frontend_port": 3000,
        "backend_port": 5000,
        "lan_url_base": f"http://{lan_ip}:3000",
    })


@qr_bp.route("/demo-customers", methods=["GET"])
def list_demo_customers():
    """List available demo customers to facilitate 1-tap mobile Google Lens testing."""
    customers = Customer.query.all()
    results = []
    for c in customers:
        user = c.user
        wallet = Wallet.query.filter_by(customer_id=c.customer_id).first()
        results.append({
            "customer_id": c.customer_id,
            "email": user.email if user else f"customer{c.customer_id}@securepay.com",
            "balance": round(float(wallet.balance), 2) if wallet else 0.0,
            "phone": c.phone,
            "age": c.customer_age,
        })
    return success("OK", {"customers": results})


@qr_bp.route("/create", methods=["POST"])
@jwt_required()
@require_role("merchant")
def create_qr_session():
    """Create a new dynamic QR payment session for a merchant."""
    user = db.session.get(User, int(get_jwt_identity()))
    merchant = user.merchant
    if not merchant:
        return error("Merchant profile not found", 404)

    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount", 0.0))
    except (TypeError, ValueError):
        return error("Amount must be numeric", 400)

    if amount < 0:
        return error("Amount cannot be negative", 400)

    description = (data.get("description") or f"Payment to {merchant.company_name}").strip()
    expires_in_minutes = int(data.get("expires_in_minutes", 15))
    host_override = (data.get("host_base") or "").strip()

    token = uuid.uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

    qr = QRPayment(
        token=token,
        merchant_id=merchant.merchant_id,
        amount=amount,
        description=description,
        status="pending",
        expires_at=expires_at,
    )
    db.session.add(qr)
    db.session.commit()

    # Determine default pay URL
    if host_override:
        pay_url = f"{host_override.rstrip('/')}/pay/qr/{token}"
    else:
        lan_ip = _get_lan_ip()
        pay_url = f"http://{lan_ip}:3000/pay/qr/{token}"

    qr_image = _generate_qr_base64(pay_url)

    log_event(logger, "qr_session_created", merchant_id=merchant.merchant_id,
              amount=amount, token=token)

    return success("QR session created", {
        "qr": qr.to_dict(),
        "pay_url": pay_url,
        "qr_image": qr_image,
        "lan_ip": _get_lan_ip(),
    }, 201)


@qr_bp.route("/<string:token>", methods=["GET"])
def get_qr_session(token):
    """Public endpoint to fetch QR session details for the checkout page."""
    qr = QRPayment.query.filter_by(token=token).first()
    if not qr:
        return error("QR session not found or invalid", 404)

    # Check expiration
    if qr.status == "pending" and qr.is_expired():
        qr.status = "expired"
        db.session.commit()

    data = qr.to_dict()
    if qr.payment:
        data["payment"] = qr.payment.to_dict()
        fraud = FraudDetection.query.filter_by(payment_id=qr.payment.payment_id).first()
        data["fraud"] = fraud.to_dict() if fraud else None

    return success("OK", data)


@qr_bp.route("/<string:token>/status", methods=["GET"])
def get_qr_status(token):
    """Fast polling endpoint for the merchant's screen to detect payment in real time."""
    qr = QRPayment.query.filter_by(token=token).first()
    if not qr:
        return error("QR session not found", 404)

    if qr.status == "pending" and qr.is_expired():
        qr.status = "expired"
        db.session.commit()

    resp = {
        "token": qr.token,
        "status": qr.status,
        "payment_id": qr.payment_id,
        "is_expired": qr.is_expired(),
    }
    if qr.payment:
        resp["payment"] = qr.payment.to_dict()
        fraud = FraudDetection.query.filter_by(payment_id=qr.payment.payment_id).first()
        resp["fraud"] = fraud.to_dict() if fraud else None

    return success("OK", resp)


@qr_bp.route("/<string:token>/pay", methods=["POST"])
def pay_qr_session(token):
    """Pay a QR payment session.

    Accepts JWT authorization, or demo customer ID, or email/password authentication.
    Runs full ML fraud detection gate.
    """
    qr = QRPayment.query.filter_by(token=token).first()
    if not qr:
        return error("QR session not found", 404)

    if qr.status == "completed":
        return error("This QR payment has already been completed", 409)

    if qr.is_expired():
        qr.status = "expired"
        db.session.commit()
        return error("This QR payment session has expired. Please ask merchant to generate a new QR.", 410)

    data = request.get_json(silent=True) or {}

    # Identify customer
    customer = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user = db.session.get(User, int(identity))
            if user and user.customer:
                customer = user.customer
    except Exception:
        pass

    if customer is None:
        # Check demo customer ID or direct customer_id
        cust_id = data.get("customer_id") or data.get("demo_customer_id")
        if cust_id:
            customer = db.session.get(Customer, int(cust_id))
        elif data.get("email") and data.get("password"):
            from werkzeug.security import check_password_hash
            u = User.query.filter_by(email=(data["email"]).strip().lower()).first()
            if u and check_password_hash(u.password_hash, data["password"]) and u.customer:
                customer = u.customer
            else:
                return error("Invalid email or password", 401)

    if customer is None:
        return error("Customer identification is required to make a payment", 400)

    # Determine amount
    amount = float(qr.amount) if float(qr.amount) > 0 else float(data.get("amount", 0.0))
    if amount <= 0:
        return error("Payment amount must be greater than zero", 400)

    location_change = int(data.get("location_change", 0) or 0)
    device_change = int(data.get("device_change", 0) or 0)

    try:
        result = process_payment(
            customer_id=customer.customer_id,
            merchant_id=qr.merchant_id,
            amount=amount,
            location_change=location_change,
            device_change=device_change,
        )
    except ValueError as e:
        return error(str(e), 400)

    if result["status"] == "success":
        qr.status = "completed"
        qr.customer_id = customer.customer_id
        qr.payment_id = result["payment"]["payment_id"]
        qr.amount = amount
        db.session.commit()
        log_event(logger, "qr_payment_success", token=token,
                  payment_id=qr.payment_id, amount=amount)
    else:
        # Flagged as suspicious / rejected by ML
        qr.status = "rejected"
        qr.customer_id = customer.customer_id
        if "payment" in result and result["payment"]:
            qr.payment_id = result["payment"].get("payment_id")
        db.session.commit()
        log_event(logger, "qr_payment_rejected", token=token,
                  customer_id=customer.customer_id, amount=amount)

    return success(result["message"], {
        **result,
        "qr": qr.to_dict(),
    }, 200)
