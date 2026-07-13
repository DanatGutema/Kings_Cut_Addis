import uuid

from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TelegramLog(Base):
    __tablename__ = "telegram_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(30), nullable=True)
    telegram_message_id = Column(BigInteger, nullable=True)
    delivery_status = Column(String(30), default="sent")
    sent_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "message_type IN ('promotion','notification','reward')",
            name="check_telegram_message_type",
        ),
        CheckConstraint(
            "delivery_status IN ('sent','failed')",
            name="check_telegram_delivery_status",
        ),
    )

    customer = relationship("Customer", back_populates="telegram_logs")
