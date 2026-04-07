"""
app/core/security.py — JWT + bcrypt utilities

Provides:
  - bcrypt hashing (get_password_hash, verify_password)
  - JWT creation and decoding (create_access_token, decode_token)
  - httpOnly cookie management (set_auth_cookie, clear_auth_cookie)
  - FastAPI dependencies (get_current_user, require_role)
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Cookie, Depends, HTTPException, Response, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

# ── bcrypt context ─────────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(plain: str) -> str:
    """Hash a plain-text string (OTP, password) using bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text string against a bcrypt hash."""
    return pwd_context.verify(plain, hashed)


# ── JWT utilities ──────────────────────────────────────────────────────────────

def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT.

    data should contain at minimum: {"sub": str(user_id), "role": role_value}
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT. Raises HTTP 401 on failure.
    """
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Cookie helpers ─────────────────────────────────────────────────────────────

def set_auth_cookie(response: Response, token: str) -> None:
    """
    Set the JWT as an httpOnly cookie.

    Flags come from settings so they can be overridden per environment:
    - COOKIE_HTTPONLY  : True always (XSS protection); configurable for tests
    - COOKIE_SECURE    : False for local HTTP dev; True in production (HTTPS required)
    - COOKIE_SAMESITE  : "lax" for local dev; "strict" recommended for production
    """
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Remove the JWT cookie (logout)."""
    response.delete_cookie(key="access_token", path="/")


# ── FastAPI dependencies ────────────────────────────────────────────────────────

async def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency — extract and validate JWT from cookie, return User ORM object.
    Raises HTTP 401 if token is missing or invalid.
    """
    from app.db.models import User  # local import to avoid circular

    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated — no token cookie found",
        )

    payload = decode_token(access_token)
    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: 'sub' is not a valid user ID",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def require_role(*roles: str):
    """
    FastAPI dependency factory — enforce role-based access control.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        OR
        current_user = Depends(get_current_user)
        _: None = Depends(require_role("admin", "merchant"))
    """
    async def role_checker(current_user=Depends(get_current_user)):
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(roles)}",
            )
        return current_user
    return role_checker
