# ROADMAP.md

> **Current Phase**: Not started
> **Milestone**: v1.0 — Local MVP

## Must-Haves (from SPEC)

- [ ] MLP model trained and served via FastAPI
- [ ] Mobile + OTP auth with JWT httpOnly cookie
- [ ] Role-based dashboards: Admin, Merchant, User
- [ ] Real-time fraud inference with fraud_score returned
- [ ] Complete transaction audit trail (all outcomes logged)
- [ ] Admin override for blocked transactions
- [ ] UPI QR code generation for merchants
- [ ] Docker-ready project structure

---

## Phases

### Phase 1: ML Pipeline
**Status**: Complete
**Objective**: Produce the trained model artifacts that the entire backend depends on.

**Deliverables:**
- `backend/ml_pipeline/train.py` — standalone script, runs top to bottom with no args
- ~50,000 synthetic UPI transaction records, ~2% fraud rate before SMOTE
- SMOTE applied to balance classes to 1:1 ratio
- MLP trained: Input(9)→Dense(128,ReLU)→BatchNorm→Dropout(0.3)→Dense(64,ReLU)→Dropout(0.2)→Dense(1,Sigmoid)
- `backend/models/mlp_model.h5` and `backend/models/scaler.pkl` saved
- Console output: accuracy, precision, recall, F1, AUC-ROC on held-out test set

