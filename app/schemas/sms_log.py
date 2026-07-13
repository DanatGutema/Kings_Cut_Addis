import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class SmsLogOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    phone_number: str
    message: str
    sms_type: Optional[Literal["promotion", "otp", "notification"]] = None
    provider: Optional[str] = None
    delivery_status: Literal["pending", "sent", "delivered", "failed"]
    provider_reference: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
