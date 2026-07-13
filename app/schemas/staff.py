import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


StaffRole = Literal["admin", "staff"]


class StaffBase(BaseModel):
    first_name: str = Field(..., max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone_number: str = Field(..., max_length=15)
    email: EmailStr
    role: StaffRole = "staff"


class StaffCreate(StaffBase):
    password: str = Field(..., min_length=8)


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
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
