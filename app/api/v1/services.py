from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import AdminStaff, CurrentStaff, DbSession
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.service_order_item import ServiceOrderItem
from app.models.visit_service import VisitService
from app.schemas.pagination import PaginatedResponse
from app.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=PaginatedResponse[ServiceOut])
def list_services(
    db: DbSession,
    _: CurrentStaff,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(True),
) -> PaginatedResponse[ServiceOut]:
    query = select(Service)
    count_query = select(func.count()).select_from(Service)

    if active_only:
        query = query.where(Service.is_active.is_(True))
        count_query = count_query.where(Service.is_active.is_(True))

    total = db.scalar(count_query) or 0
    services = db.scalars(
        query.order_by(Service.name).offset(skip).limit(limit)
    ).all()

    return PaginatedResponse(
        items=[ServiceOut.model_validate(s) for s in services],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    body: ServiceCreate,
    db: DbSession,
    _: AdminStaff,
) -> Service:
    existing = db.scalar(select(Service).where(Service.name == body.name))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service name already exists")

    service = Service(**body.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(
    service_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> Service:
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


@router.patch("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: UUID,
    body: ServiceUpdate,
    db: DbSession,
    _: AdminStaff,
) -> Service:
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    updates = body.model_dump(exclude_unset=True)
    if "name" in updates:
        conflict = db.scalar(
            select(Service).where(Service.name == updates["name"], Service.id != service_id)
        )
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service name already exists")

    for field, value in updates.items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)
    return service


@router.post("/{service_id}/deactivate", response_model=ServiceOut)
def deactivate_service(
    service_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> Service:
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    service.is_active = False
    db.commit()
    db.refresh(service)
    return service


@router.post("/{service_id}/activate", response_model=ServiceOut)
def activate_service(
    service_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> Service:
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    service.is_active = True
    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> None:
    """Permanently delete a deactivated service only when it has no related usage data."""
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    if service.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deactivate the service before deleting",
        )

    blockers: list[str] = []
    if db.query(VisitService.id).filter(VisitService.service_id == service.id).first():
        blockers.append("visits")
    if db.query(ServiceOrderItem.id).filter(ServiceOrderItem.service_id == service.id).first():
        blockers.append("service orders")
    if db.query(Appointment.id).filter(Appointment.service_id == service.id).first():
        blockers.append("appointments")

    if blockers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Cannot delete this service because it has related "
                f"{', '.join(blockers)}. Keep it deactivated instead."
            ),
        )

    db.delete(service)
    db.commit()
    return None
