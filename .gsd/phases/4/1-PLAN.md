---
phase: 4
plan: 1
wave: 1
---

# Plan 4.1: ML Inference Engine & Payment Endpoint

## Objective
Implement `POST /transactions/pay` to serve as the core of the real-time fraud detection product. Connect API inputs natively to the ML components dynamically passing 9 transformed features to the preloaded Keras MLP models.

## Context
- .gsd/ROADMAP.md
- backend/app/db/models.py
- backend/app/schemas/transaction.py
- backend/app/ml/loader.py

## Tasks

<task type="auto">
  <name>Implement Payment Router</name>
  <files>backend/app/api/transactions.py</files>
  <action>
    - Create `transactions.py` and initialize an `APIRouter()` prefixed with `/transactions` and depending on `get_current_user`.
    - Create `POST /pay` mapped to `PaymentRequestSchema` and yielding `PaymentResponseSchema`.
    - Extract Merchant by `merchant_upi`. Verify logic (e.g. valid recipient).
    - Map `STATE_CODE_MAP` and `MERCHANT_CATEGORY_MAP` from User/Merchant attributes.
    - Compile real-time timestamp components (`hour, day, month, year`), and parse `zip_prefix`.
    - Execute `get_model_loader().predict(features)` resolving an exact float `fraud_score`.
    - Construct, apply, and db commit a new `Transaction` instance assigned appropriately status `TransactionStatus.APPROVED` or `TransactionStatus.BLOCKED_FRAUD` around the `0.5` threshold.
  </action>
  <verify>cd backend && python -c "from app.api.transactions import router; assert '/pay' in [r.path for r in router.routes]"</verify>
  <done>Transactions router is properly wired capturing payment payloads and conducting inline fraud determination.</done>
</task>

<task type="auto">
  <name>Integrate Transactions Router</name>
  <files>backend/app/main.py</files>
  <action>
    - Include `transactions.router` in `app/main.py` with the `/transactions` prefix and `["transactions"]` tag.
  </action>
  <verify>cd backend && python -c "from app.main import app; assert '/transactions/pay' in [r.path for r in app.routes]"</verify>
  <done>Payments logic is fully active within the FastAPI context.</done>
</task>

## Success Criteria
- [ ] Users can execute payments resolving actual model inference
- [ ] DB `transactions` table correctly receives exhaustive data points