**Tasks:**
- [ ] Create backend/ and ml_pipeline/ directory structure
- [ ] Write synthetic data generator (9 features + binary fraud label)
- [ ] Apply SMOTE from imbalanced-learn
- [ ] Define and compile MLP with Keras (Adam optimizer, binary_crossentropy)
- [ ] Train with EarlyStopping and ModelCheckpoint callbacks
- [ ] Evaluate on held-out test set, print classification report + AUC
- [ ] Save mlp_model.h5 and scaler.pkl to backend/models/
- [ ] Add backend/models/*.h5 and backend/models/*.pkl to .gitignore

---

### Phase 2: Backend Foundation
**Status**: Complete
**Objective**: FastAPI application skeleton with database, config, and model loading in place.

**Deliverables:**
- FastAPI app with CORS configured for React dev server (localhost:5173)
- SQLAlchemy 2.0 async models for all 4 tables
- DB auto-initialized on startup (create_all)
- Model loader singleton: loads mlp_model.h5 + scaler.pkl via FastAPI lifespan
- Pydantic v2 schemas for all entities
- `.env` config (JWT_SECRET, DB_URL, OTP_TTL_SECONDS, MODEL_PATH, SCALER_PATH)
- `requirements.txt` with pinned versions

**Tasks:**
- [x] Scaffold FastAPI app with lifespan context manager
- [x] Define SQLAlchemy async models (users, merchants, transactions, otp_sessions)
- [x] Write async DB session dependency (get_db)
- [x] DB init: create_all on lifespan startup
- [x] Write model loader (singleton, loaded once at startup via lifespan)
- [x] Write all Pydantic v2 request/response schemas
- [x] Configure CORS (allow React origin, allow credentials=True)
- [x] Setup pydantic BaseSettings config from .env
- [x] Write requirements.txt (fastapi, uvicorn, sqlalchemy, aiosqlite, python-jose,
      passlib, tensorflow, scikit-learn, imbalanced-learn, python-multipart, python-dotenv)
- [x] Seed default admin account on first startup (hardcoded mobile for demo)

---

### Phase 3: Auth & User Management API
**Status**: Complete
**Objective**: Complete authentication system and admin user/merchant management endpoints.

**Deliverables:**
- `POST /auth/request-otp` — generate and store hashed OTP (6-digit, TTL 10min)
- `GET  /auth/otp-inbox/{mobile}` — return plaintext OTP (dev/demo only, no auth required)
- `POST /auth/verify-otp` — verify OTP, issue JWT in httpOnly cookie
- `POST /auth/logout` — clear JWT cookie
- `GET  /auth/me` — return current user info from JWT
- `POST /admin/users` — admin creates a user account (admin role required)
- `POST /admin/merchants` — admin creates a merchant + links to user account
- `GET  /admin/users` — list all users
- `GET  /admin/merchants` — list all merchants
- JWT dependency functions: get_current_user, require_role(role)

**Tasks:**
- [x] Write JWT utils: create_access_token, decode_token, set_jwt_cookie, clear_jwt_cookie
- [x] Write get_current_user dependency (reads JWT from cookie, decodes, returns user)
- [x] Write require_role(role) dependency factory
- [x] Implement /auth/request-otp (hash OTP with bcrypt, store with expiry)
- [x] Implement /auth/otp-inbox/{mobile} (lookup latest unused, unexpired OTP)
- [x] Implement /auth/verify-otp (verify hash, mark used, set cookie, return role)
- [x] Implement /auth/logout (delete cookie)
- [x] Implement /auth/me (return user from JWT)
- [x] Implement admin user CRUD endpoints with role guard
- [x] Seed admin on first startup (mobile: 9999999999, auto-generate first OTP)

---

### Phase 4: Transaction & Fraud Inference API
**Status**: ✅ Complete
**Objective**: Real-time fraud inference on incoming payments, comprehensive logging, admin override.

**Deliverables:**
- `POST /transactions/pay` — full payment flow: feature extraction → scale → MLP infer → log → respond
- `GET  /transactions/my` — authenticated user's transaction history
- `GET  /transactions/merchant/{merchant_id}` — received transactions for a merchant
- `GET  /admin/transactions` — full audit log (all rows, all 9 feature columns + fraud_score)
- `POST /admin/transactions/{id}/override` — approve a BLOCKED_FRAUD transaction
- All transactions written to DB regardless of fraud outcome
- Fraud response body includes: status, fraud_score (float), transaction_id, message

**Fraud decision logic:**
- Extract 9 features from request + user profile + current timestamp
- StandardScaler.transform(features)
- mlp_model.predict(scaled) → fraud_score
- If fraud_score >= 0.5: status=BLOCKED_FRAUD, return fraud alert
- If fraud_score < 0.5: status=APPROVED, return success
- In BOTH cases: write full transaction row to DB

**Tasks:**
- [x] Write feature extractor service (decomposes timestamp, encodes state/category/zip)
- [x] Write inference service (wraps model.predict, returns float fraud_score)
- [x] Implement POST /transactions/pay (role=user required)
- [x] Write transaction DB write for APPROVED and BLOCKED_FRAUD paths
- [x] Implement GET /transactions/my
- [x] Implement GET /transactions/merchant/{merchant_id} (role=merchant required)
- [x] Implement GET /admin/transactions (role=admin, all columns returned)
- [x] Implement POST /admin/transactions/{id}/override (sets status, records admin_id + timestamp)

---

### Phase 5: Frontend Foundation
**Status**: ✅ Complete
**Objective**: React application scaffold with all config, routing, state, and shared UI ready.

**Deliverables:**
- Vite + React 18 + TypeScript project in frontend/
- Tailwind CSS configured (tailwind.config.js, index.css)
- React Router v6 route tree for all 3 role dashboards
- ProtectedRoute component (reads Zustand auth store, redirects if unauthenticated or wrong role)
- Zustand auth store: { user, role, isAuthenticated, setAuth, logout }
- Axios client: baseURL=http://localhost:8000, withCredentials: true
- TanStack Query provider (QueryClient with staleTime=30s)
- Shared components: Layout, Navbar (role-aware links), LoadingSpinner, ErrorBoundary

**Tasks:**
- [ ] npx create-vite frontend --template react-ts
- [ ] Install Tailwind CSS and configure (postcss, tailwind.config)
- [ ] Install: react-router-dom, zustand, @tanstack/react-query, axios,
      react-hook-form, @hookform/resolvers, zod, qrcode.react, @types/qrcode.react
- [ ] Create Zustand auth store with localStorage persist
- [ ] Create Axios client instance with withCredentials
- [ ] Wrap main.tsx with QueryClientProvider and BrowserRouter
- [ ] Define route constants and full route tree
- [ ] Build ProtectedRoute (role-aware redirect)
- [ ] Build Layout + Navbar components (links conditional on role)
- [ ] Build LoadingSpinner and ErrorBoundary

---

### Phase 6: Auth UI & User Dashboard
**Status**: Not Started
**Objective**: Authentication flow UI and the User role dashboard — payment and history.

**Deliverables:**
- **Login Page:**
  - Step 1: Mobile number input → "Send OTP" → calls POST /auth/request-otp
  - Step 2: OTP input → "Verify" → calls POST /auth/verify-otp → redirects by role
  - **SMS Inbox Panel:** visible after OTP requested, polls GET /auth/otp-inbox/{mobile}
    every 3s, shows OTP in a styled phone-message bubble

- **User Dashboard (/user):**
  - Pay Now form: Merchant UPI ID field, Amount field → POST /transactions/pay
  - Success toast on APPROVED
  - Fraud Alert Modal on BLOCKED_FRAUD: large fraud_score gauge/percentage, transaction
    details, "Understood" dismiss button
  - Transaction History table: columns — Merchant, Amount, Time, Status badge, fraud_score
    Status badge colors: APPROVED=green, BLOCKED_FRAUD=red, ADMIN_OVERRIDDEN=amber

**Tasks:**
- [ ] Build LoginPage (two-step: mobile → OTP, React Hook Form + Zod validation)
- [ ] Build SMSInboxPanel (polling useQuery, OTP displayed in bubble UI)
- [ ] Build UserDashboard page layout
- [ ] Build PaymentForm (merchant_upi + amount, useMutation)
- [ ] Build FraudAlertModal (fraud_score as % with color gradient, details)
- [ ] Build TransactionHistory table (TanStack Query, status badges)
- [ ] Wire role-based redirect after successful login

---

### Phase 7: Merchant & Admin Dashboards
**Status**: Not Started
**Objective**: Complete Merchant and Admin role dashboards.

**Deliverables:**
- **Merchant Dashboard (/merchant):**
  - Profile card: business name, UPI ID, category
  - UPI QR Code: qrcode.react rendering `upi://pay?pa={upi_id}&pn={name}&mc={category_code}`
  - Received Transactions table: Amount, From (user name), Time, Status

- **Admin Control Panel (/admin) with 3 tabs:**
  - **Users tab:** Table of all users (name, mobile, age, state, role) + "Onboard User" button
    → OnboardUserModal form (name, mobile, age, state, zip, role=user)
  - **Merchants tab:** Table of all merchants + "Onboard Merchant" button
    → OnboardMerchantModal form (user_id or mobile, business_name, upi_id, category)
  - **Transactions tab:** Full audit log table showing ALL 9 feature columns + fraud_score + status
    - Status filter dropdown (All / APPROVED / BLOCKED_FRAUD / ADMIN_OVERRIDDEN)
    - BLOCKED_FRAUD rows: "Override" button → OverrideConfirmModal → POST /admin/transactions/{id}/override
    - ADMIN_OVERRIDDEN rows: show "Overridden by Admin #{id} at {time}" tooltip/badge

**Tasks:**
- [ ] Build MerchantDashboard page layout
- [ ] Build MerchantProfileCard component
- [ ] Build UPIQRCode component (qrcode.react, correct upi:// URI construction)
- [ ] Build MerchantTransactions table
- [ ] Build AdminDashboard page with tab navigation (Users / Merchants / Transactions)
- [ ] Build UserManagement tab (table + OnboardUserModal with React Hook Form)
- [ ] Build MerchantManagement tab (table + OnboardMerchantModal)
- [ ] Build TransactionAuditLog tab (all feature columns, status filter, Override button)
- [ ] Build OverrideConfirmModal
- [ ] Connect all components to TanStack Query hooks (queries + mutations)

---

### Phase 8: Polish & Docker-Ready Structure
**Status**: Not Started
**Objective**: Production-quality finishing: error handling, Docker config, documentation.

**Deliverables:**
- `backend/Dockerfile` — Python 3.11 slim image
- `frontend/Dockerfile` — Node build stage + nginx serve stage
- `docker-compose.yml` — orchestrates both services; volume mounts for DB and models dir
- `.env.example` — all required variables with comments
- Loading skeletons on all data-fetching components (Tailwind animate-pulse)
- Axios response interceptor → toast notifications for API errors
- Consistent Tailwind design system (color tokens, typography, spacing)
- `README.md` — setup guide (prerequisites, local run, docker run, architecture overview)
- Final .gitignore audit

**Tasks:**
- [ ] Write backend/Dockerfile
- [ ] Write frontend/Dockerfile (multi-stage: build + nginx)
- [ ] Write docker-compose.yml (backend + frontend + shared .env)
- [ ] Write .env.example with all vars documented
- [ ] Add Axios interceptor for error handling + toast (react-hot-toast or similar)
- [ ] Add loading skeletons to all tables and cards
- [ ] Audit and finalize Tailwind color system
- [ ] Write comprehensive README.md
- [ ] Final .gitignore audit (models/, *.db, .env, node_modules, __pycache__, dist/)
- [ ] End-to-end smoke test: full APPROVED and BLOCKED_FRAUD flows both work
