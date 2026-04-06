# Summary 1.2: SMOTE + MLP Training + Save Artifacts

**Status**: COMPLETE ✅
**Completed**: Phase 1, Wave 2

## What Was Done

### Task 1: train.py — Full ML Pipeline
- `backend/ml_pipeline/train.py` — 7-section standalone script
- Runs as: `cd backend && python -m ml_pipeline.train`
- Pipeline order (correct, no data leakage):
  1. Generate 50,000 synthetic records
  2. Stratified 80/20 train/test split
  3. Fit StandardScaler on train ONLY → transform test
  4. Apply SMOTE on scaled train data → balanced 1:1 classes
  5. MLP: Input(9)→Dense(128,ReLU)→BN→Dropout(0.3)→Dense(64,ReLU)→Dropout(0.2)→Dense(1,Sigmoid)
  6. Train: Adam(lr=0.001), EarlyStopping(patience=5 on val_auc), ReduceLROnPlateau
  7. Evaluate: classification_report + AUC-ROC
  8. Save mlp_model.h5 + scaler.pkl

### Task 2: verify_artifacts.py — Startup Smoke Test
- Mimics exact FastAPI startup: load model + scaler, run 2 inferences
- Asserts high-risk score > low-risk score

## Verification Results

### Training Output
- Final epoch accuracy: **0.998**
- Training completed successfully: `Phase 1 complete. Run the FastAPI backend to start serving.`
- Both artifacts saved without error

### Artifact Integrity Check
```
ARTIFACT INTEGRITY: PASS
  High-risk score : 1.0000  (night, ₹75k, Travel, age 23)
  Low-risk score  : 0.0003  (2pm, ₹250, Food, age 34)
  Delta           : 0.9997
```

Model discriminates with **0.9997 delta** — excellent separation.

## Files Created
- `backend/ml_pipeline/train.py`
- `backend/ml_pipeline/verify_artifacts.py`
- `backend/models/mlp_model.h5` (generated, gitignored)
- `backend/models/scaler.pkl` (generated, gitignored)
