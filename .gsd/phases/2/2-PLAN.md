---
phase: 2
plan: 2
wave: 2
---

# Plan 2.2: Pydantic Schemas + Model Loader + FastAPI App + Admin Seed

## Objective
Complete the backend foundation: Pydantic v2 request/response schemas, the ML model
loader singleton, the FastAPI application with lifespan (DB init + model load on startup),
CORS middleware, and the admin account seeder. After this plan, `uvicorn app.main:app`
must start cleanly, load the model, initialize the DB, and respond to `GET /health`.

**Depends on:** Plan 2.1 (config, models, session must exist)

## Context
- `.gsd/SPEC.md` — Auth flow, DB schema, feature list, admin seed (mobile: 9999999999)
- `backend/app/core/config.py` — Settings singleton (from Plan 2.1)
- `backend/app/db/models.py` — SQLAlchemy models (from Plan 2.1)
- `backend/app/db/session.py` — engine + get_db (from Plan 2.1)
- `backend/app/db/init_db.py` — init_db function (from Plan 2.1)

## Tasks

<task type="auto">
  <name>Write Pydantic v2 schemas + ML model loader singleton</name>
  <files>
    backend/app/schemas/user.py
    backend/app/schemas/merchant.py
    backend/app/schemas/transaction.py
    backend/app/schemas/auth.py
    backend/app/ml/loader.py
  </files>
  <action>
    ### backend/app/schemas/auth.py
    ```python
    from pydantic import BaseModel, field_validator

    class OtpRequestSchema(BaseModel):
        mobile: str

        @field_validator("mobile")
        @classmethod
        def mobile_must_be_10_digits(cls, v: str) -> str:
            v = v.strip()
            if not v.isdigit() or len(v) != 10:
                raise ValueError("Mobile must be exactly 10 digits")
            return v

    class OtpVerifySchema(BaseModel):
        mobile: str
        otp: str

    class TokenResponseSchema(BaseModel):
        role: str
        user_id: int
        name: str
        message: str = "Login successful"
    ```

    ### backend/app/schemas/user.py
    ```python
    from pydantic import BaseModel, field_validator
    from datetime import datetime
    from typing import Optional
    from app.db.models import UserRole

    class UserCreateSchema(BaseModel):
        mobile: str
        name: str
        age: int
        state: str
        zip_code: str
        role: UserRole = UserRole.user

        @field_validator("age")
        @classmethod
        def age_range(cls, v: int) -> int:
            if not (18 <= v <= 100):
                raise ValueError("Age must be between 18 and 100")
            return v

        @field_validator("mobile")
        @classmethod
        def mobile_digits(cls, v: str) -> str:
            if not v.strip().isdigit() or len(v.strip()) != 10:
                raise ValueError("Mobile must be 10 digits")
            return v.strip()

    class UserResponseSchema(BaseModel):
        model_config = {"from_attributes": True}
        id: int
        mobile: str
        name: str
        age: int
        state: str
        zip_code: str
        role: UserRole
        is_active: bool
        created_at: datetime
    ```

    ### backend/app/schemas/merchant.py
    ```python
    from pydantic import BaseModel, field_validator
    from datetime import datetime

    class MerchantCreateSchema(BaseModel):
        user_mobile: str          # admin looks up user by mobile
        upi_id: str
        business_name: str
        category: str             # e.g. "Food", "Retail", "Travel"

        @field_validator("upi_id")
        @classmethod
        def upi_format(cls, v: str) -> str:
            if "@" not in v:
                raise ValueError("UPI ID must contain @")
            return v.lower().strip()

    class MerchantResponseSchema(BaseModel):
        model_config = {"from_attributes": True}
        id: int
        user_id: int
        upi_id: str
        business_name: str
        category: str
        created_at: datetime
        # Denormalized for convenience
        user_name: str = ""
        user_mobile: str = ""
    ```

    ### backend/app/schemas/transaction.py
    ```python
    from pydantic import BaseModel, field_validator
    from datetime import datetime
    from typing import Optional
    from app.db.models import TransactionStatus

    class PaymentRequestSchema(BaseModel):
        merchant_upi: str
        amount: float

        @field_validator("amount")
        @classmethod
        def amount_positive(cls, v: float) -> float:
            if v <= 0:
                raise ValueError("Amount must be positive")
            if v > 1_000_000:
                raise ValueError("Amount exceeds maximum allowed")
            return round(v, 2)

    class TransactionResponseSchema(BaseModel):
        model_config = {"from_attributes": True}
        id: int
        user_id: int
        merchant_id: int
        amount: float
        hour: int
        day: int
        month: int
        year: int
        merchant_category: int
        user_age: int
        state_code: int
        zip_prefix: int
        fraud_score: float
        status: TransactionStatus
        override_by_admin_id: Optional[int]
        override_at: Optional[datetime]
        created_at: datetime
        # Denormalized
        merchant_upi: str = ""
        merchant_name: str = ""
        user_name: str = ""

    class PaymentResponseSchema(BaseModel):
        transaction_id: int
        status: TransactionStatus
        fraud_score: float
        amount: float
        merchant_upi: str
        message: str

    class OverrideResponseSchema(BaseModel):
        transaction_id: int
        previous_status: str
        new_status: str = "ADMIN_OVERRIDDEN"
        message: str = "Transaction approved by admin override"
    ```

    ### backend/app/ml/loader.py
    Write the model loader singleton. This module is imported by the FastAPI lifespan
    to load both artifacts once at startup. The `get_model_loader()` function returns
    the same ModelLoader instance every time (module-level singleton).

    ```python
    import pickle
    import pathlib
    from dataclasses import dataclass, field
    from typing import Optional
    import numpy as np

    @dataclass
    class ModelLoader:
        model: Optional[object] = field(default=None, repr=False)
        scaler: Optional[object] = field(default=None, repr=False)
        _loaded: bool = False

        def load(self, model_path: str, scaler_path: str) -> None:
            import tensorflow as tf
            import os
            os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
            model_p = pathlib.Path(model_path)
            scaler_p = pathlib.Path(scaler_path)
            if not model_p.exists():
                raise FileNotFoundError(f"Model not found: {model_p.resolve()}")
            if not scaler_p.exists():
                raise FileNotFoundError(f"Scaler not found: {scaler_p.resolve()}")
            self.model = tf.keras.models.load_model(str(model_p))
            with open(scaler_p, "rb") as f:
                self.scaler = pickle.load(f)
            self._loaded = True
            print(f"[ML] Model loaded: {model_p.name}")
            print(f"[ML] Scaler loaded: {scaler_p.name}")

        def predict(self, features: list[float]) -> float:
            if not self._loaded:
                raise RuntimeError("Model not loaded. Call load() first.")
            arr = np.array([features], dtype=np.float32)
            scaled = self.scaler.transform(arr)
            score = float(self.model.predict(scaled, verbose=0)[0][0])
            return score

        @property
        def is_loaded(self) -> bool:
            return self._loaded

    # Module-level singleton
    _loader_instance: Optional[ModelLoader] = None

    def get_model_loader() -> ModelLoader:
        global _loader_instance
        if _loader_instance is None:
            _loader_instance = ModelLoader()
        return _loader_instance
    ```
  </action>
  <verify>
    cd backend && python -c "
