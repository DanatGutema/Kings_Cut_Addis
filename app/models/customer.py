import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    phone_number = Column(String(15), nullable=False, unique=True)
    email = Column(String(255), unique=True, nullable=True)
    qr_token = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    total_visits = Column(Integer, nullable=False, default=0)
    total_spending = Column(Numeric(12, 2), nullable=False, default=0.00)
    loyalty_status = Column(String(20), default="bronze")
    joined_date = Column(Date, nullable=False, server_default=func.current_date())
    last_visit_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "loyalty_status IN ('bronze','silver','gold','platinum')",
            name="check_loyalty_status",
        ),
    )

    visits = relationship("Visit", back_populates="customer")
    rewards = relationship("Reward", back_populates="customer")
    promotion_recipients = relationship("PromotionRecipient", back_populates="customer")
    refresh_tokens = relationship("RefreshToken", back_populates="customer")
    sessions = relationship("CustomerSession", back_populates="customer")
    sms_logs = relationship("SmsLog", back_populates="customer")
    telegram_logs = relationship("TelegramLog", back_populates="customer")
    service_orders = relationship("ServiceOrder", back_populates="customer")
