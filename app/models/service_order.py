import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    status = Column(String(30), default="pending")
    scheduled_at = Column(DateTime, nullable=False)
    prefered_time_slot = Column(String(50), nullable=False)
    total_estimated_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','confirmed','in_progress','completed','cancelled')",
            name="check_service_order_status",
        ),
    )

    customer = relationship("Customer", back_populates="service_orders")
    items = relationship("ServiceOrderItem", back_populates="service_order", cascade="all, delete-orphan")
