---
phase: 2
plan: 1
wave: 1
---

# Plan 2.1: App Config + SQLAlchemy Async Models + DB Session

## Objective
Establish the data layer foundation: environment-based config (pydantic BaseSettings),
all 4 SQLAlchemy 2.0 async models (users, merchants, transactions, otp_sessions),
the async session dependency, and the DB initializer. Nothing in Phase 2 can proceed
without these — they are imported by every other backend module.

## Context
- `.gsd/SPEC.md` — Database schema (4 tables + field list + status enum)
- `backend/requirements.txt` — Pinned dependencies already installed

## Tasks

<task type="auto">
  <name>Write app config (pydantic BaseSettings from .env)</name>
  <files>
    backend/app/core/config.py
    backend/.env.example
    backend/.env
  </files>
  <action>
    ### backend/app/core/config.py

    Write a pydantic-settings BaseSettings class that reads from a `.env` file.
    Use `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`.

    ```python
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field
    import pathlib

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

        # Database
        DATABASE_URL: str = "sqlite+aiosqlite:///./upi_guard.db"

        # JWT
        JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_use_secrets_token_hex_32"
        JWT_ALGORITHM: str = "HS256"
        JWT_EXPIRE_MINUTES: int = 60

        # OTP
        OTP_TTL_SECONDS: int = 600  # 10 minutes
        OTP_LENGTH: int = 6

        # ML model paths — relative to backend/ working directory
        MODEL_PATH: str = "models/mlp_model.h5"
        SCALER_PATH: str = "models/scaler.pkl"

        # CORS
        FRONTEND_ORIGIN: str = "http://localhost:5173"

        # Admin seed (demo only — mobile used to auto-create admin on first run)
        ADMIN_MOBILE: str = "9999999999"
        ADMIN_NAME: str = "Admin"

    # Singleton — import this everywhere
    settings = Settings()
    ```

    ### backend/.env.example
    Create this file showing all configurable vars:
    ```
    # UPI Guard — Environment Variables
    # Copy to .env and fill in values

    DATABASE_URL=sqlite+aiosqlite:///./upi_guard.db
    JWT_SECRET_KEY=your-secret-key-here-use-secrets.token_hex(32)
    JWT_ALGORITHM=HS256
    JWT_EXPIRE_MINUTES=60
    OTP_TTL_SECONDS=600
    MODEL_PATH=models/mlp_model.h5
    SCALER_PATH=models/scaler.pkl
    FRONTEND_ORIGIN=http://localhost:5173
    ADMIN_MOBILE=9999999999
    ADMIN_NAME=Admin
    ```

    ### backend/.env
    Create with actual values (same as .env.example defaults — fine for local dev).
    This file is already in .gitignore.

    DO NOT use `from __future__ import annotations` — it breaks pydantic-settings in Python 3.10.
  </action>
  <verify>
    cd backend && python -c "
from app.core.config import settings
assert settings.DATABASE_URL.startswith('sqlite+aiosqlite')
assert settings.JWT_EXPIRE_MINUTES == 60
assert settings.OTP_TTL_SECONDS == 600
assert settings.ADMIN_MOBILE == '9999999999'
print('Config OK:', settings.DATABASE_URL)
"
  </verify>
  <done>
    - `from app.core.config import settings` works without error
    - settings.DATABASE_URL starts with `sqlite+aiosqlite`
    - .env.example exists with all 9 vars documented
    - .env exists with local dev defaults
  </done>
</task>

