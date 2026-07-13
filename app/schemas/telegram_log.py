import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class TelegramLogOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    telegram_id: int
    message: str
    message_type: Optional[Literal["promotion", "notification", "reward"]] = None
    telegram_message_id: Optional[int] = None
    delivery_status: Literal["sent", "failed"]
    sent_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
