import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class RewardHistoryOut(BaseModel):
    id: uuid.UUID
    reward_id: uuid.UUID
    action: Optional[Literal["earned", "redeemed", "expired", "void"]] = None
    action_date: datetime
    staff_id: Optional[uuid.UUID] = None
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
