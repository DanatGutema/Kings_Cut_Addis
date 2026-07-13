from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

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
from app.schemas.auth import RefreshTokenRequest, StaffLogin, TokenResponse
from app.schemas.staff import StaffOut

router = APIRouter(prefix="/auth", tags=["auth"])


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


@router.post("/login", response_model=TokenResponse)
def staff_login(body: StaffLogin, db: DbSession, request: Request) -> TokenResponse:
    staff = db.scalar(select(Staff).where(Staff.email == body.email))
    if staff is None or not verify_password(body.password, staff.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return _issue_tokens(db, staff, request)


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    body: RefreshTokenRequest,
    db: DbSession,
    request: Request,
) -> TokenResponse:
    token_hash = hash_token(body.refresh_token)
    record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.staff_id.isnot(None),
        )
    )
    if record is None:
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    staff = db.get(Staff, record.staff_id)
    if staff is None or not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Staff account not found or inactive",
        )

    record.revoked = True
    record.revoked_at = now
    record.last_used_at = now
    return _issue_tokens(db, staff, request)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def staff_logout(body: RefreshTokenRequest, db: DbSession) -> None:
    token_hash = hash_token(body.refresh_token)
    record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
        )
    )
    if record is None:
        return

    now = datetime.now(timezone.utc)
    record.revoked = True
    record.revoked_at = now
    db.commit()


@router.get("/me", response_model=StaffOut)
def get_current_staff_profile(current_staff: CurrentStaff) -> Staff:
    return current_staff