from app.schemas.auth import OtpRequestSchema, OtpVerifySchema
from app.schemas.user import UserCreateSchema, UserResponseSchema
from app.schemas.merchant import MerchantCreateSchema
from app.schemas.transaction import PaymentRequestSchema, PaymentResponseSchema
from app.ml.loader import get_model_loader

# Schema validation
r = OtpRequestSchema(mobile='9876543210')
assert r.mobile == '9876543210'
try:
    OtpRequestSchema(mobile='123abc')
    assert False, 'should have failed'
except Exception:
    pass

pr = PaymentRequestSchema(merchant_upi='shop@upi', amount=500.0)
assert pr.amount == 500.0

# Loader singleton
ml = get_model_loader()
assert get_model_loader() is ml, 'Not a singleton'
assert not ml.is_loaded

print('Schemas OK. Loader singleton OK.')
"
  </verify>
  <done>
    - All 5 schema files import without error
    - OtpRequestSchema rejects non-10-digit mobile
    - PaymentRequestSchema validates amount > 0
    - get_model_loader() returns same instance every call
    - ml.is_loaded is False before load() called
  </done>
</task>

<task type="auto">
  <name>Write FastAPI app with lifespan + CORS + health endpoint + admin seed</name>
  <files>
    backend/app/main.py
    backend/app/core/security.py
  </files>
  <action>
    ### backend/app/core/security.py
    JWT utility functions used by auth routes (Phase 3). Write them now so main.py
    and the admin seed can import `get_password_hash` immediately.

    ```python
    from datetime import datetime, timedelta, timezone
    from typing import Optional, Any
    from jose import jwt, JWTError
    from passlib.context import CryptContext
    from fastapi import Response, HTTPException, status
    from app.core.config import settings

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_password_hash(plain: str) -> str:
        return pwd_context.hash(plain)

    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        )
        to_encode["exp"] = expire
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def decode_token(token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token: {e}",
            )

    def set_auth_cookie(response: Response, token: str) -> None:
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,      # Set True in production (requires HTTPS)
            samesite="lax",    # "strict" breaks cross-origin dev; use lax for local dev
            max_age=settings.JWT_EXPIRE_MINUTES * 60,
            path="/",
        )

    def clear_auth_cookie(response: Response) -> None:
        response.delete_cookie(key="access_token", path="/")
    ```

    NOTE: `secure=False` and `samesite="lax"` are intentional for local HTTP dev.
    The plan originally specified `SameSite=Strict` but that breaks the React dev
    server (different port = cross-site). Use "lax" for local; document the production
    change in a comment.

    ### backend/app/main.py
    Write the FastAPI application with:
    1. Lifespan context manager (startup: init_db + load model + seed admin; shutdown: dispose engine)
    2. CORSMiddleware configured for React dev server
    3. A `GET /health` endpoint (no auth required)
    4. Router includes for all API groups (stubs — routers will be written in Phases 3-4)

    ```python
    import os
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    from contextlib import asynccontextmanager
    from datetime import datetime, timezone
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from app.core.config import settings
    from app.db.session import engine, AsyncSessionLocal
    from app.db.init_db import init_db
    from app.ml.loader import get_model_loader

    # --------------------------------------------------------------------------
    # Admin seed helper — called once after DB init
    # --------------------------------------------------------------------------
    async def seed_admin() -> None:
        from sqlalchemy import select
        from app.db.models import User, UserRole
        from app.core.security import get_password_hash

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.role == UserRole.admin)
            )
            if result.scalar_one_or_none() is None:
                admin = User(
                    mobile=settings.ADMIN_MOBILE,
                    name=settings.ADMIN_NAME,
                    age=30,
                    state="Telangana",
                    zip_code="500001",
                    role=UserRole.admin,
                    is_active=True,
                )
                session.add(admin)
                await session.commit()
                print(f"[DB] Admin seeded — mobile: {settings.ADMIN_MOBILE}")
            else:
                print("[DB] Admin already exists — skipping seed")

    # --------------------------------------------------------------------------
    # FastAPI lifespan (startup + shutdown)
    # --------------------------------------------------------------------------
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        print("[DB] Initializing database...")
        await init_db(engine)
        print("[DB] Database ready.")

        await seed_admin()

        print("[ML] Loading fraud detection model...")
        ml = get_model_loader()
        ml.load(settings.MODEL_PATH, settings.SCALER_PATH)
        print(f"[ML] Model ready. is_loaded={ml.is_loaded}")

        yield  # Application runs here

        # Shutdown
        print("[DB] Disposing engine...")
        await engine.dispose()
        print("[APP] Shutdown complete.")

    # --------------------------------------------------------------------------
    # FastAPI app
    # --------------------------------------------------------------------------
    app = FastAPI(
        title="UPI Guard API",
        description="Real-Time UPI Fraud Detection System",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS — allow React dev server with credentials (cookies)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_credentials=True,   # Required for httpOnly cookie
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --------------------------------------------------------------------------
    # Health check
    # --------------------------------------------------------------------------
    @app.get("/health", tags=["health"])
    async def health_check():
        ml = get_model_loader()
        return {
            "status": "ok",
            "model_loaded": ml.is_loaded,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # --------------------------------------------------------------------------
    # Routers (to be registered in Phases 3 + 4)
    # --------------------------------------------------------------------------
    # from app.api import auth, admin, transactions, merchants
    # app.include_router(auth.router, prefix="/auth", tags=["auth"])
    # app.include_router(admin.router, prefix="/admin", tags=["admin"])
    # app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
    # app.include_router(merchants.router, prefix="/merchants", tags=["merchants"])
    ```

    The router includes are COMMENTED OUT. They will be uncommented as each Phase
    (3, 4) creates the actual route files. DO NOT uncomment now — the files don't exist.
  </action>
  <verify>
    cd backend && python -c "
