"""Routes package: import blueprints so app/__init__.py can register them."""

from app.routes.auth import auth_bp
from app.routes.wallet import wallet_bp
from app.routes.payments import payments_bp
from app.routes.fraud import fraud_bp
from app.routes.refunds import refunds_bp
from app.routes.admin import admin_bp
from app.routes.merchant import merchant_bp
from app.routes.customer import customer_bp
from app.routes.qr_payments import qr_bp

__all__ = [
    "auth_bp", "wallet_bp", "payments_bp", "fraud_bp",
    "refunds_bp", "admin_bp", "merchant_bp", "customer_bp",
    "qr_bp",
]

