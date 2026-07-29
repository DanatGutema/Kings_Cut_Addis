from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import or_, select

from app.api.core.auth_cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from app.api.core.security import (
    create_access_token,
    create_refresh_token_value,
    get_refresh_token_expiry,
    hash_token,
    verify_password,
)
from app.api.deps import CurrentStaff, DbSession
from app.models.refresh_token import RefreshToken
from app.models.staff import Staff
from app.schemas.auth import StaffLogin, TokenResponse
from app.schemas.staff import StaffOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _ensure_staff_can_authenticate(staff: Staff) -> None:
    status_value = getattr(staff, "approval_status", "approved") or "approved"
    if status_value == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your registration is pending admin approval",
        )
    if status_value == "rejected":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your registration was rejected. Contact the shop owner.",
        )
    if not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )


def _issue_tokens(db: DbSession, staff: Staff, request: Request) -> TokenResponse:
    access_token = create_access_token(subject=staff.id, role=staff.role)
    refresh_value = create_refresh_token_value()

    db.add(
        RefreshToken(
            staff_id=staff.id,
            token_hash=hash_token(refresh_value),
            device_name=request.headers.get("User-Agent"),
            device_type="web",
            ip_address=request.client.host if request.client else None,
            expires_at=get_refresh_token_expiry(),
        )
    )
    staff.last_login = datetime.now(timezone.utc)
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_value)


@router.post("/login", response_model=StaffOut)
def staff_login(
    body: StaffLogin,
    db: DbSession,
    request: Request,
    response: Response,
) -> Staff:
    try:
        identifier = body.identifier()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    staff = db.scalar(
        select(Staff).where(
            or_(Staff.email == identifier, Staff.phone_number == identifier)
        )
    )
    if staff is None or not verify_password(body.password, staff.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/phone or password",
        )
    _ensure_staff_can_authenticate(staff)
    tokens = _issue_tokens(db, staff, request)
    set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )
    db.refresh(staff)
    return staff


@router.post("/refresh", response_model=StaffOut)
def refresh_access_token(
    db: DbSession,
    request: Request,
    response: Response,
) -> Staff:
    refresh_value = request.cookies.get(REFRESH_COOKIE)
    if not refresh_value:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    token_hash = hash_token(refresh_value)
    record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.staff_id.isnot(None),
        )
    )
    if record is None:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    now = datetime.now(timezone.utc)
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        record.revoked = True
        record.revoked_at = now
        db.commit()
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    staff = db.get(Staff, record.staff_id)
    if staff is None:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Staff account not found or inactive",
        )
    try:
        _ensure_staff_can_authenticate(staff)
    except HTTPException:
        clear_auth_cookies(response)
        raise

    record.revoked = True
    record.revoked_at = now
    record.last_used_at = now
    tokens = _issue_tokens(db, staff, request)
    set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )
    db.refresh(staff)
    return staff


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def staff_logout(
    request: Request,
    response: Response,
    db: DbSession,
) -> None:
    refresh_value = request.cookies.get(REFRESH_COOKIE)
    if refresh_value:
        token_hash = hash_token(refresh_value)
        record = db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
            )
        )
        if record is not None:
            now = datetime.now(timezone.utc)
            record.revoked = True
            record.revoked_at = now
            db.commit()

    clear_auth_cookies(response)


@router.get("/me", response_model=StaffOut)
def get_current_staff_profile(current_staff: CurrentStaff) -> Staff:
    return current_staff
