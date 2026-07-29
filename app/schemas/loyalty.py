import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RuleProgressOut(BaseModel):
    rule_id: uuid.UUID
    rule_name: str
    rule_type: str
    visit_threshold: Optional[int] = None
    spending_threshold: Optional[Decimal] = None
    evaluation_period_days: Optional[int] = None
    current_visits: int
    current_spending: Decimal
    visits_remaining: Optional[int] = None
    spending_remaining: Optional[Decimal] = None
    pending_rewards: int

    model_config = ConfigDict(from_attributes=True)


class LoyaltyProgressOut(BaseModel):
    customer_id: uuid.UUID
    total_visits: int
    total_spending: Decimal
    rules: list[RuleProgressOut]
