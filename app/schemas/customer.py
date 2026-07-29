import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerBase(BaseModel):
    first_name: str = Field(..., max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone_number: str = Field(..., max_length=15)
    email: Optional[EmailStr] = None


class CustomerCreate(CustomerBase):
    telegram_id: Optional[int] = None


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class CustomerOut(CustomerBase):
    id: uuid.UUID
    telegram_id: Optional[int] = None
    qr_token: uuid.UUID
    total_visits: int
    total_spending: Decimal
    joined_date: date
    last_visit_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerSummary(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: Optional[str] = None
    phone_number: str
    total_visits: int
    total_spending: Decimal
    last_visit_date: Optional[date] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
