"""
app/api/admin.py — Admin CRUD endpoints
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.security import require_role
from app.db.models import Merchant, User, UserRole
from app.db.session import get_db
from app.schemas.merchant import MerchantCreateSchema, MerchantResponseSchema
from app.schemas.user import AdminUserCreateSchema, UserResponseSchema

router = APIRouter(dependencies=[Depends(require_role("admin"))])


@router.get("/users", response_model=List[UserResponseSchema], summary="List all users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.post("/users", response_model=UserResponseSchema, summary="Create a new user")
async def create_user(payload: AdminUserCreateSchema, db: AsyncSession = Depends(get_db)):
    # Check if mobile exists
    result = await db.execute(select(User).where(User.mobile == payload.mobile))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this mobile number already exists."
        )

    user_data = payload.model_dump(exclude={"role"})
    user = User(**user_data, role=UserRole.user)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this mobile number already exists."
        ) from e
    return user


@router.get("/merchants", response_model=List[MerchantResponseSchema], summary="List all merchants")
async def list_merchants(db: AsyncSession = Depends(get_db)):
    # Need to load the associated User to populate response (denormalized UI fields)
    result = await db.execute(
        select(Merchant).options(selectinload(Merchant.user)).order_by(Merchant.created_at.desc())
    )
    merchants = result.scalars().all()
    
    # Populate the extra fields before Pydantic resolves them
    for m in merchants:
        if m.user:
            m.user_name = m.user.name
            m.user_mobile = m.user.mobile
            
    return merchants


@router.post("/merchants", response_model=MerchantResponseSchema, summary="Register a merchant")
async def create_merchant(payload: MerchantCreateSchema, db: AsyncSession = Depends(get_db)):
    # Verify user exists by mobile
    user_result = await db.execute(select(User).where(User.mobile == payload.user_mobile))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with provided mobile number not found."
        )

    # Check UPI ID uniqueness
    upi_result = await db.execute(select(Merchant).where(Merchant.upi_id == payload.upi_id))
    if upi_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UPI ID is already registered."
        )
        
    merchant_user_result = await db.execute(select(Merchant).where(Merchant.user_id == user.id))
    if merchant_user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already linked to a merchant account."
        )

    merchant = Merchant(
        user_id=user.id,
        upi_id=payload.upi_id,
        business_name=payload.business_name,
        category=payload.category
    )
    user.role = UserRole.merchant
    db.add(merchant)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(merchant)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UPI ID or user_id already in use."
        ) from e
    
    # Attach denormalized fields so the response validates
    merchant.user_name = user.name
    merchant.user_mobile = user.mobile
    
    return merchant
