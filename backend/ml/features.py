"""Canonical feature definitions shared by training and inference.

Keeping ONE source of truth for feature names guarantees the model trained on
the real BankSim dataset is fed the exact same 12 features at inference time
from SecurePay transaction context.

Features (12):
    1. transaction_amount
    2. transaction_hour
    3. transaction_frequency
    4. customer_age
    5. account_age
    6. previous_transaction_count
    7. average_transaction_amount
    8. merchant_risk
    9. failed_transaction_count
    10. location_change
    11. device_change
    12. previous_fraud_count

Target: 0 = Legitimate, 1 = Fraudulent
"""

FEATURES = [
    "transaction_amount",
    "transaction_hour",
    "transaction_frequency",
    "customer_age",
    "account_age",
    "previous_transaction_count",
    "average_transaction_amount",
    "merchant_risk",
    "failed_transaction_count",
    "location_change",
    "device_change",
    "previous_fraud_count",
]

TARGET = "is_fraud"

# BankSim encodes age as a categorical group code; map to a numeric midpoint.
AGE_MAP = {
    "0": 16,   # <= 18
    "1": 22,   # 19-25
    "2": 30,   # 26-35
    "3": 40,   # 36-45
    "4": 50,   # 46-55
    "5": 60,   # 56-65
    "6": 70,   # > 65
    "U": 40,   # Unknown
}
