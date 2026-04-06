"""
app/schemas/merchant.py — Merchant request/response schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class MerchantCreateSchema(BaseModel):
    user_mobile:   str   # Admin looks up user by mobile number
    upi_id:        str
    business_name: str
    category:      str   # Must be one of: Food, Retail, Travel, Entertainment, Healthcare, Education, Utilities, Other

    @field_validator("upi_id")
    @classmethod
    def upi_format(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("UPI ID must contain @  (e.g. shopname@upi)")
        return v.lower().strip()

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        valid = {"Food", "Retail", "Travel", "Entertainment", "Healthcare", "Education", "Utilities", "Other"}
        if v not in valid:
            raise ValueError(f"Category must be one of: {', '.join(sorted(valid))}")
        return v


class MerchantResponseSchema(BaseModel):
    model_config = {"from_attributes": True}

    id:            int
    user_id:       int
    upi_id:        str
    business_name: str
    category:      str
    created_at:    datetime
    # Denormalized for UI convenience (populated in route handlers)
    user_name:     str = ""
    user_mobile:   str = ""
