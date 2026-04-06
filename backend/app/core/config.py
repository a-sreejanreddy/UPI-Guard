"""
app/core/config.py — Application settings via pydantic-settings

All configuration is loaded from the .env file in the backend/ working directory.
Import the singleton: `from app.core.config import settings`
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Database ──────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./upi_guard.db"

    # ── JWT ───────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_use_secrets_token_hex_32"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── OTP ───────────────────────────────────────────────────────────
    OTP_TTL_SECONDS: int = 600   # 10 minutes
    OTP_LENGTH: int = 6

    # ── ML model paths (relative to backend/ working directory) ───────
    MODEL_PATH: str = "models/mlp_model.h5"
    SCALER_PATH: str = "models/scaler.pkl"

    # ── CORS ──────────────────────────────────────────────────────────
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # ── Admin seed (demo only) ────────────────────────────────────────
    ADMIN_MOBILE: str = "9999999999"
    ADMIN_NAME: str = "Admin"


# Module-level singleton — import this everywhere
settings = Settings()
