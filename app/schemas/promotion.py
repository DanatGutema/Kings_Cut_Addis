import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DiscountType = Literal["percentage", "fixed"]


class PromotionBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: Decimal = Field(..., ge=0)
    start_date: date
    end_date: date
    is_active: bool = True


class PromotionCreate(PromotionBase):
    pass


class PromotionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class PromotionOut(PromotionBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromotionRecipientOut(BaseModel):
    id: uuid.UUID
    promotion_id: uuid.UUID
    customer_id: uuid.UUID
    telegram_sent: bool
    sms_sent: bool
    delivered: bool
    delivered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PromotionBroadcastRequest(BaseModel):
    """Optional targeting filters. Empty = all customers with a Telegram ID."""

    min_visits: Optional[int] = Field(None, ge=0)
    max_days_since_visit: Optional[int] = Field(None, ge=1)
    min_spending: Optional[Decimal] = Field(None, ge=0)
    send_sms_fallback: bool = False


class PromotionBroadcastResult(BaseModel):
    promotion_id: uuid.UUID
    recipients_total: int
    telegram_sent: int
    telegram_failed: int
    sms_queued: int = 0