import asyncio, os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Test 1: App imports without error
from app.main import app
print('FastAPI app imported OK')

# Test 2: security utils work
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
h = get_password_hash('123456')
assert verify_password('123456', h), 'Hash verify failed'
assert not verify_password('wrong', h), 'Should reject wrong password'

token = create_access_token({'sub': '1', 'role': 'admin'})
payload = decode_token(token)
assert payload['sub'] == '1'
assert payload['role'] == 'admin'
print('Security utils OK')

# Test 3: health endpoint exists
routes = [r.path for r in app.routes]
assert '/health' in routes, f'/health not found in routes: {routes}'
print('Routes OK:', routes)
" && python -c "
import asyncio, httpx
from asgi_lifespan import LifespanManager
from app.main import app

async def test_health():
    async with LifespanManager(app):
        async with httpx.AsyncClient(app=app, base_url='http://test') as client:
            r = await client.get('/health')
            assert r.status_code == 200
            data = r.json()
            assert data['status'] == 'ok'
            assert data['model_loaded'] == True
            print('Health check PASS:', data)

asyncio.run(test_health())
"
  </verify>
  <done>
    - `from app.main import app` succeeds without error
    - JWT create_access_token + decode_token round-trip works
    - verify_password correctly validates and rejects passwords
    - `GET /health` returns 200 with `{"status": "ok", "model_loaded": true}`
    - Admin user exists in DB after lifespan startup
    - `uvicorn app.main:app --reload` starts without error (manual verification)
  </done>
</task>

## Success Criteria
- [ ] All 5 schema files import without error; validation logic works as spec'd
- [ ] `get_model_loader()` returns singleton; is_loaded=False before startup
- [ ] `from app.main import app` succeeds without error
- [ ] JWT round-trip works: create_access_token → decode_token recovers payload
- [ ] `GET /health` returns 200 + `{"status": "ok", "model_loaded": true}` after lifespan
- [ ] Admin user seeded in DB (mobile: 9999999999, role: admin) on first startup
