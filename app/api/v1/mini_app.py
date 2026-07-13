from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import and_, select

from app.api.core.security import create_access_token
from app.api.core.telegram_auth import validate_init_data
from app.api.deps import CurrentCustomer, DbSession
from app.api.services.loyalty_engine import get_rule_progress
from app.models.customer import Customer
from app.models.customer_session import CustomerSession
from app.models.loyalty_rule import LoyaltyRule
from app.models.promotion import Promotion
from app.models.reward import Reward
from app.schemas.auth import TelegramAuthRequest
from app.schemas.customer import CustomerOut
from app.schemas.loyalty import LoyaltyProgressOut, RuleProgressOut
from app.schemas.promotion import PromotionOut
from app.schemas.reward import RewardOut
from pydantic import BaseModel

router = APIRouter(prefix="/mini-app", tags=["mini-app"])


class MiniAppAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer: CustomerOut
    needs_phone: bool = False


class QrOut(BaseModel):
    qr_token: UUID
    customer_name: str
    phone_number: str


@router.post("/auth", response_model=MiniAppAuthResponse)
def mini_app_auth(body: TelegramAuthRequest, db: DbSession) -> MiniAppAuthResponse:
    validated = validate_init_data(body.init_data)
    tg_user = validated["user"]
    telegram_id = tg_user.get("id")
    if not telegram_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram user")

    customer = db.scalar(select(Customer).where(Customer.telegram_id == telegram_id))
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Open the bot first and share your phone number to activate loyalty.",
        )
    if not customer.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    db.add(
        CustomerSession(
            customer_id=customer.id,
            login_method="telegram",
            device_name="telegram-mini-app",
            is_active=True,
        )
    )
    db.commit()
    db.refresh(customer)

    token = create_access_token(subject=customer.id, role="customer")
    return MiniAppAuthResponse(
        access_token=token,
        customer=CustomerOut.model_validate(customer),
        needs_phone=False,
    )


@router.get("/me", response_model=CustomerOut)
def mini_app_me(customer: CurrentCustomer) -> Customer:
    return customer


@router.get("/qr", response_model=QrOut)
def mini_app_qr(customer: CurrentCustomer) -> QrOut:
    return QrOut(
        qr_token=customer.qr_token,
        customer_name=f"{customer.first_name} {customer.last_name or ''}".strip(),
        phone_number=customer.phone_number,
    )


@router.get("/loyalty-progress", response_model=LoyaltyProgressOut)
def mini_app_loyalty(customer: CurrentCustomer, db: DbSession) -> LoyaltyProgressOut:
    rules = db.scalars(select(LoyaltyRule).where(LoyaltyRule.is_active.is_(True))).all()
    progress = [
        RuleProgressOut.model_validate(get_rule_progress(db, customer.id, rule))
        for rule in rules
    ]
    return LoyaltyProgressOut(
        customer_id=customer.id,
        total_visits=customer.total_visits,
        total_spending=customer.total_spending,
        loyalty_status=customer.loyalty_status,
        rules=progress,
    )


@router.get("/rewards", response_model=list[RewardOut])
def mini_app_rewards(customer: CurrentCustomer, db: DbSession) -> list[Reward]:
    return list(
        db.scalars(
            select(Reward)
            .where(Reward.customer_id == customer.id)
            .order_by(Reward.earned_date.desc())
        ).all()
    )


@router.get("/promotions", response_model=list[PromotionOut])
def mini_app_promotions(db: DbSession, customer: CurrentCustomer) -> list[Promotion]:
    today = date.today()
    return list(
        db.scalars(
            select(Promotion)
            .where(
                and_(
                    Promotion.is_active.is_(True),
                    Promotion.start_date <= today,
                    Promotion.end_date >= today,
                )
            )
            .order_by(Promotion.start_date.desc())
        ).all()
    )
