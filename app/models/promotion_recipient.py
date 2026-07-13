import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PromotionRecipient(Base):
    __tablename__ = "promotion_recipients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    promotion_id = Column(UUID(as_uuid=True), ForeignKey("promotions.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    telegram_sent = Column(Boolean, default=False)
    sms_sent = Column(Boolean, default=False)
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("promotion_id", "customer_id", name="uq_promotion_recipient"),
    )

    promotion = relationship("Promotion", back_populates="recipients")
    customer = relationship("Customer", back_populates="promotion_recipients")
