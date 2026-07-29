import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="pending")
    preferred_barber_id = Column(UUID(as_uuid=True), ForeignKey("barbers.id"), nullable=True)
    handled_by_staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=True)
    responded_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','accepted','rejected','completed')",
            name="check_appointment_status",
        ),
    )

    customer = relationship("Customer", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    preferred_barber = relationship("Barber", back_populates="appointments")
    handled_by_staff = relationship("Staff", foreign_keys=[handled_by_staff_id])
    visit = relationship("Visit", foreign_keys=[visit_id])
