import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SmsLog(Base):
    __tablename__ = "sms_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    phone_number = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    sms_type = Column(String(30), nullable=True)
    provider = Column(String(100), nullable=True)
    delivery_status = Column(String(30), default="pending")
    provider_reference = Column(String(255), nullable=True)
    sent_at = Column(DateTime, server_default=func.now())
    delivered_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("sms_type IN ('promotion','otp','notification')", name="check_sms_type"),
        CheckConstraint(
            "delivery_status IN ('pending','sent','delivered','failed')",
            name="check_sms_delivery_status",
        ),
    )

    customer = relationship("Customer", back_populates="sms_logs")
