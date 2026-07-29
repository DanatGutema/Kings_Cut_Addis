from datetime import date
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload

from app.api.deps import AdminStaff, CurrentStaff, DbSession
from app.api.services.media_storage import (
    delete_media_file,
    media_public_url,
    save_promotion_media,
)
from app.api.services.promotion_broadcast import (
    broadcast_promotion,
    get_promotion,
    retry_promotion_recipient,
)
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


def _delivery_counts(db: DbSession, promotion_id: UUID) -> tuple[int, int, int]:
    total = (
        db.scalar(
            select(func.count())
            .select_from(PromotionRecipient)
            .where(PromotionRecipient.promotion_id == promotion_id)
        )
        or 0
    )
    sent = (
        db.scalar(
            select(func.count())
            .select_from(PromotionRecipient)
            .where(
                PromotionRecipient.promotion_id == promotion_id,
                PromotionRecipient.telegram_sent.is_(True),
            )
        )
        or 0
    )
    failed = max(total - sent, 0)
    return total, sent, failed


def _promotion_out(db: DbSession, promotion: Promotion) -> PromotionOut:
    total, sent, failed = _delivery_counts(db, promotion.id)
    data = PromotionOut.model_validate(promotion)
    return data.model_copy(
        update={
            "recipients_total": total,
            "telegram_sent": sent,
            "telegram_failed": failed,
            "media_url": media_public_url(promotion.media_filename),
        }
    )


def _recipient_out(recipient: PromotionRecipient) -> PromotionRecipientOut:
    customer = recipient.customer
    name = None
    phone = None
    if customer is not None:
        name = f"{customer.first_name} {customer.last_name or ''}".strip()
        phone = customer.phone_number
    data = PromotionRecipientOut.model_validate(recipient)
    return data.model_copy(
        update={
            "customer_name": name,
            "customer_phone": phone,
        }
    )


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
        items=[_promotion_out(db, p) for p in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=PromotionOut, status_code=status.HTTP_201_CREATED)
def create_promotion(
    body: PromotionCreate,
    db: DbSession,
    current_staff: AdminStaff,
) -> PromotionOut:
    if body.end_date < body.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be on or after start_date",
        )

    promotion = Promotion(**body.model_dump(), created_by=current_staff.id)
    db.add(promotion)
    db.commit()
    db.refresh(promotion)
    return _promotion_out(db, promotion)


@router.get("/{promotion_id}", response_model=PromotionOut)
def get_promotion_endpoint(
    promotion_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> PromotionOut:
    return _promotion_out(db, get_promotion(db, promotion_id))


@router.patch("/{promotion_id}", response_model=PromotionOut)
def update_promotion(
    promotion_id: UUID,
    body: PromotionUpdate,
    db: DbSession,
    _: AdminStaff,
) -> PromotionOut:
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
    return _promotion_out(db, promotion)


@router.post("/{promotion_id}/deactivate", response_model=PromotionOut)
def deactivate_promotion(
    promotion_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> PromotionOut:
    promotion = get_promotion(db, promotion_id)
    promotion.is_active = False
    db.commit()
    db.refresh(promotion)
    return _promotion_out(db, promotion)


@router.post("/{promotion_id}/activate", response_model=PromotionOut)
def activate_promotion(
    promotion_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> PromotionOut:
    promotion = get_promotion(db, promotion_id)
    promotion.is_active = True
    db.commit()
    db.refresh(promotion)
    return _promotion_out(db, promotion)


@router.post("/{promotion_id}/media", response_model=PromotionOut)
async def upload_promotion_media(
    promotion_id: UUID,
    db: DbSession,
    _: AdminStaff,
    file: UploadFile = File(...),
) -> PromotionOut:
    promotion = get_promotion(db, promotion_id)
    media_type, filename = await save_promotion_media(file)
    delete_media_file(promotion.media_filename)
    promotion.media_type = media_type
    promotion.media_filename = filename
    db.commit()
    db.refresh(promotion)
    return _promotion_out(db, promotion)


@router.delete("/{promotion_id}/media", response_model=PromotionOut)
def delete_promotion_media(
    promotion_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> PromotionOut:
    promotion = get_promotion(db, promotion_id)
    delete_media_file(promotion.media_filename)
    promotion.media_type = None
    promotion.media_filename = None
    db.commit()
    db.refresh(promotion)
    return _promotion_out(db, promotion)


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

    delete_media_file(promotion.media_filename)
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


@router.post(
    "/{promotion_id}/recipients/{recipient_id}/retry",
    response_model=PromotionRecipientOut,
)
async def retry_promotion_recipient_endpoint(
    promotion_id: UUID,
    recipient_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> PromotionRecipientOut:
    recipient = await retry_promotion_recipient(db, promotion_id, recipient_id)
    return _recipient_out(recipient)


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
        .options(selectinload(PromotionRecipient.customer))
        .where(PromotionRecipient.promotion_id == promotion_id)
        .order_by(PromotionRecipient.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    return PaginatedResponse(
        items=[_recipient_out(r) for r in recipients],
        total=total,
        skip=skip,
        limit=limit,
    )
