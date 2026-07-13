from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.loyalty_rule import LoyaltyRule
from app.models.reward import Reward
from app.models.reward_history import RewardHistory
from app.models.visit import Visit


def _period_start(
    db: Session,
    customer_id: UUID,
    rule_id: UUID,
    evaluation_period_days: int | None,
) -> datetime:
    last_reward = db.scalar(
        select(Reward)
        .where(
            Reward.customer_id == customer_id,
            Reward.loyalty_rule_id == rule_id,
        )
        .order_by(Reward.earned_date.desc())
        .limit(1)
    )

    today = date.today()
    if evaluation_period_days:
        window_start = datetime.combine(
            today - timedelta(days=evaluation_period_days),
            datetime.min.time(),
        )
        if last_reward:
            last_start = datetime.combine(last_reward.earned_date, datetime.min.time())
            return max(last_start, window_start)
        return window_start

    if last_reward:
        return datetime.combine(last_reward.earned_date, datetime.min.time())
    return datetime.min


def _count_visits_since(db: Session, customer_id: UUID, since: datetime) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Visit)
            .where(Visit.customer_id == customer_id, Visit.visit_date >= since)
        )
        or 0
    )


def _sum_spending_since(db: Session, customer_id: UUID, since: datetime) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(Visit.total_amount), 0))
        .select_from(Visit)
        .where(Visit.customer_id == customer_id, Visit.visit_date >= since)
    )
    return Decimal(total or 0)


def _issue_reward(db: Session, customer_id: UUID, rule: LoyaltyRule) -> Reward:
    today = date.today()
    reward = Reward(
        customer_id=customer_id,
        loyalty_rule_id=rule.id,
        reward_type=rule.reward_type,
        reward_percentage=rule.reward_percentage,
        reward_amount=rule.reward_amount,
        earned_date=today,
        expiry_date=today + timedelta(days=rule.expiry_days),
        status="pending",
    )
    db.add(reward)
    db.flush()
    db.add(
        RewardHistory(
            reward_id=reward.id,
            action="earned",
            remarks=f"Earned via rule: {rule.rule_name}",
        )
    )
    return reward


def _rule_qualifies(
    db: Session,
    customer_id: UUID,
    rule: LoyaltyRule,
) -> bool:
    since = _period_start(db, customer_id, rule.id, rule.evaluation_period_days)

    if rule.rule_type == "visit":
        count = _count_visits_since(db, customer_id, since)
        return rule.visit_threshold is not None and count >= rule.visit_threshold

    if rule.rule_type == "spending":
        total = _sum_spending_since(db, customer_id, since)
        return rule.spending_threshold is not None and total >= rule.spending_threshold

    return False


def evaluate_customer_loyalty(db: Session, customer_id: UUID) -> list[Reward]:
    """Evaluate active rules after a visit and issue any newly earned rewards."""
    rules = db.scalars(
        select(LoyaltyRule).where(LoyaltyRule.is_active.is_(True))
    ).all()

    new_rewards: list[Reward] = []
    for rule in rules:
        if _rule_qualifies(db, customer_id, rule):
            new_rewards.append(_issue_reward(db, customer_id, rule))

    if new_rewards:
        db.flush()
    return new_rewards


def get_rule_progress(
    db: Session,
    customer_id: UUID,
    rule: LoyaltyRule,
) -> dict:
    since = _period_start(db, customer_id, rule.id, rule.evaluation_period_days)
    visit_count = _count_visits_since(db, customer_id, since)
    spending = _sum_spending_since(db, customer_id, since)

    pending = (
        db.scalar(
            select(func.count())
            .select_from(Reward)
            .where(
                Reward.customer_id == customer_id,
                Reward.loyalty_rule_id == rule.id,
                Reward.status == "pending",
            )
        )
        or 0
    )

    visits_remaining = None
    spending_remaining = None

    if rule.rule_type == "visit" and rule.visit_threshold:
        visits_remaining = max(rule.visit_threshold - visit_count, 0)
    if rule.rule_type == "spending" and rule.spending_threshold is not None:
        spending_remaining = max(Decimal(rule.spending_threshold) - spending, Decimal("0"))

    return {
        "rule_id": rule.id,
        "rule_name": rule.rule_name,
        "rule_type": rule.rule_type,
        "visit_threshold": rule.visit_threshold,
        "spending_threshold": rule.spending_threshold,
        "evaluation_period_days": rule.evaluation_period_days,
        "current_visits": visit_count,
        "current_spending": spending,
        "visits_remaining": visits_remaining,
        "spending_remaining": spending_remaining,
        "pending_rewards": pending,
    }
