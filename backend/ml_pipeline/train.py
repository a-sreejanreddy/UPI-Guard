"""
train.py — UPI Guard MLP Fraud Detector Training Pipeline

Standalone script. Run from the backend/ directory:
    python -m ml_pipeline.train

Pipeline:
    1. Generate synthetic UPI transaction data (50k records, 2% fraud)
    2. Train/test split (80/20, stratified)
    3. Fit StandardScaler on train set ONLY
    4. Apply SMOTE on scaled train data to balance classes
    5. Train MLP: Input(9) → Dense(128) → BN → Dropout → Dense(64) → Dropout → Dense(1)
    6. Evaluate on held-out test set (classification report + AUC-ROC)
    7. Save mlp_model.h5 + scaler.pkl to backend/models/

Outputs:
    backend/models/mlp_model.h5   — Keras MLP model
    backend/models/scaler.pkl     — Fitted StandardScaler
"""

import os
import sys
import pickle
import pathlib

import numpy as np

# Suppress TensorFlow INFO/WARNING logs for cleaner output
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def main() -> None:
    # ------------------------------------------------------------------
    # Imports (deferred so the module is importable without heavy deps)
    # ------------------------------------------------------------------
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, roc_auc_score
    from imblearn.over_sampling import SMOTE
    import tensorflow as tf
    from tensorflow import keras

    from ml_pipeline.generate_data import generate_upi_transactions

    RANDOM_STATE = 42
    MODELS_DIR = pathlib.Path(__file__).parent.parent / "models"
    MODELS_DIR.mkdir(exist_ok=True)
    MODEL_PATH = MODELS_DIR / "mlp_model.h5"
    SCALER_PATH = MODELS_DIR / "scaler.pkl"

    FEATURE_COLS = [
        "hour", "day", "month", "year", "merchant_category",
        "amount", "user_age", "state_code", "zip_prefix",
    ]

    # ------------------------------------------------------------------
    # Section 1: Data Generation
    # ------------------------------------------------------------------
    print("=" * 60)
    print("UPI Guard — MLP Fraud Detector Training Pipeline")
    print("=" * 60)
    print("\n[1/7] Generating synthetic UPI transaction data...")

    df = generate_upi_transactions(
        n_samples=50_000, fraud_rate=0.02, random_state=RANDOM_STATE
    )
    fraud_count = int(df["is_fraud"].sum())
    print(f"      Total  : {len(df):,}")
    print(f"      Fraud  : {fraud_count:,} ({df['is_fraud'].mean():.1%})")
    print(f"      Legit  : {len(df) - fraud_count:,}")

    X = df[FEATURE_COLS].values.astype(np.float32)
    y = df["is_fraud"].values.astype(np.float32)

    # ------------------------------------------------------------------
    # Section 2: Train/Test Split
    # ------------------------------------------------------------------
    print("\n[2/7] Splitting data (80% train / 20% test, stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    print(f"      Train  : {len(X_train):,} rows")
    print(f"      Test   : {len(X_test):,} rows")

    # ------------------------------------------------------------------
    # Section 3: Feature Scaling (CRITICAL: fit on train only)
    # ------------------------------------------------------------------
    print("\n[3/7] Fitting StandardScaler on training data only...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)   # transform only — never fit
    print("      Scaler fitted. Test set transformed (not fitted).")

    # ------------------------------------------------------------------
    # Section 4: SMOTE — applied AFTER scaling, on train only
    # ------------------------------------------------------------------
    print("\n[4/7] Applying SMOTE to balance training classes...")
    smote = SMOTE(random_state=RANDOM_STATE)
    X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)
    resampled_fraud = int(y_train_res.sum())
    print(f"      After SMOTE — Total: {len(X_train_res):,}")
    print(f"      Fraud: {resampled_fraud:,} | Legit: {len(X_train_res) - resampled_fraud:,}")
    print(f"      Class balance: {y_train_res.mean():.1%} fraud")

    # ------------------------------------------------------------------
    # Section 5: MLP Model Definition
    # ------------------------------------------------------------------
    print("\n[5/7] Building MLP model...")
    tf.random.set_seed(RANDOM_STATE)

    model = keras.Sequential(
        [
            keras.layers.Input(shape=(9,)),
            keras.layers.Dense(128, activation="relu"),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(64, activation="relu"),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(1, activation="sigmoid"),
        ],
        name="mlp_fraud_detector",
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            keras.metrics.AUC(name="auc"),
            keras.metrics.Precision(name="precision"),
            keras.metrics.Recall(name="recall"),
        ],
    )
    model.summary()

    # ------------------------------------------------------------------
    # Section 6: Training
    # ------------------------------------------------------------------
    print("\n[6/7] Training MLP...")
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_auc",
            patience=5,
            restore_best_weights=True,
            mode="max",
            verbose=1,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1,
        ),
    ]

    history = model.fit(
        X_train_res,
        y_train_res,
        validation_split=0.15,
        epochs=50,
        batch_size=256,
        callbacks=callbacks,
        verbose=1,
    )

    epochs_run = len(history.history["loss"])
    print(f"\n      Training complete. Epochs run: {epochs_run}")

    # ------------------------------------------------------------------
    # Section 7: Evaluation on held-out test set
    # ------------------------------------------------------------------
    print("\n[7/7] Evaluating on held-out test set...")
    y_pred_proba = model.predict(X_test_scaled, verbose=0).flatten()
    y_pred = (y_pred_proba >= 0.5).astype(int)

    print("\n--- CLASSIFICATION REPORT ---")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=["Legitimate", "Fraud"],
            zero_division=0,
        )
    )

    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"AUC-ROC: {auc:.4f}")

    # Quality gate
    fraud_mask = y_test == 1
    if fraud_mask.sum() > 0:
        fraud_recall = float((y_pred[fraud_mask] == 1).mean())
        print(f"Fraud Recall: {fraud_recall:.2%}")
        if fraud_recall < 0.70:
            print(
                f"WARNING: Fraud recall {fraud_recall:.2%} < 70% target. "
                "Consider increasing n_samples or epochs."
            )
    else:
        print("WARNING: No fraud samples in test set (too small a dataset?)")

    # ------------------------------------------------------------------
    # Save Artifacts
    # ------------------------------------------------------------------
    print(f"\nSaving model  → {MODEL_PATH}")
    model.save(str(MODEL_PATH))

    print(f"Saving scaler → {SCALER_PATH}")
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    model_kb = MODEL_PATH.stat().st_size // 1024
    scaler_b = SCALER_PATH.stat().st_size
    print(f"\nArtifacts saved:")
    print(f"  mlp_model.h5 : {model_kb} KB  →  {MODEL_PATH}")
    print(f"  scaler.pkl   : {scaler_b} bytes  →  {SCALER_PATH}")
    print("\n" + "=" * 60)
    print("Phase 1 complete. Run the FastAPI backend to start serving.")
    print("=" * 60)


if __name__ == "__main__":
    main()
