import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SmsType = Literal["promotion", "otp", "notification"]
SmsDeliveryStatus = Literal["pending", "sent", "delivered", "failed"]
TelegramMessageType = Literal["promotion", "notification", "reward"]
TelegramDeliveryStatus = Literal["sent", "failed"]


class SmsLogOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    phone_number: str
    message: str
    sms_type: Optional[SmsType] = None
    provider: Optional[str] = None
    delivery_status: SmsDeliveryStatus
    provider_reference: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TelegramLogOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    telegram_id: int
    message: str
    message_type: Optional[TelegramMessageType] = None
    telegram_message_id: Optional[int] = None
    delivery_status: TelegramDeliveryStatus
    sent_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SystemSettingBase(BaseModel):
    setting_key: str = Field(..., max_length=255)
    setting_value: str
    description: Optional[str] = None


class SystemSettingCreate(SystemSettingBase):
    updated_by: Optional[uuid.UUID] = None


class SystemSettingUpdate(BaseModel):
    setting_value: str
    description: Optional[str] = None
    updated_by: Optional[uuid.UUID] = None


class SystemSettingOut(SystemSettingBase):
    id: uuid.UUID
    updated_by: Optional[uuid.UUID] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogOut(BaseModel):
    id: uuid.UUID
    staff_id: Optional[uuid.UUID] = None
    action: str
    table_name: Optional[str] = None
    record_id: Optional[uuid.UUID] = None
    old_data: Optional[dict[str, Any]] = None
    new_data: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
