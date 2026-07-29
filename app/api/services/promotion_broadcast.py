from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload

from app.api.services.media_storage import media_disk_path
from app.api.services.telegram_notify import (
    format_promotion_message,
    mini_app_keyboard,
    send_promotion_telegram,
)
from app.models.customer import Customer
from app.models.promotion import Promotion
from app.models.promotion_recipient import PromotionRecipient
from app.models.telegram_log import TelegramLog
from app.schemas.promotion import PromotionBroadcastRequest, PromotionBroadcastResult


def get_promotion(db: Session, promotion_id: UUID) -> Promotion:
    promotion = db.get(Promotion, promotion_id)
    if promotion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")
    return promotion


def _promotion_message(promotion: Promotion) -> tuple[str, object]:
    message = format_promotion_message(
        promotion.title,
        promotion.description,
        promotion.discount_type,
        promotion.discount_value,
        promotion.start_date,
        promotion.end_date,
    )
    return message, mini_app_keyboard()


async def _deliver_promotion_telegram(
    customer: Customer,
    promotion: Promotion,
    message: str,
    keyboard: object,
) -> dict:
    return await send_promotion_telegram(
        int(customer.telegram_id),
        message,
        media_type=promotion.media_type,
        media_path=media_disk_path(promotion.media_filename),
        reply_markup=keyboard,  # type: ignore[arg-type]
    )


def _target_customers(db: Session, filters: PromotionBroadcastRequest) -> list[Customer]:
    query = select(Customer).where(
        Customer.is_active.is_(True),
        Customer.telegram_id.isnot(None),
    )

    conditions = []
    if filters.min_visits is not None:
        conditions.append(Customer.total_visits >= filters.min_visits)
    if filters.min_spending is not None:
        conditions.append(Customer.total_spending >= filters.min_spending)
    if filters.max_days_since_visit is not None:
        cutoff = date.today() - timedelta(days=filters.max_days_since_visit)
        conditions.append(Customer.last_visit_date >= cutoff)

    if conditions:
        query = query.where(and_(*conditions))

    return list(db.scalars(query).all())


async def broadcast_promotion(
    db: Session,
    promotion_id: UUID,
    filters: PromotionBroadcastRequest,
) -> PromotionBroadcastResult:
    promotion = get_promotion(db, promotion_id)
    customers = _target_customers(db, filters)

    message, keyboard = _promotion_message(promotion)

    telegram_sent = 0
    telegram_failed = 0
    sms_queued = 0

    for customer in customers:
        recipient = db.scalar(
            select(PromotionRecipient).where(
                PromotionRecipient.promotion_id == promotion.id,
                PromotionRecipient.customer_id == customer.id,
            )
        )
        if recipient is None:
            recipient = PromotionRecipient(
                promotion_id=promotion.id,
                customer_id=customer.id,
            )
            db.add(recipient)
            db.flush()

        try:
            result = await _deliver_promotion_telegram(
                customer, promotion, message, keyboard
            )
            recipient.telegram_sent = True
            recipient.delivered = True
            recipient.delivered_at = datetime.now(timezone.utc)
            db.add(
                TelegramLog(
                    customer_id=customer.id,
                    telegram_id=customer.telegram_id,
                    message=message,
                    message_type="promotion",
                    telegram_message_id=result.get("message_id"),
                    delivery_status="sent",
                )
            )
            telegram_sent += 1
        except Exception as exc:
            recipient.telegram_sent = False
            db.add(
                TelegramLog(
                    customer_id=customer.id,
                    telegram_id=customer.telegram_id,
                    message=f"{message}\n\n[error] {exc}",
                    message_type="promotion",
                    delivery_status="failed",
                )
            )
            telegram_failed += 1
            # SMS fallback is queued in Phase 9; count intent only for now
            if filters.send_sms_fallback:
                sms_queued += 1

    db.commit()
    return PromotionBroadcastResult(
        promotion_id=promotion.id,
        recipients_total=len(customers),
        telegram_sent=telegram_sent,
        telegram_failed=telegram_failed,
        sms_queued=sms_queued,
    )


async def retry_promotion_recipient(
    db: Session,
    promotion_id: UUID,
    recipient_id: UUID,
) -> PromotionRecipient:
    """Resend a failed promotion Telegram delivery to one recipient."""
    promotion = get_promotion(db, promotion_id)
    recipient = db.scalar(
        select(PromotionRecipient)
        .options(selectinload(PromotionRecipient.customer))
        .where(
            PromotionRecipient.id == recipient_id,
            PromotionRecipient.promotion_id == promotion.id,
        )
    )
    if recipient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found for this promotion",
        )

    if recipient.telegram_sent or recipient.delivered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This recipient was already delivered successfully",
        )

    customer = recipient.customer
    if customer is None or customer.telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer has no Telegram ID to retry",
        )
    if not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer is deactivated",
        )

    message, keyboard = _promotion_message(promotion)

    try:
        result = await _deliver_promotion_telegram(
            customer, promotion, message, keyboard
        )
        recipient.telegram_sent = True
        recipient.delivered = True
        recipient.delivered_at = datetime.now(timezone.utc)
        db.add(
            TelegramLog(
                customer_id=customer.id,
                telegram_id=customer.telegram_id,
                message=message,
                message_type="promotion",
                telegram_message_id=result.get("message_id"),
                delivery_status="sent",
            )
        )
        db.commit()
        db.refresh(recipient)
        return recipient
    except Exception as exc:
        recipient.telegram_sent = False
        recipient.delivered = False
        db.add(
            TelegramLog(
                customer_id=customer.id,
                telegram_id=customer.telegram_id,
                message=f"{message}\n\n[retry error] {exc}",
                message_type="promotion",
                delivery_status="failed",
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Retry failed: {exc}",
        ) from exc
