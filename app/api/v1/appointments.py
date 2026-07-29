from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentStaff, DbSession
from app.api.services import appointments as appointment_service
from app.schemas.appointment import AppointmentOut, StaffAppointmentCreate
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("", response_model=PaginatedResponse[AppointmentOut])
def list_appointments(
    db: DbSession,
    _: CurrentStaff,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
) -> PaginatedResponse[AppointmentOut]:
    if status_filter and status_filter not in ("pending", "accepted", "rejected", "completed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status filter",
        )
    items, total = appointment_service.list_appointments(
        db,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    body: StaffAppointmentCreate,
    db: DbSession,
    staff: CurrentStaff,
) -> AppointmentOut:
    """Staff log for phone / walk-in appointments (created as accepted)."""
    return appointment_service.create_staff_appointment(db, staff, body)


@router.post("/{appointment_id}/accept", response_model=AppointmentOut)
async def accept_appointment(
    appointment_id: UUID,
    db: DbSession,
    staff: CurrentStaff,
) -> AppointmentOut:
    return await appointment_service.accept_appointment(db, appointment_id, staff)


@router.post("/{appointment_id}/reject", response_model=AppointmentOut)
async def reject_appointment(
    appointment_id: UUID,
    db: DbSession,
    staff: CurrentStaff,
) -> AppointmentOut:
    return await appointment_service.reject_appointment(db, appointment_id, staff)


@router.post("/{appointment_id}/complete", response_model=AppointmentOut)
async def complete_appointment(
    appointment_id: UUID,
    db: DbSession,
    staff: CurrentStaff,
) -> AppointmentOut:
    return await appointment_service.complete_appointment(db, appointment_id, staff)
