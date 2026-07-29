from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import AdminStaff, CurrentStaff, DbSession
from app.models.appointment import Appointment
from app.models.barber import Barber
from app.schemas.barber import BarberCreate, BarberOut, BarberUpdate

router = APIRouter(prefix="/barbers", tags=["barbers"])


def _normalize_email(email: str | None) -> str | None:
    if email is None:
        return None
    cleaned = email.strip().lower()
    return cleaned or None


@router.get("", response_model=list[BarberOut])
def list_barbers(
    db: DbSession,
    _: CurrentStaff,
    active_only: bool = Query(False),
):
    """List barbers for admin/staff (dashboard)."""
    query = select(Barber).order_by(Barber.first_name.asc(), Barber.last_name.asc())
    if active_only:
        query = query.where(Barber.is_active.is_(True))
    return list(db.scalars(query).all())


@router.post("", response_model=BarberOut, status_code=status.HTTP_201_CREATED)
def create_barber(
    body: BarberCreate,
    db: DbSession,
    _: AdminStaff,
) -> BarberOut:
    phone = body.phone_number.strip()
    email = _normalize_email(str(body.email) if body.email else None)

    if db.scalar(select(Barber).where(Barber.phone_number == phone)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered for a barber",
        )
    if email and db.scalar(select(Barber).where(Barber.email == email)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered for a barber",
        )

    barber = Barber(
        first_name=body.first_name.strip(),
        last_name=(body.last_name or "").strip() or None,
        phone_number=phone,
        email=email,
        specialty=(body.specialty or "").strip() or None,
        notes=(body.notes or "").strip() or None,
        is_active=True,
    )
    db.add(barber)
    db.commit()
    db.refresh(barber)
    return barber


@router.patch("/{barber_id}", response_model=BarberOut)
def update_barber(
    barber_id: UUID,
    body: BarberUpdate,
    db: DbSession,
    _: AdminStaff,
) -> BarberOut:
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barber not found")

    updates = body.model_dump(exclude_unset=True)
    if "phone_number" in updates and updates["phone_number"] is not None:
        phone = updates["phone_number"].strip()
        conflict = db.scalar(
            select(Barber).where(Barber.phone_number == phone, Barber.id != barber.id)
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered for a barber",
            )
        updates["phone_number"] = phone

    if "email" in updates:
        email = _normalize_email(str(updates["email"]) if updates["email"] else None)
        if email:
            conflict = db.scalar(
                select(Barber).where(Barber.email == email, Barber.id != barber.id)
            )
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered for a barber",
                )
        updates["email"] = email

    for field in ("first_name", "last_name", "specialty", "notes"):
        if field in updates and isinstance(updates[field], str):
            updates[field] = updates[field].strip() or None
            if field == "first_name" and not updates[field]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="First name is required",
                )

    for field, value in updates.items():
        setattr(barber, field, value)

    db.commit()
    db.refresh(barber)
    return barber


@router.post("/{barber_id}/deactivate", response_model=BarberOut)
def deactivate_barber(
    barber_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> BarberOut:
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barber not found")
    barber.is_active = False
    db.commit()
    db.refresh(barber)
    return barber


@router.post("/{barber_id}/activate", response_model=BarberOut)
def activate_barber(
    barber_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> BarberOut:
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barber not found")
    barber.is_active = True
    db.commit()
    db.refresh(barber)
    return barber


@router.delete("/{barber_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_barber(
    barber_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> None:
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barber not found")

    if barber.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deactivate the barber before deleting",
        )

    linked = db.scalar(
        select(func.count()).select_from(Appointment).where(Appointment.preferred_barber_id == barber.id)
    )
    if linked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Cannot delete this barber because they are linked to appointments. "
                "Keep them deactivated instead."
            ),
        )

    db.delete(barber)
    db.commit()
    return None
