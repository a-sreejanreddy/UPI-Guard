"""
app/db/base.py — SQLAlchemy declarative base

All models inherit from Base. Import Base here to avoid circular imports.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
