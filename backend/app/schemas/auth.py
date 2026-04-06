"""
app/schemas/auth.py — Auth request/response schemas
"""
from pydantic import BaseModel, field_validator


class OtpRequestSchema(BaseModel):
    mobile: str

    @field_validator("mobile")
    @classmethod
    def mobile_must_be_10_digits(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Mobile must be exactly 10 digits")
        return v


class OtpVerifySchema(BaseModel):
    mobile: str
    otp: str


class TokenResponseSchema(BaseModel):
    role: str
    user_id: int
    name: str
    message: str = "Login successful"


class OtpInboxResponseSchema(BaseModel):
    mobile: str
    otp: str
    expires_in_seconds: int
    message: str = "OTP retrieved from mock inbox"
