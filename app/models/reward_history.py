import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RewardHistory(Base):
    __tablename__ = "reward_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reward_id = Column(UUID(as_uuid=True), ForeignKey("rewards.id"), nullable=False)
    action = Column(String(30), nullable=True)
    action_date = Column(DateTime, nullable=False, server_default=func.now())
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "action IN ('earned','redeemed','expired','void')",
            name="check_history_action",
        ),
    )

    reward = relationship("Reward", back_populates="history")
    staff = relationship("Staff", back_populates="reward_history")
