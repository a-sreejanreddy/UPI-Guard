"""
app/api/transactions.py — Transactions and Payment endpoints
"""
import asyncio
from datetime import datetime, timezone
import logging
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, require_role
from app.db.models import (
    Merchant,
    Transaction,
    TransactionStatus,
    User,
    UserRole,
    STATE_CODE_MAP,
    MERCHANT_CATEGORY_MAP
)
from app.db.session import get_db
from app.ml.loader import get_model_loader
from app.schemas.transaction import (
    PaymentRequestSchema,
    PaymentResponseSchema,
    TransactionResponseSchema
)

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


def _denormalize_transactions(txns: list[Transaction]) -> list[Transaction]:
    """Helper to attach user and merchant UI names to the response."""
    for t in txns:
        if t.merchant:
            t.merchant_upi = t.merchant.upi_id
            t.merchant_name = t.merchant.business_name
        if t.user:
            t.user_name = t.user.name
    return txns

@router.post("/pay", response_model=PaymentResponseSchema, summary="Execute a payment with fraud inference")
async def process_payment(
    payload: PaymentRequestSchema,
    idempotency_key: str = Header(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Idempotency pre-check
    existing_result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.merchant))
        .where(
            Transaction.idempotency_key == idempotency_key,
            Transaction.user_id == current_user.id
        )
    )
    existing_txn = existing_result.scalar_one_or_none()
    if existing_txn:
        msg = "Payment blocked due to suspected fraud." if existing_txn.status == TransactionStatus.BLOCKED_FRAUD else "Payment approved."
        return PaymentResponseSchema(
            transaction_id=existing_txn.id,
            status=existing_txn.status,
            fraud_score=existing_txn.fraud_score,
            amount=existing_txn.amount,
            merchant_upi=existing_txn.merchant.upi_id,
            message=msg
        )

    # Lookup recipient merchant by UPI ID
    merchant_result = await db.execute(select(Merchant).where(Merchant.upi_id == payload.merchant_upi))
    merchant = merchant_result.scalar_one_or_none()
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
        
    if merchant.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pay yourself"
        )

    # Prepare features
    now = datetime.now(timezone.utc)
    hour = now.hour
    day = now.day
    month = now.month
    year = now.year
    
    # Safely derive encodings with fallback limits
    category_encoded = MERCHANT_CATEGORY_MAP.get(merchant.category, MERCHANT_CATEGORY_MAP.get("Other", 7))
    state_encoded = STATE_CODE_MAP.get(current_user.state, 28) # Defaults to 'Delhi' encoding mapped at 28 if unknown
    
    # Parse zip_prefix
    try:
        zip_prefix = int(current_user.zip_code[:3])
    except (ValueError, TypeError):
        zip_prefix = 0
        
    amount = payload.amount
    user_age = current_user.age or 0

    features = [
        hour,
        day,
        month,
        year,
        category_encoded,
        amount,
        user_age,
        state_encoded,
        zip_prefix
    ]

    # Model inference
    try:
        fraud_score = await asyncio.to_thread(get_model_loader().predict, features)
    except Exception as e:
        logger.error(f"Inference engine failure: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fraud engine unavailable"
        ) from e

    # Verdict
    is_fraud = fraud_score >= 0.5
    txn_status = TransactionStatus.BLOCKED_FRAUD if is_fraud else TransactionStatus.APPROVED
    
    # Persist transaction
    txn = Transaction(
        idempotency_key=idempotency_key,
        user_id=current_user.id,
        merchant_id=merchant.id,
        amount=amount,
        hour=hour,
        day=day,
        month=month,
        year=year,
        merchant_category=category_encoded,
        user_age=user_age,
        state_code=state_encoded,
        zip_prefix=zip_prefix,
        fraud_score=fraud_score,
        status=txn_status
    )
    
    db.add(txn)
    try:
        await db.commit()
        await db.refresh(txn)
    except IntegrityError:
        await db.rollback()
        # Fallback to fetch from another concurrent request
        existing_result = await db.execute(
            select(Transaction).where(
                Transaction.idempotency_key == idempotency_key,
                Transaction.user_id == current_user.id
            )
        )
        txn = existing_result.scalar_one()

    # Response
    message = "Payment blocked due to suspected fraud." if is_fraud else "Payment approved."
    return PaymentResponseSchema(
        transaction_id=txn.id,
        status=txn_status,
        fraud_score=fraud_score,
        amount=txn.amount,
        merchant_upi=merchant.upi_id,
        message=message
    )


@router.get("/my", response_model=List[TransactionResponseSchema], summary="View my transaction history")
async def get_my_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.merchant), selectinload(Transaction.user))
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .offset(skip).limit(limit)
    )
    txns = result.scalars().all()
    
    return _denormalize_transactions(txns)


@router.get("/merchant/{merchant_id}", response_model=List[TransactionResponseSchema], summary="View merchant received transactions")
async def get_merchant_transactions(
    merchant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role("merchant")),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership of this merchant ID
    merchant_result = await db.execute(
        select(Merchant).where(Merchant.id == merchant_id)
    )
    merchant = merchant_result.scalar_one_or_none()
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
        
    if merchant.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this merchant's transactions"
        )
        
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.merchant), selectinload(Transaction.user))
        .where(Transaction.merchant_id == merchant_id)
        .order_by(Transaction.created_at.desc())
        .offset(skip).limit(limit)
    )
    txns = result.scalars().all()
    
    return _denormalize_transactions(txns)
