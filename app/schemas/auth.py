import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

LoginMethod = Literal["telegram", "otp"]


class CustomerSessionOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    login_method: Optional[LoginMethod] = None
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    login_time: datetime
    logout_time: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenOut(BaseModel):
    id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    staff_id: Optional[uuid.UUID] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    expires_at: datetime
    revoked: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None


class StaffLogin(BaseModel):
    """Login with email or phone number."""

    email: Optional[str] = None
    phone_number: Optional[str] = None
    password: str

    def identifier(self) -> str:
        value = (self.email or self.phone_number or "").strip()
        if not value:
            raise ValueError("email or phone_number is required")
        return value


class TelegramAuthRequest(BaseModel):
    init_data: str


class OtpRequest(BaseModel):
    phone_number: str = Field(..., max_length=15)


class OtpVerify(BaseModel):
    phone_number: str = Field(..., max_length=15)
    otp_code: str = Field(..., min_length=4, max_length=8)
