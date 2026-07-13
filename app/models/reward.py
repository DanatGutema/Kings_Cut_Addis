import uuid

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Reward(Base):
    __tablename__ = "rewards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    loyalty_rule_id = Column(UUID(as_uuid=True), ForeignKey("loyalty_rules.id"), nullable=False)
    reward_type = Column(String(30), nullable=False)
    reward_percentage = Column(Numeric(5, 2), nullable=True)
    reward_amount = Column(Numeric(12, 2), nullable=True)
    earned_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(String(30), default="pending")
    redeemed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','redeemed','expired','void')",
            name="check_reward_status",
        ),
    )

    customer = relationship("Customer", back_populates="rewards")
    loyalty_rule = relationship("LoyaltyRule", back_populates="rewards")
    history = relationship("RewardHistory", back_populates="reward", cascade="all, delete-orphan")
