import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VisitServiceItemBase(BaseModel):
    service_id: uuid.UUID
    quantity: int = Field(1, ge=1)
    unit_price: Decimal = Field(..., ge=0)
    subtotal: Decimal = Field(..., ge=0)


class VisitServiceItemCreate(BaseModel):
    service_id: uuid.UUID
    quantity: int = Field(1, ge=1)


class VisitServiceItemOut(VisitServiceItemBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class VisitBase(BaseModel):
    customer_id: uuid.UUID
    staff_id: uuid.UUID
    total_amount: Decimal = Field(..., ge=0)
    notes: Optional[str] = None
    visit_date: Optional[datetime] = None


class VisitCreate(BaseModel):
    customer_id: uuid.UUID
    staff_id: uuid.UUID
    notes: Optional[str] = None
    visit_date: Optional[datetime] = None
    services: list[VisitServiceItemCreate]


class VisitUpdate(BaseModel):
    staff_id: Optional[uuid.UUID] = None
    total_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    visit_date: Optional[datetime] = None


class VisitOut(VisitBase):
    id: uuid.UUID
    visit_date: datetime
    created_at: datetime
    updated_at: datetime
    visit_services: list[VisitServiceItemOut] = []

    model_config = ConfigDict(from_attributes=True)
