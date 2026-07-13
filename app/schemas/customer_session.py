import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class CustomerSessionOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    login_method: Optional[Literal["telegram", "otp"]] = None
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    login_time: datetime
    logout_time: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
