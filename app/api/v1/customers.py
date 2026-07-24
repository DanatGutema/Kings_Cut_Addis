from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import CurrentStaff, DbSession
from app.models.appointment import Appointment
from app.models.customer import Customer
from app.models.customer_session import CustomerSession
from app.models.promotion_recipient import PromotionRecipient
from app.models.refresh_token import RefreshToken
from app.models.reward import Reward
from app.models.service_order import ServiceOrder
from app.models.sms_log import SmsLog
from app.models.telegram_log import TelegramLog
from app.models.visit import Visit
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerSummary, CustomerUpdate
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=PaginatedResponse[CustomerSummary])
def list_customers(
    db: DbSession,
    _: CurrentStaff,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None, description="Search by name or phone"),
    loyalty_status: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> PaginatedResponse[CustomerSummary]:
    query = select(Customer)
    filters = []

    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Customer.first_name.ilike(term),
                Customer.last_name.ilike(term),
                Customer.phone_number.ilike(term),
            )
        )
    if loyalty_status is not None:
        filters.append(Customer.loyalty_status == loyalty_status)
    if is_active is not None:
        filters.append(Customer.is_active == is_active)

    count_query = select(func.count()).select_from(Customer)
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    total = db.scalar(count_query) or 0
    customers = db.scalars(
        query.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
    ).all()

    return PaginatedResponse(
        items=[CustomerSummary.model_validate(c) for c in customers],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CustomerCreate,
    db: DbSession,
    _: CurrentStaff,
) -> Customer:
    if db.scalar(select(Customer).where(Customer.phone_number == body.phone_number)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer with this phone number already exists",
        )
    if body.email and db.scalar(select(Customer).where(Customer.email == body.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer with this email already exists",
        )

    customer = Customer(**body.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: UUID,
    body: CustomerUpdate,
    db: DbSession,
    _: CurrentStaff,
) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    updates = body.model_dump(exclude_unset=True)
    if "email" in updates and updates["email"]:
        conflict = db.scalar(
            select(Customer).where(
                Customer.email == updates["email"],
                Customer.id != customer_id,
            )
        )
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    for field, value in updates.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer


@router.post("/{customer_id}/deactivate", response_model=CustomerOut)
def deactivate_customer(
    customer_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    customer.is_active = False
    db.commit()
    db.refresh(customer)
    return customer


@router.post("/{customer_id}/activate", response_model=CustomerOut)
def activate_customer(
    customer_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    customer.is_active = True
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: UUID,
    db: DbSession,
    _: CurrentStaff,
) -> None:
    """Permanently delete a deactivated customer only when they have no related business data."""
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    if customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deactivate the customer before deleting",
        )

    blockers: list[str] = []
    if db.query(Visit.id).filter(Visit.customer_id == customer.id).first():
        blockers.append("visits")
    if db.query(Reward.id).filter(Reward.customer_id == customer.id).first():
        blockers.append("rewards")
    if db.query(ServiceOrder.id).filter(ServiceOrder.customer_id == customer.id).first():
        blockers.append("service orders")
    if db.query(PromotionRecipient.id).filter(PromotionRecipient.customer_id == customer.id).first():
        blockers.append("promotions")
    if db.query(SmsLog.id).filter(SmsLog.customer_id == customer.id).first():
        blockers.append("SMS logs")
    if db.query(TelegramLog.id).filter(TelegramLog.customer_id == customer.id).first():
        blockers.append("Telegram logs")
    if db.query(Appointment.id).filter(Appointment.customer_id == customer.id).first():
        blockers.append("appointments")

    if blockers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Cannot delete this customer because they have related "
                f"{', '.join(blockers)}. Keep them deactivated instead."
            ),
        )

    db.query(CustomerSession).filter(CustomerSession.customer_id == customer.id).delete(
        synchronize_session=False
    )
    db.query(RefreshToken).filter(RefreshToken.customer_id == customer.id).delete(
        synchronize_session=False
    )

    db.delete(customer)
    db.commit()
    return None
