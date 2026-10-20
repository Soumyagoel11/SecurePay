"""Model package: import all models so Flask-SQLAlchemy registers them."""

from app.models.user import User
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.admin import Admin
from app.models.wallet import Wallet
from app.models.payment import Payment
from app.models.transaction import Transaction
from app.models.fraud_detection import FraudDetection
from app.models.refund import Refund
from app.models.qr_payment import QRPayment

__all__ = [
    "User", "Customer", "Merchant", "Admin", "Wallet",
    "Payment", "Transaction", "FraudDetection", "Refund", "QRPayment",
]

