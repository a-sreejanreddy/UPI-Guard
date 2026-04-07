"""
app/main.py — UPI Guard FastAPI Application

Startup order (via lifespan):
  1. Create all DB tables (init_db)
  2. Seed admin user if none exists
  3. Load MLP model + scaler (get_model_loader().load(...))

Run locally:
  cd backend && uvicorn app.main:app --reload --port 8000
"""
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


# ── Admin seed ────────────────────────────────────────────────────────────────

async def _seed_admin() -> None:
    """
    Create a default admin account on first startup.
    Mobile: settings.ADMIN_MOBILE (default: 9999999999)
    """
    from sqlalchemy import select
    from app.db.models import User, UserRole

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
            _masked = "*" * (len(settings.ADMIN_MOBILE) - 4) + settings.ADMIN_MOBILE[-4:]
            print(f"[DB] Admin seeded  : mobile={_masked}, role=admin")
        else:
            print("[DB] Admin exists  : skipping seed")


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────
    print("[APP] Starting UPI Guard API...")

    print("[DB]  Initializing database tables...")
    await init_db(engine)
    print("[DB]  Tables ready.")

    await _seed_admin()

    print("[ML]  Loading fraud detection model...")
    ml = get_model_loader()
    ml.load(settings.MODEL_PATH, settings.SCALER_PATH)
    print(f"[ML]  Model ready. loaded={ml.is_loaded}")

    print("[APP] Startup complete. Serving at http://localhost:8000")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    print("[DB]  Disposing engine...")
    await engine.dispose()
    print("[APP] Shutdown complete.")


# ── FastAPI application ───────────────────────────────────────────────────────

app = FastAPI(
    title="UPI Guard API",
    description=(
        "Real-Time UPI Fraud Detection System — "
        "MLP-powered fraud inference with role-based access control."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allow React dev server to send cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,   # Required for httpOnly cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"], summary="Server health + model status")
async def health_check():
    ml = get_model_loader()
    return {
        "status": "ok",
        "model_loaded": ml.is_loaded,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


# ── Routers (registered as phases are implemented) ────────────────────────────
# Phase 3 will add:
#   from app.api import auth, admin
#   app.include_router(auth.router,  prefix="/auth",   tags=["auth"])
#   app.include_router(admin.router, prefix="/admin",  tags=["admin"])
#
# Phase 4 will add:
#   from app.api import transactions, merchants
#   app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
#   app.include_router(merchants.router,    prefix="/merchants",    tags=["merchants"])
