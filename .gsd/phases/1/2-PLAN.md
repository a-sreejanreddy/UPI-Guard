---
phase: 1
plan: 2
wave: 2
---

# Plan 1.2: SMOTE Balancing + MLP Training + Save Artifacts

## Objective
Write `backend/ml_pipeline/train.py` — the standalone, single-command training script
that: generates data, applies SMOTE, trains the MLP, evaluates it, and saves
`mlp_model.h5` + `scaler.pkl` to `backend/models/`. This script is the Phase 1
deliverable the entire backend depends on.

**Depends on:** Plan 1.1 (generate_data.py must exist and pass verification)

## Context
- `.gsd/SPEC.md` — MLP architecture spec, feature list, artifact paths
- `backend/ml_pipeline/generate_data.py` — data generator (from Plan 1.1)

## Tasks

<task type="auto">
  <name>Write train.py — full pipeline script</name>
  <files>
    backend/ml_pipeline/train.py
  </files>
  <action>
    Write backend/ml_pipeline/train.py as a standalone executable script.
    Running `python ml_pipeline/train.py` from the `backend/` directory must:
    complete without errors and save both model artifacts.

    **Exact script structure (implement each section in order):**

    ### Section 1: Imports & Config
    ```python
    import os, sys, pickle, pathlib
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, roc_auc_score
    from imblearn.over_sampling import SMOTE
    import tensorflow as tf
    from tensorflow import keras
    from ml_pipeline.generate_data import generate_upi_transactions

    MODELS_DIR = pathlib.Path(__file__).parent.parent / "models"
    MODELS_DIR.mkdir(exist_ok=True)
    MODEL_PATH = MODELS_DIR / "mlp_model.h5"
    SCALER_PATH = MODELS_DIR / "scaler.pkl"
    RANDOM_STATE = 42
    ```

    ### Section 2: Data Generation
    ```python
    print("Generating synthetic UPI transaction data...")
    df = generate_upi_transactions(n_samples=50000, fraud_rate=0.02, random_state=RANDOM_STATE)
    print(f"  Total: {len(df):,} | Fraud: {df['is_fraud'].sum():,} ({df['is_fraud'].mean():.1%})")

    FEATURE_COLS = ['hour','day','month','year','merchant_category',
                    'amount','user_age','state_code','zip_prefix']
    X = df[FEATURE_COLS].values.astype(np.float32)
    y = df['is_fraud'].values.astype(np.float32)
    ```

    ### Section 3: Train/Test Split
    ```python
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    print(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")
    ```

    ### Section 4: Feature Scaling (CRITICAL — fit on train only)
    ```python
    print("Fitting StandardScaler on training data only...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)  # transform only, never fit
    ```

    ### Section 5: SMOTE (apply AFTER scaling, on train only)
    ```python
    print("Applying SMOTE to balance training classes...")
    smote = SMOTE(random_state=RANDOM_STATE)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)
    print(f"  After SMOTE — Total: {len(X_train_resampled):,} | "
          f"Fraud: {y_train_resampled.sum():.0f} ({y_train_resampled.mean():.1%})")
    ```

    ### Section 6: MLP Model Definition
    Build exactly this architecture:
    ```python
    tf.random.set_seed(RANDOM_STATE)
    model = keras.Sequential([
        keras.layers.Input(shape=(9,)),
        keras.layers.Dense(128, activation='relu'),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(1, activation='sigmoid')
    ], name='mlp_fraud_detector')

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy', keras.metrics.AUC(name='auc'),
                 keras.metrics.Precision(name='precision'),
                 keras.metrics.Recall(name='recall')]
    )
    model.summary()
    ```

    ### Section 7: Training
    ```python
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_auc', patience=5, restore_best_weights=True, mode='max'
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6
        )
    ]

    print("Training MLP...")
    history = model.fit(
        X_train_resampled, y_train_resampled,
        validation_split=0.15,
        epochs=50,
        batch_size=256,
        callbacks=callbacks,
        verbose=1
    )
    ```

    ### Section 8: Evaluation on Test Set
    ```python
    print("\n--- EVALUATION ON HELD-OUT TEST SET ---")
    y_pred_proba = model.predict(X_test_scaled, verbose=0).flatten()
    y_pred = (y_pred_proba >= 0.5).astype(int)

    print(classification_report(y_test, y_pred, target_names=['Legitimate','Fraud'],
                                 zero_division=0))
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"AUC-ROC: {auc:.4f}")

    # Warn if model is too weak
    fraud_recall = (y_pred[y_test == 1] == 1).mean()
    if fraud_recall < 0.70:
        print(f"WARNING: Fraud recall is {fraud_recall:.2%} — consider more epochs or data")
    ```

    ### Section 9: Save Artifacts
    ```python
    print(f"\nSaving model to {MODEL_PATH}...")
    model.save(str(MODEL_PATH))

    print(f"Saving scaler to {SCALER_PATH}...")
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)

    print("\nDone. Artifacts saved:")
    print(f"  Model:  {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.0f} KB)")
    print(f"  Scaler: {SCALER_PATH} ({SCALER_PATH.stat().st_size} bytes)")
    print("\nPhase 1 complete. You can now start the FastAPI backend.")
    ```

    **Critical constraints:**
    - Scaler MUST be fit on X_train BEFORE SMOTE, then SMOTE applied to scaled data
    - Do NOT fit scaler on test data
    - Do NOT save the dataset to disk
    - If run from backend/ directory, imports must work: `from ml_pipeline.generate_data import ...`
    - Add `if __name__ == "__main__":` guard around sections 2-9 so the file
      is importable without triggering training
  </action>
  <verify>
    cd backend && python -c "
