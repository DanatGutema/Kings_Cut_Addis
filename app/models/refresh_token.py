import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    token_hash = Column(Text, nullable=False)
    device_name = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)
    ip_address = Column(String(50), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "(customer_id IS NOT NULL AND staff_id IS NULL) OR "
            "(customer_id IS NULL AND staff_id IS NOT NULL)",
            name="check_token_owner",
        ),
    )

    customer = relationship("Customer", back_populates="refresh_tokens")
    staff = relationship("Staff", back_populates="refresh_tokens")
