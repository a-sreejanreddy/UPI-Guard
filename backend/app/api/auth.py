"""
app/api/auth.py — Authentication endpoints
"""
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    clear_auth_cookie,
    create_access_token,
    get_current_user,
    get_password_hash,
    set_auth_cookie,
    verify_password,
)
from app.db.models import OtpSession, User
from app.db.session import get_db
from app.schemas.auth import (
    OtpInboxResponseSchema,
    OtpRequestSchema,
    OtpVerifySchema,
    TokenResponseSchema,
)
from app.schemas.user import UserResponseSchema

router = APIRouter()


@router.post("/request-otp", response_model=dict, summary="Request an OTP")
async def request_otp(
    payload: OtpRequestSchema, db: AsyncSession = Depends(get_db)
):
    """
    Generate a mock OTP, store hashed in DB for verification,
    and also store plaintext for the mock SMS inbox UI.
    """
    mobile = payload.mobile

    # In a real app we'd trigger an SMS provider here.
    # For this demo, generate a random 6-digit OTP.
    plain_otp = f"{random.randint(0, 999999):0length}".replace("length", str(settings.OTP_LENGTH))
    # Python zero-padding fix:
    plain_otp = f"{random.randint(0, 10**settings.OTP_LENGTH - 1)}".zfill(settings.OTP_LENGTH)

    hashed_otp = get_password_hash(plain_otp)
    expires = datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_TTL_SECONDS)

    # Invalidate older unused OTPs for this mobile
    await db.execute(
        update(OtpSession)
        .where(OtpSession.mobile == mobile)
        .where(OtpSession.used == False)
        .values(used=True)
    )

    # Create new OTP session
    otp_session = OtpSession(
        mobile=mobile,
        otp_hash=hashed_otp,
        otp_plain=plain_otp,
        expires_at=expires.replace(tzinfo=None),  # SQLite stores naive datetime
        used=False,
    )
    db.add(otp_session)
    await db.commit()

    return {"message": f"OTP generated and sent to {mobile}."}


@router.get("/otp-inbox/{mobile}", response_model=OtpInboxResponseSchema, summary="Mock SMS Inbox")
async def get_otp_inbox(mobile: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve the latest unexpired OTP in plaintext.
    Used ONLY for the demo UI to simulate an SMS inbox.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    result = await db.execute(
        select(OtpSession)
        .where(OtpSession.mobile == mobile)
        .where(OtpSession.used == False)
        .where(OtpSession.expires_at > now)
        .order_by(OtpSession.created_at.desc())
        .limit(1)
    )
    otp_session = result.scalar_one_or_none()

    if not otp_session:
        raise HTTPException(status_code=404, detail="No active OTP found for this mobile number.")

    expires_in = int((otp_session.expires_at - now).total_seconds())
    return OtpInboxResponseSchema(
        mobile=mobile,
        otp=otp_session.otp_plain,
        expires_in_seconds=max(0, expires_in),
        message="OTP retrieved from mock inbox",
    )


@router.post("/verify-otp", response_model=TokenResponseSchema, summary="Verify OTP & Login")
async def verify_otp(
    payload: OtpVerifySchema, response: Response, db: AsyncSession = Depends(get_db)
):
    """
    Verify the OTP hash. If valid, set httpOnly cookie and return JWT info.
    If the user does not exist, they should be created ONLY if they are an admin or pre-approved,
    BUT wait! The roadmap says 'auto-activate' or 'public user' doesn't matter, we create public Users?
    Let's check the spec: "Users log in using their Mobile Number... If the User is new, we create."
    Actually the spec said "Option C... Users log in using Mobile Number... if new... wait"
    Wait, in `schemas/user.py` we have `UserCreateSchema` without role, which means new users are created as `user` role.
    Let's implement creating a missing User with default values if they don't exist.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    result = await db.execute(
        select(OtpSession)
        .where(OtpSession.mobile == payload.mobile)
        .where(OtpSession.used == False)
        .where(OtpSession.expires_at > now)
        .order_by(OtpSession.created_at.desc())
        .limit(1)
    )
    otp_session = result.scalar_one_or_none()

    if not otp_session or not verify_password(payload.otp, otp_session.otp_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    # Mark OTP as used
    otp_session.used = True
    await db.commit()

    # Find User
    user_result = await db.execute(select(User).where(User.mobile == payload.mobile))
    user = user_result.scalar_one_or_none()

    if not user:
        # Create a basic user profile for automatic onboarding.
        # In a real app we might redirect to a profile completion page.
        user = User(
            mobile=payload.mobile,
            name="New User",
            age=25,
            state="Unknown",
            zip_code="000000",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    # Mint JWT
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    
    # Set httpOnly cookie
    set_auth_cookie(response, access_token)

    return TokenResponseSchema(
        role=user.role.value,
        user_id=user.id,
        name=user.name,
        message="Login successful"
    )


@router.post("/logout", summary="Logout")
async def logout(response: Response):
    """Clear the JWT cookie."""
    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponseSchema, summary="Get Current User Profile")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently logged-in user."""
    return current_user
