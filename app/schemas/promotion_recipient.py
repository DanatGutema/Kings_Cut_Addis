import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PromotionRecipientOut(BaseModel):
    id: uuid.UUID
    promotion_id: uuid.UUID
    customer_id: uuid.UUID
    telegram_sent: bool
    sms_sent: bool
    delivered: bool
    delivered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
