from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.customer import Customer
from app.models.service import Service
from app.models.staff import Staff
from app.models.visit import Visit
from app.models.visit_service import VisitService
from app.schemas.visit import VisitCreate, VisitUpdate


def _get_active_customer(db: Session, customer_id: UUID) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None or not customer.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


def _get_active_staff(db: Session, staff_id: UUID) -> Staff:
    staff = db.get(Staff, staff_id)
    if staff is None or not staff.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    return staff


def _build_line_items(db: Session, services: list) -> tuple[list[dict], Decimal]:
    if not services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one service is required",
        )

    line_items: list[dict] = []
    total = Decimal("0.00")

    for item in services:
        service = db.get(Service, item.service_id)
        if service is None or not service.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Service {item.service_id} not found or inactive",
            )
        unit_price = Decimal(service.price)
        subtotal = unit_price * item.quantity
        total += subtotal
        line_items.append(
            {
                "service_id": service.id,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            }
        )

    return line_items, total


def create_visit(db: Session, data: VisitCreate) -> Visit:
    customer = _get_active_customer(db, data.customer_id)
    _get_active_staff(db, data.staff_id)
    line_items, total_amount = _build_line_items(db, data.services)

    visit_date = data.visit_date or datetime.utcnow()
    visit = Visit(
        customer_id=data.customer_id,
        staff_id=data.staff_id,
        visit_date=visit_date,
        total_amount=total_amount,
        notes=data.notes,
    )
    db.add(visit)
    db.flush()

    for item in line_items:
        db.add(VisitService(visit_id=visit.id, **item))

    customer.total_visits += 1
    customer.total_spending = Decimal(customer.total_spending) + total_amount
    customer.last_visit_date = visit_date.date()

    from app.api.services.loyalty_engine import evaluate_customer_loyalty

    evaluate_customer_loyalty(db, customer.id)

    db.commit()
    db.refresh(visit)
    return get_visit(db, visit.id)


def get_visit(db: Session, visit_id: UUID) -> Visit:
    visit = db.scalar(
        select(Visit)
        .options(selectinload(Visit.visit_services))
        .where(Visit.id == visit_id)
    )
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return visit


def update_visit(db: Session, visit_id: UUID, data: VisitUpdate) -> Visit:
    visit = get_visit(db, visit_id)
    customer = _get_active_customer(db, visit.customer_id)

    if data.staff_id is not None:
        _get_active_staff(db, data.staff_id)
        visit.staff_id = data.staff_id

    if data.notes is not None:
        visit.notes = data.notes

    if data.visit_date is not None:
        visit.visit_date = data.visit_date
        customer.last_visit_date = data.visit_date.date()

    if data.total_amount is not None:
        old_total = Decimal(visit.total_amount)
        new_total = Decimal(data.total_amount)
        customer.total_spending = Decimal(customer.total_spending) - old_total + new_total
        visit.total_amount = new_total

    db.commit()
    db.refresh(visit)
    return visit


def list_visits(
    db: Session,
    *,
    skip: int,
    limit: int,
    customer_id: UUID | None = None,
    staff_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Visit], int]:
    filters = []
    if customer_id is not None:
        filters.append(Visit.customer_id == customer_id)
    if staff_id is not None:
        filters.append(Visit.staff_id == staff_id)
    if date_from is not None:
        filters.append(Visit.visit_date >= date_from)
    if date_to is not None:
        filters.append(Visit.visit_date <= date_to)

    count_query = select(func.count()).select_from(Visit)
    list_query = (
        select(Visit)
        .options(selectinload(Visit.visit_services))
        .order_by(Visit.visit_date.desc())
    )
    if filters:
        count_query = count_query.where(*filters)
        list_query = list_query.where(*filters)

    total = db.scalar(count_query) or 0
    visits = db.scalars(list_query.offset(skip).limit(limit)).all()
    return list(visits), total


def list_customer_visits(
    db: Session,
    customer_id: UUID,
    skip: int,
    limit: int,
) -> tuple[list[Visit], int]:
    return list_visits(db, skip=skip, limit=limit, customer_id=customer_id)
