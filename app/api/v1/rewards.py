from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AdminStaff, CurrentStaff, DbSession
from app.api.services import rewards as reward_service
from app.api.services.loyalty_engine import get_rule_progress
from app.models.customer import Customer
from app.models.loyalty_rule import LoyaltyRule
from app.models.reward import Reward
from app.schemas.loyalty import LoyaltyProgressOut, RuleProgressOut
from app.schemas.pagination import PaginatedResponse
from app.schemas.reward import RewardHistoryOut, RewardOut, RewardRedeem, RewardVoid

router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.get("", response_model=PaginatedResponse[RewardOut])
def list_rewards(
    db: DbSession,
    _: CurrentStaff,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    customer_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    loyalty_rule_id: UUID | None = Query(None),
) -> PaginatedResponse[RewardOut]:
    rewards, total = reward_service.list_rewards(
        db,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        status_filter=status_filter,
        loyalty_rule_id=loyalty_rule_id,
    )
    return PaginatedResponse(
        items=[RewardOut.model_validate(r) for r in rewards],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/expire-stale", response_model=dict)
def expire_stale_rewards(
    db: DbSession,
    _: AdminStaff,
) -> dict:
    count = reward_service.expire_stale_rewards(db)
    return {"expired_count": count}


@router.get("/{reward_id}", response_model=RewardOut)
def get_reward(
    reward_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> Reward:
    reward = db.scalar(
        select(Reward)
        .options(selectinload(Reward.history))
        .where(Reward.id == reward_id)
    )
    if reward is None:
        raise HTTPException(status_code=404, detail="Reward not found")
    return reward


@router.post("/{reward_id}/redeem", response_model=RewardOut)
def redeem_reward(
    reward_id: UUID,
    body: RewardRedeem,
    db: DbSession,
    current_staff: CurrentStaff,
) -> Reward:
    reward = reward_service.redeem_reward(db, reward_id, current_staff, body)
    return db.scalar(
        select(Reward)
        .options(selectinload(Reward.history))
        .where(Reward.id == reward.id)
    )


@router.post("/{reward_id}/void", response_model=RewardOut)
def void_reward(
    reward_id: UUID,
    body: RewardVoid,
    db: DbSession,
    current_staff: CurrentStaff,
) -> Reward:
    reward = reward_service.void_reward(db, reward_id, current_staff, body)
    return db.scalar(
        select(Reward)
        .options(selectinload(Reward.history))
        .where(Reward.id == reward.id)
    )


@router.get("/{reward_id}/history", response_model=list[RewardHistoryOut])
def get_reward_history(
    reward_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> list:
    reward = db.scalar(
        select(Reward)
        .options(selectinload(Reward.history))
        .where(Reward.id == reward_id)
    )
    if reward is None:
        raise HTTPException(status_code=404, detail="Reward not found")
    return reward.history


loyalty_router = APIRouter(tags=["loyalty"])


@loyalty_router.get("/customers/{customer_id}/loyalty-progress", response_model=LoyaltyProgressOut)
def get_customer_loyalty_progress(
    customer_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> LoyaltyProgressOut:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    rules = db.scalars(
        select(LoyaltyRule).where(LoyaltyRule.is_active.is_(True))
    ).all()

    progress = [
        RuleProgressOut.model_validate(get_rule_progress(db, customer_id, rule))
        for rule in rules
    ]

    return LoyaltyProgressOut(
        customer_id=customer.id,
        total_visits=customer.total_visits,
        total_spending=customer.total_spending,
        rules=progress,
    )
