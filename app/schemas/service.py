import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    name: str = Field(..., max_length=255)
    price: Decimal = Field(..., ge=0)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    price: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ServiceOut(ServiceBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
