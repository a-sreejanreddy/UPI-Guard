# SPEC.md — UPI Guard: Real-Time UPI Fraud Detection System

> **Status**: `FINALIZED`

## Vision

UPI Guard is a full-stack web application simulating a real-time UPI payment fraud detection
system. A pre-trained Dense Neural Network (MLP) evaluates incoming transaction metadata and
blocks fraudulent payments before processing. The system exposes three role-based dashboards
(Admin, Merchant, User), authenticates via mobile + simulated OTP with JWT stored in httpOnly
cookies, and logs every transaction decision — including blocked ones — for complete audit
capability.

## Goals

1. **ML Fraud Engine** — Train an MLP on synthetic, SMOTE-balanced data; serve real-time
   predictions returning a `fraud_score` (0.0–1.0) with every decision.
2. **Secure Auth** — Mobile number + simulated OTP login. JWT in httpOnly, Secure,
   SameSite=Strict cookies. Mock SMS Inbox UI panel delivers the OTP in-app.
3. **Role-Based Access** — Three roles (Admin, Merchant, User) enforced at both React Router
   (UI) and FastAPI middleware (API) layers.
4. **Complete Audit Trail** — Log ALL transactions to SQLite (APPROVED / BLOCKED_FRAUD /
   ADMIN_OVERRIDDEN) with all 9 extracted features and fraud_score.
5. **Admin Override** — Admin can review and manually approve any blocked transaction.
6. **Realistic UPI QR** — Generate proper `upi://pay?pa=...` QR codes for merchants.
7. **Docker-Ready** — Structured for containerization from day one; V1 runs locally.

## Non-Goals (Out of Scope for V1)

- Real UPI payment rail integration (NPCI/bank APIs)
- Real SMS/OTP delivery — simulated only
- Production cloud deployment
- Multi-tenancy or organization hierarchies
- Model retraining via the UI
- WebSocket real-time push (on-demand API calls sufficient)

## Users

| Role     | Description |
|----------|-------------|
| Admin    | Super-user. Onboards User and Merchant accounts. Views all users, merchants, and
              the full transaction audit log. Can approve/override blocked transactions. |
| Merchant | Registered business. Views profile, UPI QR code, and received transactions log. |
| User     | End consumer. Initiates payments and views their own transaction history. |

## Architecture

### Stack

| Layer       | Technology |
|-------------|------------|
| Frontend    | React 18 + Vite + Tailwind CSS + React Router v6 |
| State       | Zustand (auth/session) + TanStack Query (server state) |
| HTTP        | Axios (withCredentials: true) |
| Forms       | React Hook Form + Zod |
| QR Code     | qrcode.react |
| Backend     | Python 3.11 + FastAPI + Pydantic v2 |
| Auth        | JWT in httpOnly cookie |
| ORM         | SQLAlchemy 2.0 async + aiosqlite |
| ML          | TensorFlow/Keras MLP + scikit-learn + imbalanced-learn (SMOTE) |
| Deploy      | Docker + docker-compose (structure only for V1) |

### Project Structure

```
UPI-Guard/
├── backend/
│   ├── app/
│   │   ├── api/        # Route handlers: auth, users, merchants, transactions, admin
│   │   ├── core/       # Config, JWT utils, security middleware, CORS
│   │   ├── db/         # SQLAlchemy models, async session, DB init
│   │   ├── ml/         # Model loader + inference engine
│   │   └── schemas/    # Pydantic v2 request/response models
│   ├── ml_pipeline/    # train.py: data → SMOTE → train → save artifacts
│   ├── models/         # mlp_model.h5 + scaler.pkl (gitignored, generated locally)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/        # Axios client + TanStack Query hooks
│   │   ├── components/ # Shared UI: layout, modals, cards
│   │   ├── pages/      # Auth, User, Merchant, Admin pages
│   │   ├── store/      # Zustand auth store
│   │   └── routes/     # ProtectedRoute wrappers per role
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

### ML Model

- **Script:** `backend/ml_pipeline/train.py`
- **Data:** ~50,000 synthetic UPI transactions, ~2% fraud rate before SMOTE
- **Input Features (9):**

| Feature           | Type  | Notes |
|-------------------|-------|-------|
| hour              | int   | From transaction timestamp |
| day               | int   | Day of month |
| month             | int   | Month |
| year              | int   | Year |
| merchant_category | int   | Label-encoded (Food, Retail, Travel, etc.) |
| amount            | float | INR |
| user_age          | int   | From user profile |
| state_code        | int   | Label-encoded Indian state |
| zip_prefix        | int   | First 3 digits of ZIP |

- **Architecture:** Input(9) → Dense(128,ReLU) → BatchNorm → Dropout(0.3) → Dense(64,ReLU)
  → Dropout(0.2) → Dense(1, Sigmoid)
- **Threshold:** fraud_score >= 0.5 → BLOCKED_FRAUD
- **Artifacts:** `backend/models/mlp_model.h5` + `backend/models/scaler.pkl`

### Database Schema

```
users        (id, mobile, name, age, state, zip, role, is_active, created_at)
merchants    (id, user_id FK, upi_id, business_name, category, created_at)
transactions (id, user_id FK, merchant_id FK, amount,
              hour, day, month, year, merchant_category, user_age, state_code, zip_prefix,
              fraud_score, status, override_by_admin_id FK nullable, override_at, created_at)
otp_sessions (id, mobile, otp_hash, expires_at, used)
```

Transaction status enum: `APPROVED` | `BLOCKED_FRAUD` | `ADMIN_OVERRIDDEN`

### Auth Flow

1. User submits mobile → Backend generates 6-digit OTP, stores hashed in `otp_sessions`
2. OTP appears in mock **SMS Inbox** panel (polled from `/auth/otp-inbox/{mobile}`)
3. User submits OTP → Backend verifies hash, sets JWT in httpOnly cookie
4. JWT payload: `{ sub: user_id, role: "admin"|"merchant"|"user", exp }`
5. All protected endpoints validate JWT from cookie (not Authorization header)

## Constraints

- V1 runs locally via `uvicorn` + `npm run dev` (or `docker-compose up` after model training)
- Python 3.11+, Node 18+
- SQLite single-file DB at `backend/upi_guard.db`
- No real money, no real OTP — simulation/portfolio system

## Success Criteria

- [ ] `train.py` generates data, applies SMOTE, trains MLP, saves model.h5 + scaler.pkl
- [ ] FastAPI loads model on startup without error
- [ ] Mobile + OTP login works; OTP visible in SMS Inbox panel
- [ ] JWT in httpOnly cookie; all 3 roles reach correct dashboards
- [ ] Payment flow: both APPROVED and BLOCKED_FRAUD paths work end-to-end
- [ ] Fraud alert modal shows fraud_score on block
- [ ] ALL transactions (approved + blocked) written to DB with all 9 features + fraud_score
- [ ] Merchant panel shows scannable `upi://pay` QR code
- [ ] Admin sees full transaction audit log with all features + fraud_score
- [ ] Admin override changes BLOCKED_FRAUD → ADMIN_OVERRIDDEN in DB
- [ ] docker-compose.yml starts both services cleanly (after model is trained)
