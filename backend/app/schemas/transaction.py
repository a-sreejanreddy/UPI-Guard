"""
app/schemas/transaction.py — Transaction request/response schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.db.models import TransactionStatus


class PaymentRequestSchema(BaseModel):
    merchant_upi: str
    amount: float

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > 1_000_000:
            raise ValueError("Amount exceeds maximum limit of ₹10,00,000")
        return round(v, 2)

    @field_validator("merchant_upi")
    @classmethod
    def upi_format(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v:
            raise ValueError("Merchant UPI ID must contain @")
        return v


class TransactionResponseSchema(BaseModel):
    model_config = {"from_attributes": True}

    id:                   int
    user_id:              int
    merchant_id:          int
    amount:               float
    # 9 ML features
    hour:                 int
    day:                  int
    month:                int
    year:                 int
    merchant_category:    int
    user_age:             int
    state_code:           int
    zip_prefix:           int
    # Fraud decision
    fraud_score:          float
    status:               TransactionStatus
    # Admin override
    override_by_admin_id: Optional[int]
    override_at:          Optional[datetime]
    created_at:           datetime
    # Denormalized (populated in route handlers)
    merchant_upi:         str = ""
    merchant_name:        str = ""
    user_name:            str = ""


class PaymentResponseSchema(BaseModel):
    transaction_id: int
    status:         TransactionStatus
    fraud_score:    float
    amount:         float
    merchant_upi:   str
    message:        str


class OverrideResponseSchema(BaseModel):
    transaction_id: int
    previous_status: str
    new_status:      str = "ADMIN_OVERRIDDEN"
    message:         str = "Transaction approved by admin override"
