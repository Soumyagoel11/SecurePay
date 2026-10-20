"""Seed SecurePay with demo data.

Usage:
    cd backend
    python seed.py

Works with any configured database (SQLite default or MySQL). Idempotent:
re-running will not duplicate users. Demo credentials are printed at the end.
"""

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.admin import Admin
from app.models.wallet import Wallet
from app.models.payment import Payment
from app.models.fraud_detection import FraudDetection
from app.models.refund import Refund
from app.services.payment_service import process_payment


DEMO_PASSWORD = "password123"


def _user(email, role):
    u = User.query.filter_by(email=email).first()
    if u:
        return u
    u = User(email=email, password_hash=generate_password_hash(DEMO_PASSWORD), role=role)
    db.session.add(u)
    db.session.flush()
    return u


def seed():
    # ---- Admin ----
    admin_user = _user("admin@securepay.com", "admin")
    if not admin_user.admin:
        db.session.add(Admin(user_id=admin_user.user_id, department="Risk & Fraud"))

    # ---- Merchants ----
    merchants = [
        ("merchant1@securepay.com", "TechNova Store", "Electronics"),
        ("merchant2@securepay.com", "FreshCart Groceries", "Retail"),
    ]
    merchant_objs = []
    for email, name, btype in merchants:
        mu = _user(email, "merchant")
        if not mu.merchant:
            m = Merchant(user_id=mu.user_id, company_name=name, business_type=btype, merchant_risk=0.1)
            db.session.add(m)
            db.session.flush()
            merchant_objs.append(m)
        else:
            merchant_objs.append(mu.merchant)

    # ---- Customers ----
    customers_info = [
        ("customer1@securepay.com", "Alice Johnson", 34, 1200.0),
        ("customer2@securepay.com", "Bob Smith", 28, 800.0),
        ("customer3@securepay.com", "Carol Lee", 45, 2500.0),
        ("customer4@securepay.com", "David Kim", 22, 500.0),
        ("customer5@securepay.com", "Eve Adams", 51, 3000.0),
    ]
    customers = []
    for email, name, age, balance in customers_info:
        cu = _user(email, "customer")
        if not cu.customer:
            c = Customer(user_id=cu.user_id, phone=f"+1{age}000", address=f"{age} Main St",
                         customer_age=age)
            db.session.add(c)
            db.session.flush()
            db.session.add(Wallet(customer_id=c.customer_id, balance=balance))
            customers.append(c)
        else:
            customers.append(cu.customer)

    db.session.commit()

    # ---- Sample payments (use the real workflow so fraud records are created) ----
    payment_plans = [
        (customers[0], merchant_objs[0], 150.0),
        (customers[0], merchant_objs[1], 60.0),
        (customers[1], merchant_objs[0], 300.0),
        (customers[2], merchant_objs[1], 500.0),
        (customers[2], merchant_objs[0], 1200.0),
        (customers[3], merchant_objs[1], 90.0),
        (customers[4], merchant_objs[0], 750.0),
    ]
    for cust, merch, amount in payment_plans:
        # ensure enough balance
        wallet = Wallet.query.filter_by(customer_id=cust.customer_id).first()
        if wallet and wallet.balance < amount:
            wallet.balance = float(wallet.balance) + amount + 50
            db.session.commit()
        try:
            process_payment(cust.customer_id, merch.merchant_id, amount)
        except Exception as e:
            print(f"  (payment skipped: {e})")

    # ---- One explicit suspicious payment + fraud record (demo of flagging) ----
    suspicious = Payment(
        customer_id=customers[3].customer_id, merchant_id=merchant_objs[0].merchant_id,
        amount=9000.0, status="rejected", risk_score=0.92, fraud_flag=True,
        fraud_decision="Suspicious", failure_reason="Flagged by fraud model",
    )
    db.session.add(suspicious)
    db.session.flush()
    db.session.add(FraudDetection(
        payment_id=suspicious.payment_id, prediction="Suspicious",
        risk_score=0.92, model_version="securepay-fraud-v1", model_name="RandomForest",
    ))

    # ---- One pending refund request on a successful payment ----
    successful = Payment.query.filter_by(status="success").first()
    if successful and not Refund.query.filter_by(payment_id=successful.payment_id).first():
        db.session.add(Refund(
            payment_id=successful.payment_id, customer_id=successful.customer_id,
            amount=float(successful.amount), reason="Item not as described",
            status="pending",
        ))

    db.session.commit()
    print("Demo data seeded successfully.")
    print("\n=== Demo credentials (password for all: %s) ===" % DEMO_PASSWORD)
    print("Admin   : admin@securepay.com")
    print("Merchant: merchant1@securepay.com | merchant2@securepay.com")
    print("Customer: customer1@securepay.com ... customer5@securepay.com")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        seed()
