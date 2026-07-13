from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.reward import Reward
from app.models.reward_history import RewardHistory
from app.models.staff import Staff
from app.schemas.reward import RewardRedeem, RewardVoid


def _get_reward(db: Session, reward_id: UUID) -> Reward:
    reward = db.scalar(
        select(Reward)
        .options(selectinload(Reward.history))
        .where(Reward.id == reward_id)
    )
    if reward is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reward not found")
    return reward


def list_rewards(
    db: Session,
    *,
    skip: int,
    limit: int,
    customer_id: UUID | None = None,
    status_filter: str | None = None,
    loyalty_rule_id: UUID | None = None,
) -> tuple[list[Reward], int]:
    filters = []
    if customer_id is not None:
        filters.append(Reward.customer_id == customer_id)
    if status_filter is not None:
        filters.append(Reward.status == status_filter)
    if loyalty_rule_id is not None:
        filters.append(Reward.loyalty_rule_id == loyalty_rule_id)

    count_query = select(func.count()).select_from(Reward)
    list_query = select(Reward).order_by(Reward.earned_date.desc())
    if filters:
        count_query = count_query.where(*filters)
        list_query = list_query.where(*filters)

    total = db.scalar(count_query) or 0
    rewards = db.scalars(list_query.offset(skip).limit(limit)).all()
    return list(rewards), total


def redeem_reward(db: Session, reward_id: UUID, staff: Staff, body: RewardRedeem) -> Reward:
    reward = _get_reward(db, reward_id)

    if reward.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot redeem reward with status '{reward.status}'",
        )
    if reward.expiry_date < date.today():
        reward.status = "expired"
        db.add(
            RewardHistory(
                reward_id=reward.id,
                action="expired",
                staff_id=staff.id,
                remarks="Auto-expired on redeem attempt",
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reward has expired",
        )

    now = datetime.now(timezone.utc)
    reward.status = "redeemed"
    reward.redeemed_at = now
    db.add(
        RewardHistory(
            reward_id=reward.id,
            action="redeemed",
            staff_id=staff.id,
            remarks=body.remarks,
        )
    )
    db.commit()
    db.refresh(reward)
    return reward


def void_reward(db: Session, reward_id: UUID, staff: Staff, body: RewardVoid) -> Reward:
    reward = _get_reward(db, reward_id)

    if reward.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot void reward with status '{reward.status}'",
        )

    reward.status = "void"
    db.add(
        RewardHistory(
            reward_id=reward.id,
            action="void",
            staff_id=staff.id,
            remarks=body.remarks,
        )
    )
    db.commit()
    db.refresh(reward)
    return reward


def expire_stale_rewards(db: Session) -> int:
    today = date.today()
    stale = db.scalars(
        select(Reward).where(Reward.status == "pending", Reward.expiry_date < today)
    ).all()

    for reward in stale:
        reward.status = "expired"
        db.add(
            RewardHistory(
                reward_id=reward.id,
                action="expired",
                remarks="Expired automatically",
            )
        )

    if stale:
        db.commit()
    return len(stale)
