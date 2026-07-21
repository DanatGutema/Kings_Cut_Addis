import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Staff(Base):
    __tablename__ = "staff"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    phone_number = Column(String(15), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="staff")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('admin','staff')", name="check_staff_role"),
    )

    visits = relationship("Visit", back_populates="staff")
    promotions = relationship("Promotion", back_populates="created_by_staff")
    reward_history = relationship("RewardHistory", back_populates="staff")
    refresh_tokens = relationship("RefreshToken", back_populates="staff")
    system_settings = relationship("SystemSetting", back_populates="updated_by_staff")
    audit_logs = relationship("AuditLog", back_populates="staff")


class StaffInvitation(Base):
    __tablename__ = "staff_invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    staff = relationship("Staff")