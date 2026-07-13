from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.staff import Staff
from app.schemas.checkin import CheckInResponse


def _get_active_staff(db: Session, staff_id: UUID) -> Staff:
    staff = db.get(Staff, staff_id)
    if staff is None or not staff.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    return staff


def _to_checkin_response(customer: Customer, *, is_new: bool) -> CheckInResponse:
    return CheckInResponse(
        customer_id=customer.id,
        first_name=customer.first_name,
        last_name=customer.last_name,
        phone_number=customer.phone_number,
        total_visits=customer.total_visits,
        total_spending=float(customer.total_spending),
        loyalty_status=customer.loyalty_status,
        is_new_customer=is_new,
    )


def checkin_by_qr(db: Session, qr_token: UUID, staff_id: UUID) -> CheckInResponse:
    _get_active_staff(db, staff_id)
    customer = db.scalar(
        select(Customer).where(Customer.qr_token == qr_token, Customer.is_active.is_(True))
    )
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found for this QR code")
    return _to_checkin_response(customer, is_new=False)


def checkin_by_phone(
    db: Session,
    phone_number: str,
    staff_id: UUID,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
) -> CheckInResponse:
    _get_active_staff(db, staff_id)
    customer = db.scalar(select(Customer).where(Customer.phone_number == phone_number))

    if customer is not None:
        if not customer.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer account is deactivated")
        return _to_checkin_response(customer, is_new=False)

    if not first_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found. Provide first_name to register a new customer.",
        )

    customer = Customer(
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return _to_checkin_response(customer, is_new=True)
