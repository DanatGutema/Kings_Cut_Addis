from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import and_, func, select

from app.api.deps import AdminStaff, CurrentStaff, DbSession
from app.api.services.promotion_broadcast import broadcast_promotion, get_promotion
from app.models.promotion import Promotion
from app.models.promotion_recipient import PromotionRecipient
from app.schemas.pagination import PaginatedResponse
from app.schemas.promotion import (
    PromotionBroadcastRequest,
    PromotionBroadcastResult,
    PromotionCreate,
    PromotionOut,
    PromotionRecipientOut,
    PromotionUpdate,
)

router = APIRouter(prefix="/promotions", tags=["promotions"])


@router.get("", response_model=PaginatedResponse[PromotionOut])
def list_promotions(
    db: DbSession,
    _: CurrentStaff,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(False),
    currently_valid: bool = Query(False, description="Only promotions within start/end dates"),
) -> PaginatedResponse[PromotionOut]:
    query = select(Promotion)
    count_query = select(func.count()).select_from(Promotion)
    filters = []

    if active_only:
        filters.append(Promotion.is_active.is_(True))
    if currently_valid:
        today = date.today()
        filters.append(Promotion.start_date <= today)
        filters.append(Promotion.end_date >= today)
        filters.append(Promotion.is_active.is_(True))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = db.scalar(count_query) or 0
    items = db.scalars(
        query.order_by(Promotion.created_at.desc()).offset(skip).limit(limit)
    ).all()

    return PaginatedResponse(
        items=[PromotionOut.model_validate(p) for p in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=PromotionOut, status_code=status.HTTP_201_CREATED)
def create_promotion(
    body: PromotionCreate,
    db: DbSession,
    current_staff: AdminStaff,
) -> Promotion:
    if body.end_date < body.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be on or after start_date",
        )

    promotion = Promotion(**body.model_dump(), created_by=current_staff.id)
    db.add(promotion)
    db.commit()
    db.refresh(promotion)
    return promotion


@router.get("/{promotion_id}", response_model=PromotionOut)
def get_promotion_endpoint(
    promotion_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> Promotion:
    return get_promotion(db, promotion_id)


@router.patch("/{promotion_id}", response_model=PromotionOut)
def update_promotion(
    promotion_id: UUID,
    body: PromotionUpdate,
    db: DbSession,
    _: AdminStaff,
) -> Promotion:
    promotion = get_promotion(db, promotion_id)
    updates = body.model_dump(exclude_unset=True)

    start = updates.get("start_date", promotion.start_date)
    end = updates.get("end_date", promotion.end_date)
    if end < start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be on or after start_date",
        )

    for field, value in updates.items():
        setattr(promotion, field, value)

    db.commit()
    db.refresh(promotion)
    return promotion


@router.post("/{promotion_id}/deactivate", response_model=PromotionOut)
def deactivate_promotion(
    promotion_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> Promotion:
    promotion = get_promotion(db, promotion_id)
    promotion.is_active = False
    db.commit()
    db.refresh(promotion)
    return promotion


@router.post("/{promotion_id}/activate", response_model=PromotionOut)
def activate_promotion(
    promotion_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> Promotion:
    promotion = get_promotion(db, promotion_id)
    promotion.is_active = True
    db.commit()
    db.refresh(promotion)
    return promotion


@router.delete("/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_promotion(
    promotion_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> None:
    """Permanently delete a deactivated promotion only when it has no recipients."""
    promotion = get_promotion(db, promotion_id)

    if promotion.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deactivate the promotion before deleting",
        )

    if (
        db.query(PromotionRecipient.id)
        .filter(PromotionRecipient.promotion_id == promotion.id)
        .first()
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Cannot delete this promotion because it has related broadcast recipients. "
                "Keep it deactivated instead."
            ),
        )

    db.delete(promotion)
    db.commit()
    return None


@router.post("/{promotion_id}/broadcast", response_model=PromotionBroadcastResult)
async def broadcast_promotion_endpoint(
    promotion_id: UUID,
    body: PromotionBroadcastRequest,
    db: DbSession,
    _: AdminStaff,
) -> PromotionBroadcastResult:
    return await broadcast_promotion(db, promotion_id, body)


@router.get(
    "/{promotion_id}/recipients",
    response_model=PaginatedResponse[PromotionRecipientOut],
)
def list_promotion_recipients(
    promotion_id: UUID,
    db: DbSession,
    _: CurrentStaff,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[PromotionRecipientOut]:
    get_promotion(db, promotion_id)

    total = (
        db.scalar(
            select(func.count())
            .select_from(PromotionRecipient)
            .where(PromotionRecipient.promotion_id == promotion_id)
        )
        or 0
    )
    recipients = db.scalars(
        select(PromotionRecipient)
        .where(PromotionRecipient.promotion_id == promotion_id)
        .order_by(PromotionRecipient.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    return PaginatedResponse(
        items=[PromotionRecipientOut.model_validate(r) for r in recipients],
        total=total,
        skip=skip,
        limit=limit,
    )
