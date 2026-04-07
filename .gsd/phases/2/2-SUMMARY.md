# Summary 2.2: Schemas + Model Loader + FastAPI App + Admin Seed

**Status**: COMPLETE
**Wave**: 2

## What Was Done

### Task 1: Pydantic v2 Schemas + Model Loader
- `backend/app/schemas/auth.py` — OtpRequestSchema (10-digit mobile validator)
- `backend/app/schemas/user.py` — UserCreateSchema + UserResponseSchema
- `backend/app/schemas/merchant.py` — MerchantCreateSchema (UPI format + category validator)
- `backend/app/schemas/transaction.py` — PaymentRequestSchema, TransactionResponseSchema, PaymentResponseSchema, OverrideResponseSchema
- `backend/app/ml/loader.py` — ModelLoader singleton, get_model_loader() factory

### Task 2: Security + FastAPI App
- `backend/app/core/security.py` — bcrypt hash/verify, JWT create/decode, cookie set/clear, get_current_user dep, require_role() factory
- `backend/app/main.py` — FastAPI with lifespan, CORS, /health endpoint

## Verification Results
- Schemas OK: OtpRequestSchema rejects non-10-digit mobile
- Loader singleton: `get_model_loader() is ml` == True; is_loaded=False before startup
- Security utils: JWT round-trip verified (create → decode)
- Full lifespan test PASSED:
  - `[DB] Tables ready`
  - `[DB] Admin seeded: mobile=9999999999, role=admin`
  - `[ML] Loaded model: mlp_model.h5 (input shape: (None, 9))`
  - `GET /health` returns `{"status": "ok", "model_loaded": true}` — Exit code: 0

## Files Created (7 total)
- backend/app/core/security.py
- backend/app/main.py
- backend/app/ml/loader.py
- backend/app/schemas/auth.py, merchant.py, transaction.py, user.py
