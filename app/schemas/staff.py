import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


StaffRole = Literal["admin", "staff"]
ApprovalStatus = Literal["pending", "approved", "rejected"]


class StaffBase(BaseModel):
    first_name: str = Field(..., max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone_number: str = Field(..., max_length=15)
    email: Optional[EmailStr] = None
    role: StaffRole = "staff"


class StaffCreate(StaffBase):
    """Admin invite create — email required so invitation can be sent."""

    email: EmailStr
    password: Optional[str] = Field(None, min_length=8)


class StaffSelfRegister(BaseModel):
    """Public self-registration. Email optional; phone + password required.
    Role is assigned by an admin at approval time.
    """

    first_name: str = Field(..., max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone_number: str = Field(..., max_length=15)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=8)

    @field_validator("phone_number")
    @classmethod
    def phone_not_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 9:
            raise ValueError("phone_number looks too short")
        return cleaned


class StaffApproveRequest(BaseModel):
    """Admin assigns the real role when approving a pending registration."""

    role: StaffRole = "staff"


class StaffUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=15)
    email: Optional[EmailStr] = None
    role: Optional[StaffRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class StaffOut(StaffBase):
    id: uuid.UUID
    is_active: bool
    approval_status: ApprovalStatus = "approved"
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StaffRegisterResult(BaseModel):
    message: str
    approval_status: ApprovalStatus = "pending"
