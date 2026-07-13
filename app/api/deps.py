from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.core.security import TOKEN_TYPE_ACCESS, decode_token
from app.database import get_db
from app.models.customer import Customer
from app.models.staff import Staff

bearer_scheme = HTTPBearer(auto_error=True)

DbSession = Annotated[Session, Depends(get_db)]


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_staff(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> Staff:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != TOKEN_TYPE_ACCESS:
            raise _credentials_exception()
        if payload.get("role") not in ("admin", "staff"):
            raise _credentials_exception()
        staff_id = payload.get("sub")
        if staff_id is None:
            raise _credentials_exception()
    except JWTError:
        raise _credentials_exception() from None

    staff = db.get(Staff, UUID(staff_id))
    if staff is None or not staff.is_active:
        raise _credentials_exception()
    return staff


def get_current_customer(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> Customer:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != TOKEN_TYPE_ACCESS:
            raise _credentials_exception()
        if payload.get("role") != "customer":
            raise _credentials_exception()
        customer_id = payload.get("sub")
        if customer_id is None:
            raise _credentials_exception()
    except JWTError:
        raise _credentials_exception() from None

    customer = db.get(Customer, UUID(customer_id))
    if customer is None or not customer.is_active:
        raise _credentials_exception()
    return customer


def require_admin(
    current_staff: Annotated[Staff, Depends(get_current_staff)],
) -> Staff:
    if current_staff.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_staff


CurrentStaff = Annotated[Staff, Depends(get_current_staff)]
AdminStaff = Annotated[Staff, Depends(require_admin)]
CurrentCustomer = Annotated[Customer, Depends(get_current_customer)]
