"""
app/core/config.py — Application settings via pydantic-settings

All configuration is loaded from the .env file located in the same directory
as THIS module (backend/app/core/.env is NOT correct — the .env lives at
backend/.env, two directories up from here). We resolve the path absolutely
so the app works regardless of where uvicorn is launched from.

Import the singleton: `from app.core.config import settings`
"""
import pathlib

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve backend/.env absolutely from this file's location:
#   this file  → backend/app/core/config.py
#   parent     → backend/app/core/
#   parent×2   → backend/app/
#   parent×3   → backend/
#   + ".env"   → backend/.env
_BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
_ENV_FILE    = str(_BACKEND_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # ── Database ──────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./upi_guard.db"

    # ── JWT ───────────────────────────────────────────────────────────
    # No default — application fails fast if this is missing from .env.
    JWT_SECRET_KEY: str
    JWT_ALGORITHM:  str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── Cookie security (override in .env for production) ─────────────
    # COOKIE_SECURE=False  is correct for local HTTP dev (no HTTPS).
    # COOKIE_SECURE=True   must be set in production (requires HTTPS).
    # COOKIE_SAMESITE      "lax" works for same-origin+cross-origin GET;
    #                      use "strict" behind a reverse proxy in production.
    COOKIE_SECURE:   bool = False
    COOKIE_SAMESITE: str  = "lax"
    COOKIE_HTTPONLY: bool = True

    # ── OTP ───────────────────────────────────────────────────────────
    OTP_TTL_SECONDS: int = 600   # 10 minutes
    OTP_LENGTH:      int = 6

    # ── ML model paths (relative to backend/ working directory) ───────
    MODEL_PATH:  str = "models/mlp_model.h5"
    SCALER_PATH: str = "models/scaler.pkl"

    # ── CORS ──────────────────────────────────────────────────────────
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # ── Admin seed (demo only) ────────────────────────────────────────
    ADMIN_MOBILE: str = "9999999999"
    ADMIN_NAME:   str = "Admin"

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_secret_must_not_be_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 16:
            raise ValueError(
                "JWT_SECRET_KEY must be set to a secure random string of at least "
                "16 characters. Generate one with: python -c \"import secrets; "
                "print(secrets.token_hex(32))\""
            )
        return v


# Module-level singleton — import this everywhere
settings = Settings()
