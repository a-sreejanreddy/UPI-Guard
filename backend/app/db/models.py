"""
app/db/models.py — SQLAlchemy 2.0 async ORM models

All 4 tables: users, merchants, transactions, otp_sessions
Uses Mapped + mapped_column (SQLAlchemy 2.0 typed style).
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey,
    Integer, String, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin    = "admin"
    merchant = "merchant"
    user     = "user"


class TransactionStatus(str, enum.Enum):
    APPROVED         = "APPROVED"
    BLOCKED_FRAUD    = "BLOCKED_FRAUD"
    ADMIN_OVERRIDDEN = "ADMIN_OVERRIDDEN"


# ── Merchant category encoding ─────────────────────────────────────────────────
# Must stay in sync with ml_pipeline/generate_data.py
MERCHANT_CATEGORY_MAP = {
    "Food":          0,
    "Retail":        1,
    "Travel":        2,
    "Entertainment": 3,
    "Healthcare":    4,
    "Education":     5,
    "Utilities":     6,
    "Other":         7,
}

# State code encoding (0-indexed)
STATE_CODE_MAP = {
    "Andhra Pradesh": 0, "Arunachal Pradesh": 1, "Assam": 2,
    "Bihar": 3, "Chhattisgarh": 4, "Goa": 5, "Gujarat": 6,
    "Haryana": 7, "Himachal Pradesh": 8, "Jharkhand": 9,
    "Karnataka": 10, "Kerala": 11, "Madhya Pradesh": 12,
    "Maharashtra": 13, "Manipur": 14, "Meghalaya": 15,
    "Mizoram": 16, "Nagaland": 17, "Odisha": 18, "Punjab": 19,
    "Rajasthan": 20, "Sikkim": 21, "Tamil Nadu": 22, "Telangana": 23,
    "Tripura": 24, "Uttar Pradesh": 25, "Uttarakhand": 26,
    "West Bengal": 27, "Delhi": 28,
}


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id:         Mapped[int]      = mapped_column(Integer,     primary_key=True, autoincrement=True)
    mobile:     Mapped[str]      = mapped_column(String(15),  unique=True, nullable=False, index=True)
    name:       Mapped[str]      = mapped_column(String(100), nullable=False)
    age:        Mapped[int]      = mapped_column(Integer,     nullable=False)
    state:      Mapped[str]      = mapped_column(String(50),  nullable=False)
    zip_code:   Mapped[str]      = mapped_column(String(10),  nullable=False)
    role:       Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.user)
    is_active:  Mapped[bool]     = mapped_column(Boolean,     default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime,    server_default=func.now())

    # Relationships
    merchant:     Mapped[Optional["Merchant"]]    = relationship(back_populates="user", uselist=False)
    transactions: Mapped[list["Transaction"]]     = relationship(
        back_populates="user",
        foreign_keys="Transaction.user_id",
    )


class Merchant(Base):
    __tablename__ = "merchants"

    id:            Mapped[int]      = mapped_column(Integer,      primary_key=True, autoincrement=True)
    user_id:       Mapped[int]      = mapped_column(Integer,      ForeignKey("users.id"), unique=True, nullable=False)
    upi_id:        Mapped[str]      = mapped_column(String(100),  unique=True, nullable=False, index=True)
    business_name: Mapped[str]      = mapped_column(String(150),  nullable=False)
    category:      Mapped[str]      = mapped_column(String(50),   nullable=False)
    created_at:    Mapped[datetime] = mapped_column(DateTime,     server_default=func.now())

    # Relationships
    user:         Mapped["User"]             = relationship(back_populates="merchant")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="merchant")


class Transaction(Base):
    __tablename__ = "transactions"

    id:          Mapped[int]              = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:     Mapped[int]              = mapped_column(Integer, ForeignKey("users.id"),     nullable=False)
    merchant_id: Mapped[int]              = mapped_column(Integer, ForeignKey("merchants.id"), nullable=False)
    amount:      Mapped[float]            = mapped_column(Float,   nullable=False)

    # ── 9 ML features (stored for audit trail) ──────────────────────
    hour:              Mapped[int]   = mapped_column(Integer, nullable=False)
    day:               Mapped[int]   = mapped_column(Integer, nullable=False)
    month:             Mapped[int]   = mapped_column(Integer, nullable=False)
    year:              Mapped[int]   = mapped_column(Integer, nullable=False)
    merchant_category: Mapped[int]   = mapped_column(Integer, nullable=False)
    user_age:          Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    state_code:        Mapped[int]   = mapped_column(Integer, nullable=False)
    zip_prefix:        Mapped[int]   = mapped_column(Integer, nullable=False)

    # ── Idempotency (nullable because it didn't exist before) ────
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uix_user_idempotency"),
    )

    # ── Fraud decision ───────────────────────────────────────────────
    fraud_score: Mapped[float]             = mapped_column(Float, nullable=False)
    status:      Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), nullable=False, default=TransactionStatus.APPROVED
    )

    # ── Admin override (nullable) ────────────────────────────────────
    override_by_admin_id: Mapped[Optional[int]]      = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    override_at:          Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user:     Mapped["User"]     = relationship(back_populates="transactions", foreign_keys=[user_id])
    merchant: Mapped["Merchant"] = relationship(back_populates="transactions")


class OtpSession(Base):
    """
    Stores OTP requests.

    otp_plain is stored (alongside the bcrypt hash) ONLY for the mock SMS Inbox feature.
    In a real system this field would not exist — OTP would be sent via SMS and never persisted.
    """
    __tablename__ = "otp_sessions"

    id:         Mapped[int]      = mapped_column(Integer,     primary_key=True, autoincrement=True)
    mobile:     Mapped[str]      = mapped_column(String(15),  nullable=False, index=True)
    otp_hash:   Mapped[str]      = mapped_column(String(200), nullable=False)
    otp_plain:  Mapped[str]      = mapped_column(String(10),  nullable=False)  # SMS inbox mock only
    expires_at: Mapped[datetime] = mapped_column(DateTime,    nullable=False)
    used:       Mapped[bool]     = mapped_column(Boolean,     default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime,    server_default=func.now())
