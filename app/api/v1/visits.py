from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentStaff, DbSession
from app.api.services import visits as visit_service
from app.models.visit import Visit
from app.schemas.pagination import PaginatedResponse
from app.schemas.visit import VisitCreate, VisitOut, VisitUpdate

router = APIRouter(prefix="/visits", tags=["visits"])


@router.get("", response_model=PaginatedResponse[VisitOut])
def list_visits(
    db: DbSession,
    _: CurrentStaff,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    customer_id: UUID | None = Query(None),
    staff_id: UUID | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
) -> PaginatedResponse[VisitOut]:
    visits, total = visit_service.list_visits(
        db,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        staff_id=staff_id,
        date_from=date_from,
        date_to=date_to,
    )
    return PaginatedResponse(
        items=[VisitOut.model_validate(v) for v in visits],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=VisitOut, status_code=201)
def create_visit(
    body: VisitCreate,
    db: DbSession,
    _: CurrentStaff,
) -> Visit:
    return visit_service.create_visit(db, body)


@router.get("/{visit_id}", response_model=VisitOut)
def get_visit(
    visit_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> Visit:
    return visit_service.get_visit(db, visit_id)


@router.patch("/{visit_id}", response_model=VisitOut)
def update_visit(
    visit_id: UUID,
    body: VisitUpdate,
    db: DbSession,
    _: CurrentStaff,
) -> Visit:
    return visit_service.update_visit(db, visit_id, body)
