"""Appointment booking, staff decisions, and visit creation on completion."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.services.telegram_notify import mini_app_keyboard, send_telegram_message
from app.api.services.visits import create_visit
from app.models.appointment import Appointment
from app.models.customer import Customer
from app.models.service import Service
from app.models.staff import Staff
from app.schemas.appointment import AppointmentCreate, AppointmentOut
from app.schemas.visit import VisitCreate, VisitServiceItemCreate


def _to_out(appointment: Appointment) -> AppointmentOut:
    customer = appointment.customer
    service = appointment.service
    customer_name = None
    customer_phone = None
    if customer is not None:
        customer_name = f"{customer.first_name} {customer.last_name or ''}".strip()
        customer_phone = customer.phone_number
    return AppointmentOut(
        id=appointment.id,
        customer_id=appointment.customer_id,
        service_id=appointment.service_id,
        scheduled_at=appointment.scheduled_at,
        notes=appointment.notes,
        status=appointment.status,
        handled_by_staff_id=appointment.handled_by_staff_id,
        visit_id=appointment.visit_id,
        responded_at=appointment.responded_at,
        completed_at=appointment.completed_at,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        customer_name=customer_name,
        customer_phone=customer_phone,
        service_name=service.name if service else None,
        service_price=service.price if service else None,
    )


def _load_appointment(db: Session, appointment_id: UUID) -> Appointment:
    appointment = db.scalar(
        select(Appointment)
        .options(
            selectinload(Appointment.customer),
            selectinload(Appointment.service),
        )
        .where(Appointment.id == appointment_id)
    )
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appointment


async def _notify_customer(customer: Customer, text: str) -> None:
    if not customer.telegram_id:
        return
    try:
        await send_telegram_message(
            int(customer.telegram_id),
            text,
            reply_markup=mini_app_keyboard(),
        )
    except Exception as exc:  # noqa: BLE001 — notification must not block workflow
        print(f"Warning: appointment Telegram notify failed: {exc}")


def create_appointment(
    db: Session,
    customer: Customer,
    data: AppointmentCreate,
) -> AppointmentOut:
    if not customer.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    service = db.get(Service, data.service_id)
    if service is None or not service.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service not found or inactive",
        )

    if data.scheduled_at.tzinfo is not None:
        scheduled_at = data.scheduled_at.astimezone().replace(tzinfo=None)
    else:
        scheduled_at = data.scheduled_at

    if scheduled_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment time must be in the future",
        )

    appointment = Appointment(
        customer_id=customer.id,
        service_id=service.id,
        scheduled_at=scheduled_at,
        notes=data.notes,
        status="pending",
    )
    db.add(appointment)
    db.commit()
    return _to_out(_load_appointment(db, appointment.id))


def list_appointments(
    db: Session,
    *,
    skip: int,
    limit: int,
    status_filter: str | None = None,
    customer_id: UUID | None = None,
) -> tuple[list[AppointmentOut], int]:
    filters = []
    if status_filter:
        filters.append(Appointment.status == status_filter)
    if customer_id is not None:
        filters.append(Appointment.customer_id == customer_id)

    count_query = select(func.count()).select_from(Appointment)
    list_query = (
        select(Appointment)
        .options(
            selectinload(Appointment.customer),
            selectinload(Appointment.service),
        )
        .order_by(Appointment.created_at.desc(), Appointment.scheduled_at.desc())
    )
    if filters:
        count_query = count_query.where(*filters)
        list_query = list_query.where(*filters)

    total = db.scalar(count_query) or 0
    rows = db.scalars(list_query.offset(skip).limit(limit)).all()
    return [_to_out(row) for row in rows], total


async def accept_appointment(
    db: Session,
    appointment_id: UUID,
    staff: Staff,
) -> AppointmentOut:
    appointment = _load_appointment(db, appointment_id)
    if appointment.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending appointments can be accepted",
        )

    appointment.status = "accepted"
    appointment.handled_by_staff_id = staff.id
    appointment.responded_at = datetime.utcnow()
    db.commit()
    appointment = _load_appointment(db, appointment_id)

    when = appointment.scheduled_at.strftime("%Y-%m-%d %H:%M")
    service_name = appointment.service.name if appointment.service else "your service"
    await _notify_customer(
        appointment.customer,
        (
            f"✅ <b>Appointment accepted</b>\n\n"
            f"Service: <b>{service_name}</b>\n"
            f"Time: <b>{when}</b>\n\n"
            f"See you at Kings Cut Addis."
        ),
    )
    return _to_out(appointment)


async def reject_appointment(
    db: Session,
    appointment_id: UUID,
    staff: Staff,
) -> AppointmentOut:
    appointment = _load_appointment(db, appointment_id)
    if appointment.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending appointments can be rejected",
        )

    appointment.status = "rejected"
    appointment.handled_by_staff_id = staff.id
    appointment.responded_at = datetime.utcnow()
    db.commit()
    appointment = _load_appointment(db, appointment_id)

    when = appointment.scheduled_at.strftime("%Y-%m-%d %H:%M")
    service_name = appointment.service.name if appointment.service else "your service"
    await _notify_customer(
        appointment.customer,
        (
            f"❌ <b>Appointment declined</b>\n\n"
            f"Service: <b>{service_name}</b>\n"
            f"Requested time: <b>{when}</b>\n\n"
            f"Please book another time in the Mini App."
        ),
    )
    return _to_out(appointment)


async def complete_appointment(
    db: Session,
    appointment_id: UUID,
    staff: Staff,
) -> AppointmentOut:
    appointment = _load_appointment(db, appointment_id)
    if appointment.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only accepted appointments can be completed",
        )
    if appointment.visit_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment already completed",
        )

    completed_at = datetime.utcnow()
    notes = appointment.notes
    if notes:
        notes = f"{notes} (from appointment)"
    else:
        notes = "Completed from appointment"

    visit = create_visit(
        db,
        VisitCreate(
            customer_id=appointment.customer_id,
            staff_id=staff.id,
            visit_date=completed_at,
            notes=notes,
            services=[VisitServiceItemCreate(service_id=appointment.service_id, quantity=1)],
        ),
    )

    appointment = _load_appointment(db, appointment_id)
    appointment.status = "completed"
    appointment.handled_by_staff_id = staff.id
    appointment.completed_at = completed_at
    appointment.visit_id = visit.id
    db.commit()
    appointment = _load_appointment(db, appointment_id)

    service_name = appointment.service.name if appointment.service else "your service"
    await _notify_customer(
        appointment.customer,
        (
            f"✂️ <b>Service completed</b>\n\n"
            f"Service: <b>{service_name}</b>\n"
            f"Thanks for visiting Kings Cut Addis. "
            f"Your visit and loyalty progress are updated in the Mini App."
        ),
    )
    return _to_out(appointment)
