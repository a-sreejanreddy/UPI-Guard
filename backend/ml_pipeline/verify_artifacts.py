"""
verify_artifacts.py — Artifact Integrity Smoke Test

Mimics exactly what the FastAPI backend does at startup:
loads mlp_model.h5 + scaler.pkl, runs two inference calls,
and asserts the high-risk transaction scores higher than the low-risk one.

Run from backend/ directory:
    python ml_pipeline/verify_artifacts.py
"""

import os
import pickle
import pathlib
import sys

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf

MODELS_DIR = pathlib.Path(__file__).parent.parent / "models"
MODEL_PATH = MODELS_DIR / "mlp_model.h5"
SCALER_PATH = MODELS_DIR / "scaler.pkl"


def verify() -> None:
    print("=" * 50)
    print("UPI Guard — Artifact Integrity Check")
    print("=" * 50)

    # Check files exist
    if not MODEL_PATH.exists():
        print(f"FAIL: {MODEL_PATH} not found. Run train.py first.")
        sys.exit(1)
    if not SCALER_PATH.exists():
        print(f"FAIL: {SCALER_PATH} not found. Run train.py first.")
        sys.exit(1)

    # Load model
    print(f"\nLoading model from {MODEL_PATH}...")
    model = tf.keras.models.load_model(str(MODEL_PATH))
    print(f"  Input shape  : {model.input_shape}")
    print(f"  Output shape : {model.output_shape}")
    assert model.input_shape == (None, 9), "Expected 9 input features"

    # Load scaler
    print(f"\nLoading scaler from {SCALER_PATH}...")
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    print(f"  Scaler type  : {type(scaler).__name__}")
    print(f"  Feature means: {scaler.mean_.round(2)}")

    # ------------------------------------------------------------------
    # Inference test 1: HIGH-RISK transaction
    # Features: 2am, 15th, June 2024, Travel category, ₹75,000, age 23, state 5, zip 400
    # ------------------------------------------------------------------
    print("\nInference test 1 — HIGH-RISK (night, large amount, Travel):")
    high_risk = np.array(
        [[2, 15, 6, 2024, 2, 75_000.0, 23, 5, 400]],
        dtype=np.float32,
    )
    scaled_hr = scaler.transform(high_risk)
    score_hr = float(model.predict(scaled_hr, verbose=0)[0][0])
    print(f"  fraud_score = {score_hr:.4f}  {'⚠ BLOCKED' if score_hr >= 0.5 else '✓ allowed'}")
    assert 0.0 <= score_hr <= 1.0, f"Score out of range: {score_hr}"

    # ------------------------------------------------------------------
    # Inference test 2: LOW-RISK transaction
    # Features: 2pm, 10th, March 2024, Food category, ₹250, age 34, state 12, zip 560
    # ------------------------------------------------------------------
    print("\nInference test 2 — LOW-RISK (daytime, small amount, Food):")
    low_risk = np.array(
        [[14, 10, 3, 2024, 0, 250.0, 34, 12, 560]],
        dtype=np.float32,
    )
    scaled_lr = scaler.transform(low_risk)
    score_lr = float(model.predict(scaled_lr, verbose=0)[0][0])
    print(f"  fraud_score = {score_lr:.4f}  {'⚠ BLOCKED' if score_lr >= 0.5 else '✓ allowed'}")
    assert 0.0 <= score_lr <= 1.0, f"Score out of range: {score_lr}"

    # ------------------------------------------------------------------
    # Key assertion: fraud score should beat legit score
    # ------------------------------------------------------------------
    assert score_hr > score_lr, (
        f"Model ordering wrong: high_risk ({score_hr:.4f}) <= low_risk ({score_lr:.4f}). "
        "Check training data or feature engineering."
    )

    print("\n" + "=" * 50)
    print("ARTIFACT INTEGRITY: PASS")
    print(f"  High-risk score : {score_hr:.4f}")
    print(f"  Low-risk score  : {score_lr:.4f}")
    print(f"  Delta           : {score_hr - score_lr:.4f}")
    print("=" * 50)


if __name__ == "__main__":
    verify()
