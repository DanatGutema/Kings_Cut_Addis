import uuid

from sqlalchemy import Column, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ServiceOrderItem(Base):
    __tablename__ = "service_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_order_id = Column(UUID(as_uuid=True), ForeignKey("service_orders.id"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    service_order = relationship("ServiceOrder", back_populates="items")
    service = relationship("Service", back_populates="order_items")
