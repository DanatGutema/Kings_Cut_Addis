import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

AppointmentStatus = Literal["pending", "accepted", "rejected", "completed"]


class AppointmentCreate(BaseModel):
    service_id: uuid.UUID
    scheduled_at: datetime
    notes: Optional[str] = Field(None, max_length=1000)


class AppointmentOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    service_id: uuid.UUID
    scheduled_at: datetime
    notes: Optional[str] = None
    status: AppointmentStatus
    handled_by_staff_id: Optional[uuid.UUID] = None
    visit_id: Optional[uuid.UUID] = None
    responded_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    service_name: Optional[str] = None
    service_price: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)
