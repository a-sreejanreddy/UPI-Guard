"""
app/db/init_db.py — Database initializer

Creates all tables if they don't exist. Called once during FastAPI lifespan startup.
"""
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base
from app.db import models  # noqa: F401 — import so all models register with Base.metadata


async def init_db(engine: AsyncEngine) -> None:
    """Create all tables defined in Base.metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
