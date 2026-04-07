# Summary 2.1: Config + SQLAlchemy Async Models + DB Session

**Status**: COMPLETE
**Wave**: 1

## What Was Done

### Task 1: App Config
- `backend/app/core/config.py` — pydantic-settings BaseSettings, reads .env, 11 vars
- `backend/.env.example` — all vars documented
- `backend/.env` — local dev defaults (gitignored)

### Task 2: SQLAlchemy 2.0 Models
- `backend/app/db/base.py` — DeclarativeBase
- `backend/app/db/models.py` — User, Merchant, Transaction, OtpSession (Mapped style)
  - UserRole enum: admin, merchant, user
  - TransactionStatus enum: APPROVED, BLOCKED_FRAUD, ADMIN_OVERRIDDEN
  - OtpSession.otp_plain field for SMS Inbox mock
  - MERCHANT_CATEGORY_MAP and STATE_CODE_MAP for feature encoding
- `backend/app/db/session.py` — async engine + AsyncSessionLocal + get_db()
- `backend/app/db/init_db.py` — create_all initializer

## Verification
- `Config OK: sqlite+aiosqlite:///./upi_guard.db`
- `DB tables created OK` + `Models OK`
- `backend/upi_guard.db` created: 36,864 bytes