<task type="auto">
  <name>Write SQLAlchemy 2.0 async models + session + DB initializer</name>
  <files>
    backend/app/db/base.py
    backend/app/db/models.py
    backend/app/db/session.py
    backend/app/db/init_db.py
  </files>
  <action>
    ### backend/app/db/base.py
    ```python
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass
    ```

    ### backend/app/db/models.py
    Define all 4 async-compatible SQLAlchemy models. Import Base from base.py.
    Use `Mapped` + `mapped_column` (SQLAlchemy 2.0 style — NOT the old Column style).

    ```python
    import enum
    from datetime import datetime
    from typing import Optional
    from sqlalchemy import String, Integer, Float, Boolean, DateTime, Enum, ForeignKey, func
    from sqlalchemy.orm import Mapped, mapped_column, relationship
    from app.db.base import Base

    class UserRole(str, enum.Enum):
        admin = "admin"
        merchant = "merchant"
        user = "user"

    class TransactionStatus(str, enum.Enum):
        APPROVED = "APPROVED"
        BLOCKED_FRAUD = "BLOCKED_FRAUD"
        ADMIN_OVERRIDDEN = "ADMIN_OVERRIDDEN"

    class User(Base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        mobile: Mapped[str] = mapped_column(String(15), unique=True, nullable=False, index=True)
        name: Mapped[str] = mapped_column(String(100), nullable=False)
        age: Mapped[int] = mapped_column(Integer, nullable=False)
        state: Mapped[str] = mapped_column(String(50), nullable=False)
        zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
        role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.user)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
        created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
        # Relationships
        merchant: Mapped[Optional["Merchant"]] = relationship(back_populates="user", uselist=False)
        transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")

    class Merchant(Base):
        __tablename__ = "merchants"
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
        upi_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
        business_name: Mapped[str] = mapped_column(String(150), nullable=False)
        category: Mapped[str] = mapped_column(String(50), nullable=False)
        created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
        # Relationships
        user: Mapped["User"] = relationship(back_populates="merchant")
        transactions: Mapped[list["Transaction"]] = relationship(back_populates="merchant")

    class Transaction(Base):
        __tablename__ = "transactions"
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
        merchant_id: Mapped[int] = mapped_column(Integer, ForeignKey("merchants.id"), nullable=False)
        amount: Mapped[float] = mapped_column(Float, nullable=False)
        # Extracted ML features (9 total)
        hour: Mapped[int] = mapped_column(Integer, nullable=False)
        day: Mapped[int] = mapped_column(Integer, nullable=False)
        month: Mapped[int] = mapped_column(Integer, nullable=False)
        year: Mapped[int] = mapped_column(Integer, nullable=False)
        merchant_category: Mapped[int] = mapped_column(Integer, nullable=False)
        user_age: Mapped[int] = mapped_column(Integer, nullable=False)
        state_code: Mapped[int] = mapped_column(Integer, nullable=False)
        zip_prefix: Mapped[int] = mapped_column(Integer, nullable=False)
        # Fraud decision
        fraud_score: Mapped[float] = mapped_column(Float, nullable=False)
        status: Mapped[TransactionStatus] = mapped_column(
            Enum(TransactionStatus), nullable=False, default=TransactionStatus.APPROVED
        )
        # Admin override (nullable)
        override_by_admin_id: Mapped[Optional[int]] = mapped_column(
            Integer, ForeignKey("users.id"), nullable=True
        )
        override_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
        # Relationships
        user: Mapped["User"] = relationship(back_populates="transactions", foreign_keys=[user_id])
        merchant: Mapped["Merchant"] = relationship(back_populates="transactions")

    class OtpSession(Base):
        __tablename__ = "otp_sessions"
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        mobile: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
        otp_hash: Mapped[str] = mapped_column(String(200), nullable=False)
        otp_plain: Mapped[str] = mapped_column(String(10), nullable=False)  # stored for SMS inbox mock
        expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
        used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
        created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ```

    NOTE on otp_plain: For the SMS Inbox mock (dev/demo only), we store the plaintext OTP
    alongside the hash so `/auth/otp-inbox/{mobile}` can return it without reversing the hash.
    This is intentional for the demo — in production this field would not exist.

    ### backend/app/db/session.py
    ```python
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from typing import AsyncGenerator
    from app.core.config import settings

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},  # SQLite only
    )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    ```

    ### backend/app/db/init_db.py
    ```python
    from sqlalchemy.ext.asyncio import AsyncEngine
    from app.db.base import Base
    from app.db import models  # import so all models are registered with Base.metadata

    async def init_db(engine: AsyncEngine) -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    ```
  </action>
  <verify>
    cd backend && python -c "
import asyncio
from app.db.session import engine
from app.db.init_db import init_db
from app.db.models import User, Merchant, Transaction, OtpSession, UserRole, TransactionStatus

async def test():
    await init_db(engine)
    print('DB tables created OK')
    # Verify models have correct attributes
    assert hasattr(User, 'mobile')
    assert hasattr(Transaction, 'fraud_score')
    assert hasattr(Transaction, 'override_by_admin_id')
    assert hasattr(OtpSession, 'otp_plain')
    assert TransactionStatus.BLOCKED_FRAUD.value == 'BLOCKED_FRAUD'
    print('Models OK')
    await engine.dispose()

asyncio.run(test())
" && python -c "import pathlib; db=pathlib.Path('upi_guard.db'); print('DB file created:', db.exists(), db.stat().st_size, 'bytes')"
  </verify>
  <done>
    - All 4 models import without error
    - `init_db(engine)` creates the SQLite DB file (`backend/upi_guard.db`)
    - `upi_guard.db` exists with size > 0 after running init_db
    - TransactionStatus enum has APPROVED, BLOCKED_FRAUD, ADMIN_OVERRIDDEN values
    - OtpSession has otp_plain field (for SMS inbox mock)
  </done>
</task>

## Success Criteria
- [ ] `from app.core.config import settings` works; settings.DATABASE_URL starts with `sqlite+aiosqlite`
- [ ] `.env.example` exists with all 9 config vars documented
- [ ] All 4 SQLAlchemy models import without error
- [ ] `init_db(engine)` creates `backend/upi_guard.db` successfully
- [ ] TransactionStatus enum has all 3 values (APPROVED, BLOCKED_FRAUD, ADMIN_OVERRIDDEN)
