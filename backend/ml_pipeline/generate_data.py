"""
generate_data.py — Synthetic UPI Transaction Data Generator

Generates realistic, imbalanced UPI transaction data for training
the fraud detection MLP. No ML libraries required — only numpy/pandas.

Usage:
    from ml_pipeline.generate_data import generate_upi_transactions
    df = generate_upi_transactions(n_samples=50000, fraud_rate=0.02)

    # Or run directly for a sanity check:
    python ml_pipeline/generate_data.py  (from backend/ directory)
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Merchant category encoding (must match inference-time encoding in FastAPI)
# ---------------------------------------------------------------------------
MERCHANT_CATEGORIES = {
    0: "Food",
    1: "Retail",
    2: "Travel",
    3: "Entertainment",
    4: "Healthcare",
    5: "Education",
    6: "Utilities",
    7: "Other",
}

# Indian state codes (28 states + UTs, 0-indexed)
N_STATES = 29

# Legitimate transaction hour weights — favour business hours
_HOUR_WEIGHTS_LEGIT = np.array([
    0.5, 0.3, 0.2, 0.15, 0.15, 0.2,   # 0-5: very low
    0.5, 1.5, 3.0, 4.0, 4.5, 4.5,     # 6-11: morning ramp
    4.0, 4.0, 4.5, 4.5, 4.0, 4.0,     # 12-17: afternoon peak
    3.5, 3.0, 2.5, 2.0, 1.5, 1.0,     # 18-23: evening taper
], dtype=float)
_HOUR_WEIGHTS_LEGIT /= _HOUR_WEIGHTS_LEGIT.sum()

# Fraudulent transaction hours — heavily biased toward late night
_FRAUD_HOURS = [0, 1, 2, 3, 4, 5, 23]

# Fraudulent merchant categories — riskier segments
_FRAUD_CAT_WEIGHTS = np.array([
    0.05, 0.10, 0.30, 0.10, 0.05, 0.05, 0.05, 0.30  # Travel + Other dominant
], dtype=float)
_FRAUD_CAT_WEIGHTS /= _FRAUD_CAT_WEIGHTS.sum()


def generate_upi_transactions(
    n_samples: int = 50000,
    fraud_rate: float = 0.02,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic UPI transaction records.

    Parameters
    ----------
    n_samples    : Total number of transactions to generate.
    fraud_rate   : Fraction of transactions that are fraudulent (~0.02 = 2%).
    random_state : NumPy random seed for reproducibility.

    Returns
    -------
    pd.DataFrame with columns:
        hour, day, month, year, merchant_category, amount,
        user_age, state_code, zip_prefix, is_fraud
    """
    rng = np.random.default_rng(random_state)

    n_fraud = max(1, int(n_samples * fraud_rate))
    n_legit = n_samples - n_fraud

    # ------------------------------------------------------------------
    # Legitimate transactions
    # ------------------------------------------------------------------
    legit_hours = rng.choice(np.arange(24), size=n_legit, p=_HOUR_WEIGHTS_LEGIT)
    legit_days = rng.integers(1, 29, size=n_legit)
    legit_months = rng.integers(1, 13, size=n_legit)
    legit_years = rng.choice([2023, 2024], size=n_legit)
    legit_cats = rng.integers(0, 8, size=n_legit)

    # Log-normal amount: realistic INR range [10, 50_000]
    legit_amounts = np.exp(rng.normal(loc=5.5, scale=1.2, size=n_legit))
    legit_amounts = np.clip(legit_amounts, 10.0, 50_000.0).round(2)

    legit_ages = np.clip(
        rng.normal(loc=32, scale=10, size=n_legit), 18, 70
    ).astype(int)
    legit_states = rng.integers(0, N_STATES, size=n_legit)
    legit_zips = rng.integers(100, 1000, size=n_legit)

    df_legit = pd.DataFrame({
        "hour": legit_hours,
        "day": legit_days,
        "month": legit_months,
        "year": legit_years,
        "merchant_category": legit_cats,
        "amount": legit_amounts,
        "user_age": legit_ages,
        "state_code": legit_states,
        "zip_prefix": legit_zips,
        "is_fraud": np.zeros(n_legit, dtype=int),
    })

    # ------------------------------------------------------------------
    # Fraudulent transactions — anomaly signals injected
    # ------------------------------------------------------------------
    fraud_hours = rng.choice(_FRAUD_HOURS, size=n_fraud)
    fraud_days = rng.integers(1, 29, size=n_fraud)
    fraud_months = rng.integers(1, 13, size=n_fraud)
    fraud_years = rng.choice([2023, 2024], size=n_fraud)
    fraud_cats = rng.choice(np.arange(8), size=n_fraud, p=_FRAUD_CAT_WEIGHTS)

    # High-value amounts: [5_000, 200_000]
    fraud_amounts = np.exp(rng.normal(loc=8.5, scale=1.5, size=n_fraud))
    fraud_amounts = np.clip(fraud_amounts, 5_000.0, 200_000.0).round(2)

    # Younger age skew
    fraud_ages = np.clip(
        rng.normal(loc=25, scale=8, size=n_fraud), 18, 50
    ).astype(int)
    fraud_states = rng.integers(0, N_STATES, size=n_fraud)
    fraud_zips = rng.integers(100, 1000, size=n_fraud)

    df_fraud = pd.DataFrame({
        "hour": fraud_hours,
        "day": fraud_days,
        "month": fraud_months,
        "year": fraud_years,
        "merchant_category": fraud_cats,
        "amount": fraud_amounts,
        "user_age": fraud_ages,
        "state_code": fraud_states,
        "zip_prefix": fraud_zips,
        "is_fraud": np.ones(n_fraud, dtype=int),
    })

    # ------------------------------------------------------------------
    # Combine, shuffle, reset index
    # ------------------------------------------------------------------
    df = pd.concat([df_legit, df_fraud], ignore_index=True)
    df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)

    # Enforce correct dtypes
    int_cols = ["hour", "day", "month", "year", "merchant_category",
                "user_age", "state_code", "zip_prefix", "is_fraud"]
    for col in int_cols:
        df[col] = df[col].astype(int)
    df["amount"] = df["amount"].astype(float)

    return df


# ---------------------------------------------------------------------------
# Sanity-check entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pathlib

    print("Generating 50,000 synthetic UPI transactions...")
    df = generate_upi_transactions(n_samples=50_000, fraud_rate=0.02)

    fraud_count = df["is_fraud"].sum()
    fraud_rate_actual = df["is_fraud"].mean()

    print(f"\nDataset shape    : {df.shape}")
    print(f"Fraud count      : {fraud_count:,}")
    print(f"Fraud rate       : {fraud_rate_actual:.2%}")
    print(f"\nColumn dtypes:\n{df.dtypes}")
    print(f"\nDescriptive stats:\n{df.describe().round(2).to_string()}")

    # Save first 100 rows for visual inspection
    out_path = pathlib.Path(__file__).parent / "sample_data_check.csv"
    df.head(100).to_csv(out_path, index=False)
    print(f"\nSample saved to {out_path}")
