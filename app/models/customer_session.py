import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CustomerSession(Base):
    __tablename__ = "customer_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    login_method = Column(String(30), nullable=True)
    device_name = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    login_time = Column(DateTime, nullable=False, server_default=func.now())
    logout_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("login_method IN ('telegram','otp')", name="check_login_method"),
    )

    customer = relationship("Customer", back_populates="sessions")
