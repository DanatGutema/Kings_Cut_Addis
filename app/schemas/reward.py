import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

RewardStatus = Literal["pending", "redeemed", "expired", "void"]
RewardAction = Literal["earned", "redeemed", "expired", "void"]


class RewardBase(BaseModel):
    customer_id: uuid.UUID
    loyalty_rule_id: uuid.UUID
    reward_type: str
    reward_percentage: Optional[Decimal] = None
    reward_amount: Optional[Decimal] = None
    earned_date: date
    expiry_date: date


class RewardHistoryOut(BaseModel):
    id: uuid.UUID
    reward_id: uuid.UUID
    action: RewardAction
    action_date: datetime
    staff_id: Optional[uuid.UUID] = None
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RewardOut(RewardBase):
    id: uuid.UUID
    status: RewardStatus
    redeemed_at: Optional[datetime] = None
    created_at: datetime
    history: list[RewardHistoryOut] = []

    model_config = ConfigDict(from_attributes=True)


class RewardRedeem(BaseModel):
    remarks: Optional[str] = None


class RewardVoid(BaseModel):
    remarks: Optional[str] = None

