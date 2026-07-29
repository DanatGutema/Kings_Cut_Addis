import uuid
from typing import Optional

from pydantic import BaseModel, Field


class QrCheckInRequest(BaseModel):
    qr_token: uuid.UUID
    staff_id: uuid.UUID


class PhoneCheckInRequest(BaseModel):
    phone_number: str = Field(..., max_length=15)
    staff_id: uuid.UUID
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)


class CheckInResponse(BaseModel):
    customer_id: uuid.UUID
    first_name: str
    last_name: Optional[str] = None
    phone_number: str
    total_visits: int
    total_spending: float
    is_new_customer: bool
