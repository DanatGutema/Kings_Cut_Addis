import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ServiceOrderStatus = Literal["pending", "confirmed", "in_progress", "completed", "cancelled"]


class ServiceOrderItemBase(BaseModel):
    service_id: uuid.UUID
    quantity: int = Field(1, ge=1)
    unit_price: Decimal = Field(..., ge=0)
    subtotal: Decimal = Field(..., ge=0)


class ServiceOrderItemCreate(BaseModel):
    service_id: uuid.UUID
    quantity: int = Field(1, ge=1)


class ServiceOrderItemOut(ServiceOrderItemBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ServiceOrderBase(BaseModel):
    customer_id: uuid.UUID
    scheduled_at: datetime
    prefered_time_slot: str = Field(..., max_length=50)
    total_estimated_price: Decimal = Field(..., ge=0)


class ServiceOrderCreate(BaseModel):
    customer_id: uuid.UUID
    scheduled_at: datetime
    prefered_time_slot: str = Field(..., max_length=50)
    items: list[ServiceOrderItemCreate]


class ServiceOrderUpdate(BaseModel):
    status: Optional[ServiceOrderStatus] = None
    scheduled_at: Optional[datetime] = None
    prefered_time_slot: Optional[str] = Field(None, max_length=50)
    total_estimated_price: Optional[Decimal] = Field(None, ge=0)


class ServiceOrderOut(ServiceOrderBase):
    id: uuid.UUID
    status: ServiceOrderStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: list[ServiceOrderItemOut] = []

    model_config = ConfigDict(from_attributes=True)
