from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import AdminStaff, CurrentStaff, DbSession
from app.models.loyalty_rule import LoyaltyRule
from app.schemas.loyalty_rule import LoyaltyRuleCreate, LoyaltyRuleOut, LoyaltyRuleUpdate
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/loyalty-rules", tags=["loyalty"])


@router.get("", response_model=PaginatedResponse[LoyaltyRuleOut])
def list_loyalty_rules(
    db: DbSession,
    _: CurrentStaff,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(False),
) -> PaginatedResponse[LoyaltyRuleOut]:
    query = select(LoyaltyRule)
    count_query = select(func.count()).select_from(LoyaltyRule)

    if active_only:
        query = query.where(LoyaltyRule.is_active.is_(True))
        count_query = count_query.where(LoyaltyRule.is_active.is_(True))

    total = db.scalar(count_query) or 0
    rules = db.scalars(query.order_by(LoyaltyRule.created_at.desc()).offset(skip).limit(limit)).all()

    return PaginatedResponse(
        items=[LoyaltyRuleOut.model_validate(r) for r in rules],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=LoyaltyRuleOut, status_code=status.HTTP_201_CREATED)
def create_loyalty_rule(
    body: LoyaltyRuleCreate,
    db: DbSession,
    _: AdminStaff,
) -> LoyaltyRule:
    rule = LoyaltyRule(**body.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/{rule_id}", response_model=LoyaltyRuleOut)
def get_loyalty_rule(
    rule_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> LoyaltyRule:
    rule = db.get(LoyaltyRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty rule not found")
    return rule


@router.patch("/{rule_id}", response_model=LoyaltyRuleOut)
def update_loyalty_rule(
    rule_id: UUID,
    body: LoyaltyRuleUpdate,
    db: DbSession,
    _: AdminStaff,
) -> LoyaltyRule:
    rule = db.get(LoyaltyRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty rule not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", response_model=LoyaltyRuleOut)
def deactivate_loyalty_rule(
    rule_id: UUID,
    db: DbSession,
    _: AdminStaff,
) -> LoyaltyRule:
    rule = db.get(LoyaltyRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty rule not found")

    rule.is_active = False
    db.commit()
    db.refresh(rule)
    return rule
