import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BarberCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone_number: str = Field(..., min_length=7, max_length=15)
    email: Optional[EmailStr] = None
    specialty: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class BarberUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, min_length=7, max_length=15)
    email: Optional[EmailStr] = None
    specialty: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class BarberOut(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: Optional[str] = None
    phone_number: str
    email: Optional[str] = None
    specialty: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
