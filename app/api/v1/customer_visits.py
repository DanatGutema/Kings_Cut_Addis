from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentStaff, DbSession
from app.api.services import visits as visit_service
from app.schemas.pagination import PaginatedResponse
from app.schemas.visit import VisitOut

router = APIRouter(tags=["customers"])


@router.get("/{customer_id}/visits", response_model=PaginatedResponse[VisitOut])
def get_customer_visits(
    customer_id: UUID,
    db: DbSession,
    _: CurrentStaff,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[VisitOut]:
    visits, total = visit_service.list_customer_visits(db, customer_id, skip, limit)
    return PaginatedResponse(
        items=[VisitOut.model_validate(v) for v in visits],
        total=total,
        skip=skip,
        limit=limit,
    )
