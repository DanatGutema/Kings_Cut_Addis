import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class SystemSettingBase(BaseModel):
    setting_key: str
    setting_value: str
    description: Optional[str] = None


class SystemSettingCreate(SystemSettingBase):
    pass


class SystemSettingUpdate(BaseModel):
    setting_value: Optional[str] = None
    description: Optional[str] = None


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
