"""
app/schemas/user.py — User request/response schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.db.models import UserRole


class UserCreateSchema(BaseModel):
    mobile: str
    name: str
    age: int
    state: str
    zip_code: str
    # role is explicitly excluded here to prevent privilege escalation on signup

    @field_validator("age")
    @classmethod
    def age_range(cls, v: int) -> int:
        if not (18 <= v <= 100):
            raise ValueError("Age must be between 18 and 100")
        return v

    @field_validator("mobile")
    @classmethod
    def mobile_digits(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Mobile must be exactly 10 digits")
        return v


class AdminUserCreateSchema(UserCreateSchema):
    role: UserRole = UserRole.user


class UserResponseSchema(BaseModel):
    model_config = {"from_attributes": True}

    id:         int
    mobile:     str
    name:       str
    age:        int
    state:      str
    zip_code:   str
    role:       UserRole
    is_active:  bool
    created_at: datetime
