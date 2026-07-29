from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.core.auth_cookies import ACCESS_COOKIE
from app.api.core.security import TOKEN_TYPE_ACCESS, decode_token
from app.database import get_db
from app.models.customer import Customer
from app.models.staff import Staff

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _access_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> str:
    if credentials and credentials.credentials:
        return credentials.credentials
    cookie_token = request.cookies.get(ACCESS_COOKIE)
    if cookie_token:
        return cookie_token
    raise _credentials_exception()


def get_current_staff(
    request: Request,
    db: DbSession,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
) -> Staff:
    token = _access_token_from_request(request, credentials)
    try:
        payload = decode_token(token)
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
    if getattr(staff, "approval_status", "approved") != "approved":
        raise _credentials_exception()
    return staff


def get_current_customer(
    request: Request,
    db: DbSession,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
) -> Customer:
    # Mini-app keeps Bearer tokens; cookies are for staff dashboard.
    token = _access_token_from_request(request, credentials)
    try:
        payload = decode_token(token)
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
