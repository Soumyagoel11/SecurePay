"""
Dataset loaders for SecurePay fraud detection.

Primary (real) dataset : BankSim  (bs140513_032310.csv)
    - Agent-based simulation built from aggregated data of a Spanish bank.
    - Reputable, payment-domain dataset with interpretable columns that map
      directly onto SecurePay's feature model.
    - Source: Kaggle "Synthetic data from a financial payment system" /
      research paper "BankSim: A bank payments simulator for fraud detection".

Fallback (synthetic): a documented synthetic generator used ONLY when the real
dataset file is not present (so the project remains runnable out of the box).
We strongly recommend dropping the real BankSim CSV into ml/dataset/ for a
credible, data-driven model.

Both loaders return a DataFrame with the 12 canonical FEATURES plus TARGET.
"""

import os
import numpy as np
import pandas as pd

from ml.features import FEATURES, TARGET, AGE_MAP

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
BANKSIM_PATH = os.path.join(DATASET_DIR, "bs140513_032310.csv")
SYNTH_PATH = os.path.join(DATASET_DIR, "synthetic_transactions.csv")

SEED = 42


# ---------------------------------------------------------------------------
# Real dataset: BankSim
# ---------------------------------------------------------------------------
def load_banksim(path: str = BANKSIM_PATH) -> pd.DataFrame:
    """Load BankSim and engineer the canonical 12-feature representation."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"BankSim dataset not found at {path}")

    df = pd.read_csv(path)
    # Strip surrounding quotes from object columns.
    for col in ["customer", "age", "gender", "merchant", "category"]:
        df[col] = df[col].astype(str).str.strip("'").str.strip()

    df = df.sort_values(["customer", "step"]).reset_index(drop=True)
    g = df.groupby("customer")

    # Prior transaction count (cumcount = number of earlier rows in group).
    df["previous_transaction_count"] = g.cumcount()

    # Average amount of PRIOR transactions.
    amount_cs = g["amount"].cumsum()
    with np.errstate(invalid="ignore", divide="ignore"):
        avg = (amount_cs - df["amount"]) / df["previous_transaction_count"].replace(0, np.nan)
    df["average_transaction_amount"] = avg.fillna(0.0)

    # Prior fraud / failed counts (cumulative fraud excluding current row).
    fraud_cs = g["fraud"].cumsum()
    df["failed_transaction_count"] = (fraud_cs - df["fraud"]).clip(lower=0)
    df["previous_fraud_count"] = df["failed_transaction_count"]

    # Account age in days since the customer's first observed transaction.
    first_step = g["step"].transform("first")
    df["account_age"] = ((df["step"] - first_step) / 24.0).clip(lower=0)
    df["account_age"] = df["account_age"].replace(0, 1)

    # Merchant risk = historical fraud rate of that merchant (stable signal).
    merchant_risk = df.groupby("merchant")["fraud"].transform("mean").astype(float)
    df["merchant_risk"] = merchant_risk

    # Transaction hour within the day (step is an hour index 0..179).
    df["transaction_hour"] = df["step"] % 24

    # Customer age mapped from categorical group to numeric midpoint.
    df["customer_age"] = df["age"].map(AGE_MAP).fillna(40).astype(float)

    # Location / device change are not present in BankSim; neutral defaults.
    # At inference time SecurePay supplies real values from session context.
    df["location_change"] = 0
    df["device_change"] = 0

    # Transaction frequency = number of this customer's prior transactions
    # within the previous 24 simulated hours.
    def _freq_last_24h(steps: pd.Series) -> pd.Series:
        arr = steps.values
        n = len(arr)
        out = np.empty(n, dtype=int)
        for i in range(n):
            left = int(np.searchsorted(arr, arr[i] - 24, side="left"))
            out[i] = i - left  # prior rows in [step-24, step)
        return pd.Series(out, index=steps.index)

    df["transaction_frequency"] = g["step"].transform(_freq_last_24h)

    df["transaction_amount"] = df["amount"].astype(float)
    df[TARGET] = df["fraud"].astype(int)

    out = df[FEATURES + [TARGET]].copy()
    return out


# ---------------------------------------------------------------------------
# Fallback: documented synthetic generator
# ---------------------------------------------------------------------------
def generate_synthetic(n_samples: int = 20000, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    transaction_amount = np.round(rng.lognormal(mean=4.2, sigma=1.0, size=n_samples), 2)
    transaction_amount = np.clip(transaction_amount, 1.0, 25000.0)
    transaction_hour = rng.integers(0, 24, size=n_samples)
    transaction_frequency = rng.poisson(lam=2.0, size=n_samples)
    customer_age = rng.integers(18, 80, size=n_samples)
    account_age = rng.integers(1, 2000, size=n_samples)
    previous_transaction_count = rng.poisson(lam=15, size=n_samples)
    average_transaction_amount = np.clip(
        np.round(rng.lognormal(mean=4.0, sigma=0.8, size=n_samples), 2), 1.0, 20000.0
    )
    merchant_risk = np.round(rng.beta(a=2, b=5, size=n_samples), 3)
    failed_transaction_count = rng.poisson(lam=0.5, size=n_samples)
    location_change = rng.binomial(1, 0.1, size=n_samples)
    device_change = rng.binomial(1, 0.1, size=n_samples)
    previous_fraud_count = rng.poisson(lam=0.1, size=n_samples)

    df = pd.DataFrame({
        "transaction_amount": transaction_amount,
        "transaction_hour": transaction_hour,
        "transaction_frequency": transaction_frequency,
        "customer_age": customer_age,
        "account_age": account_age,
        "previous_transaction_count": previous_transaction_count,
        "average_transaction_amount": average_transaction_amount,
        "merchant_risk": merchant_risk,
        "failed_transaction_count": failed_transaction_count,
        "location_change": location_change,
        "device_change": device_change,
        "previous_fraud_count": previous_fraud_count,
    })

    amount_ratio = df["transaction_amount"] / (df["average_transaction_amount"] + 1.0)
    risk = (
        0.30 * (amount_ratio > 5).astype(float)
        + 0.20 * ((df["transaction_hour"] >= 0) & (df["transaction_hour"] <= 5)).astype(float)
        + 0.25 * (df["transaction_frequency"] >= 8).astype(float)
        + 0.20 * (df["account_age"] < 30).astype(float)
        + 0.30 * (df["merchant_risk"] > 0.7).astype(float)
        + 0.25 * (df["failed_transaction_count"] >= 3).astype(float)
        + 0.35 * (df["location_change"] == 1).astype(float)
        + 0.30 * (df["device_change"] == 1).astype(float)
        + 0.50 * (df["previous_fraud_count"] >= 1).astype(float)
    )
    # Label is a deterministic-ish function of the engineered risk so the model
    # learns a clear, explainable boundary (with light noise to avoid perfect
    # memorisation). High risk => fraudulent, low risk => legitimate.
    noise = rng.normal(0, 0.05, size=n_samples)
    df[TARGET] = (risk + noise > 0.6).astype(int)
    return df


# ---------------------------------------------------------------------------
# Unified loader
# ---------------------------------------------------------------------------
def load_training_data(use_cache: bool = True) -> pd.DataFrame:
    """Return the training DataFrame, preferring the real BankSim dataset."""
    if os.path.exists(BANKSIM_PATH):
        df = load_banksim()
        df.attrs["source"] = "banksim"
        return df
    # Synthetic fallback so the project is runnable without the real CSV.
    if use_cache and os.path.exists(SYNTH_PATH):
        df = pd.read_csv(SYNTH_PATH)
    else:
        df = generate_synthetic()
        df.to_csv(SYNTH_PATH, index=False)
    df.attrs["source"] = "synthetic"
    return df


if __name__ == "__main__":
    data = load_training_data()
    print(f"Source: {data.attrs.get('source')}")
    print(f"Rows: {len(data)} | Fraud rate: {data[TARGET].mean():.4f}")
    print(f"Features: {FEATURES}")
