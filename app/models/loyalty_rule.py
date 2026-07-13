import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class LoyaltyRule(Base):
    __tablename__ = "loyalty_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(String(30), nullable=False)
    visit_threshold = Column(Integer, nullable=True)
    spending_threshold = Column(Numeric(12, 2), nullable=True)
    reward_type = Column(String(30), nullable=False)
    reward_percentage = Column(Numeric(5, 2), nullable=True)
    reward_amount = Column(Numeric(12, 2), nullable=True)
    expiry_days = Column(Integer, nullable=False)
    evaluation_period_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("rule_type IN ('visit','spending')", name="check_rule_type"),
        CheckConstraint(
            "reward_type IN ('percentage','fixed','both')",
            name="check_reward_type",
        ),
    )

    rewards = relationship("Reward", back_populates="loyalty_rule")
