import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

RuleType = Literal["visit", "spending"]
RewardType = Literal["percentage", "fixed", "both"]


class LoyaltyRuleBase(BaseModel):
    rule_name: str = Field(..., max_length=255)
    rule_type: RuleType
    visit_threshold: Optional[int] = Field(None, ge=1)
    spending_threshold: Optional[Decimal] = Field(None, ge=0)
    reward_type: RewardType
    reward_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    reward_amount: Optional[Decimal] = Field(None, ge=0)
    expiry_days: int = Field(..., ge=1)
    evaluation_period_days: Optional[int] = Field(None, ge=1)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_thresholds(self):
        if self.rule_type == "visit" and not self.visit_threshold:
            raise ValueError("visit_threshold is required for visit-based rules")
        if self.rule_type == "spending" and self.spending_threshold is None:
            raise ValueError("spending_threshold is required for spending-based rules")
        if self.reward_type in ("percentage", "both") and self.reward_percentage is None:
            raise ValueError("reward_percentage is required for percentage rewards")
        if self.reward_type in ("fixed", "both") and self.reward_amount is None:
            raise ValueError("reward_amount is required for fixed rewards")
        return self


class LoyaltyRuleCreate(LoyaltyRuleBase):
    pass


class LoyaltyRuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, max_length=255)
    rule_type: Optional[RuleType] = None
    visit_threshold: Optional[int] = Field(None, ge=1)
    spending_threshold: Optional[Decimal] = Field(None, ge=0)
    reward_type: Optional[RewardType] = None
    reward_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    reward_amount: Optional[Decimal] = Field(None, ge=0)
    expiry_days: Optional[int] = Field(None, ge=1)
    evaluation_period_days: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class LoyaltyRuleOut(LoyaltyRuleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