import pathlib, subprocess, sys
result = subprocess.run([sys.executable, '-m', 'ml_pipeline.train'],
                       capture_output=True, text=True, timeout=300)
print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
if result.returncode != 0:
    print('STDERR:', result.stderr[-1000:])
    raise SystemExit('train.py failed')
model_ok = pathlib.Path('models/mlp_model.h5').exists()
scaler_ok = pathlib.Path('models/scaler.pkl').exists()
assert model_ok, 'mlp_model.h5 not found'
assert scaler_ok, 'scaler.pkl not found'
print(f'PASS — model={pathlib.Path("models/mlp_model.h5").stat().st_size//1024}KB scaler={pathlib.Path("models/scaler.pkl").stat().st_size}B')
"
  </verify>
  <done>
    - `python -m ml_pipeline.train` runs top-to-bottom without error (from backend/ dir)
    - `backend/models/mlp_model.h5` exists and is > 50 KB
    - `backend/models/scaler.pkl` exists and is > 0 bytes
    - Console shows classification report + AUC-ROC score
    - AUC-ROC is >= 0.80 on held-out test set
    - Fraud recall is >= 0.70 (the model actually detects fraud)
  </done>
</task>

<task type="auto">
  <name>Smoke-test artifact integrity (load and infer)</name>
  <files>
    backend/ml_pipeline/verify_artifacts.py
  </files>
  <action>
    Write a small smoke-test script `backend/ml_pipeline/verify_artifacts.py`
    that mimics exactly what the FastAPI backend will do at startup:

    ```python
    import pickle, pathlib
    import numpy as np
    import tensorflow as tf

    MODELS_DIR = pathlib.Path(__file__).parent.parent / "models"

    print("Loading model...")
    model = tf.keras.models.load_model(str(MODELS_DIR / "mlp_model.h5"))
    print(f"  Input shape: {model.input_shape}")
    print(f"  Output shape: {model.output_shape}")

    print("Loading scaler...")
    with open(MODELS_DIR / "scaler.pkl", "rb") as f:
        scaler = pickle.load(f)

    print("Running inference on synthetic transaction...")
    # Simulate a high-risk transaction (night hour, large amount)
    sample = np.array([[2, 15, 6, 2024, 2, 75000.0, 23, 5, 400]], dtype=np.float32)
    scaled = scaler.transform(sample)
    score = float(model.predict(scaled, verbose=0)[0][0])
    print(f"  fraud_score = {score:.4f}")

    # Simulate a low-risk transaction (daytime, small amount)
    sample2 = np.array([[14, 10, 3, 2024, 0, 250.0, 34, 12, 560]], dtype=np.float32)
    scaled2 = scaler.transform(sample2)
    score2 = float(model.predict(scaled2, verbose=0)[0][0])
    print(f"  legitimate_score = {score2:.4f}")

    assert 0.0 <= score <= 1.0, "Score out of range"
    assert 0.0 <= score2 <= 1.0, "Score out of range"
    # High-risk should score higher than low-risk
    assert score > score2, f"Expected fraud_score ({score:.4f}) > legit_score ({score2:.4f})"
    print("ARTIFACT INTEGRITY: PASS")
    ```

    This file should be standalone, runnable as:
    `cd backend && python ml_pipeline/verify_artifacts.py`
  </action>
  <verify>
    cd backend && python ml_pipeline/verify_artifacts.py
  </verify>
  <done>
    - `verify_artifacts.py` runs without error
    - Outputs "ARTIFACT INTEGRITY: PASS"
    - High-risk transaction scores higher than low-risk transaction
    - Both scores are floats in [0.0, 1.0]
  </done>
</task>

## Success Criteria
- [ ] `backend/ml_pipeline/train.py` exists and is a valid Python script
- [ ] `python -m ml_pipeline.train` (from backend/) completes without error in < 5 minutes
- [ ] `backend/models/mlp_model.h5` exists and is > 50 KB
- [ ] `backend/models/scaler.pkl` exists and is > 0 bytes
- [ ] AUC-ROC on test set is >= 0.80
- [ ] Fraud recall on test set is >= 0.70
- [ ] `python ml_pipeline/verify_artifacts.py` outputs ARTIFACT INTEGRITY: PASS
