from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
import secrets
from uuid import UUID

from sqlalchemy import or_

from app.models.staff import Staff, StaffInvitation
from app.models.visit import Visit
from app.models.reward_history import RewardHistory
from app.models.promotion import Promotion
from app.models.audit_log import AuditLog
from app.models.refresh_token import RefreshToken
from app.models.system_setting import SystemSetting
from app.schemas.staff import (
    StaffApproveRequest,
    StaffCreate,
    StaffOut,
    StaffRegisterResult,
    StaffSelfRegister,
    StaffUpdate,
)
from app.api.deps import AdminStaff, DbSession
from app.api.core.security import hash_password
from app.api.services.email_service import send_staff_invitation
from pydantic import BaseModel


router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("/", response_model=list[StaffOut])
def list_staff(
    db: DbSession,
    _: AdminStaff,
):
    """List all staff members (admin only)."""
    return db.query(Staff).order_by(Staff.created_at.desc()).all()


@router.post("/register", response_model=StaffRegisterResult, status_code=status.HTTP_201_CREATED)
def self_register_staff(
    body: StaffSelfRegister,
    db: DbSession,
):
    """Public self-registration. Account stays pending until an admin approves."""
    phone = body.phone_number.strip()
    email = str(body.email).strip().lower() if body.email else None

    existing_phone = db.query(Staff).filter(Staff.phone_number == phone).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )

    if email:
        existing_email = db.query(Staff).filter(Staff.email == email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    new_staff = Staff(
        first_name=body.first_name.strip(),
        last_name=(body.last_name or "").strip() or None,
        phone_number=phone,
        email=email,
        password_hash=hash_password(body.password),
        role="staff",
        approval_status="pending",
        is_active=False,
    )
    db.add(new_staff)
    db.commit()

    return StaffRegisterResult(
        message="Registration submitted. An admin must approve your account before you can sign in.",
        approval_status="pending",
    )


@router.post("/", response_model=StaffOut, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    db: DbSession,
    _: AdminStaff,
):
    """Create a new staff member and send invitation email (admin only)."""
    existing = db.query(Staff).filter(
        or_(Staff.email == staff_data.email, Staff.phone_number == staff_data.phone_number)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or phone already registered",
        )

    new_staff = Staff(
        first_name=staff_data.first_name,
        last_name=staff_data.last_name,
        phone_number=staff_data.phone_number,
        email=staff_data.email,
        password_hash=hash_password("TEMPORARY_PASSWORD_TO_BE_REPLACED"),
        role=staff_data.role,
        approval_status="approved",
        is_active=True,
    )
    db.add(new_staff)
    db.flush()

    token = secrets.token_urlsafe(32)
    invitation = StaffInvitation(
        staff_id=new_staff.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24),
        used=False,
    )
    db.add(invitation)
    db.commit()
    db.refresh(new_staff)

    try:
        await send_staff_invitation(
            email=new_staff.email,
            first_name=new_staff.first_name,
            token=token,
        )
    except Exception as e:
        print(f"Warning: Failed to send invitation email: {e}")

    return new_staff


@router.post("/{staff_id}/approve", response_model=StaffOut)
def approve_staff(
    staff_id: str,
    db: DbSession,
    _: AdminStaff,
    body: StaffApproveRequest = StaffApproveRequest(),
):
    """Approve a pending self-registration and assign their role (admin only)."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    staff.role = body.role
    staff.approval_status = "approved"
    staff.is_active = True
    db.commit()
    db.refresh(staff)
    return staff


@router.post("/{staff_id}/reject", response_model=StaffOut)
def reject_staff(
    staff_id: str,
    db: DbSession,
    _: AdminStaff,
):
    """Reject a pending self-registration (admin only)."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    staff.approval_status = "rejected"
    staff.is_active = False
    db.commit()
    db.refresh(staff)
    return staff


@router.put("/{staff_id}", response_model=StaffOut)
def update_staff(
    staff_id: str,
    staff_data: StaffUpdate,
    db: DbSession,
    _: AdminStaff,
):
    """Update staff details (admin only)."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found",
        )

    update_data = staff_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(staff, field, value)

    db.commit()
    db.refresh(staff)
    return staff


@router.post("/{staff_id}/deactivate")
def deactivate_staff(
    staff_id: str,
    db: DbSession,
    _: AdminStaff,
):
    """Deactivate a staff member (admin only)."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found",
        )

    staff.is_active = False
    db.commit()
    return {"message": "Staff deactivated successfully"}


@router.post("/{staff_id}/activate")
def activate_staff(
    staff_id: str,
    db: DbSession,
    _: AdminStaff,
):
    """Activate a staff member (admin only)."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found",
        )

    if staff.approval_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approve this registration before activating",
        )

    staff.is_active = True
    db.commit()
    return {"message": "Staff activated successfully"}


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    staff_id: str,
    db: DbSession,
    current_admin: AdminStaff,
):
    """Permanently delete a deactivated staff member with no related business data."""
    try:
        target_id = UUID(staff_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid staff id",
        ) from exc

    staff = db.query(Staff).filter(Staff.id == target_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found",
        )

    if staff.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    if staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deactivate the staff member before deleting",
        )

    if staff.role == "admin":
        other_admins = (
            db.query(Staff)
            .filter(
                Staff.role == "admin",
                Staff.id != staff.id,
                Staff.approval_status == "approved",
            )
            .count()
        )
        if other_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin account",
            )

    blockers: list[str] = []
    if db.query(Visit.id).filter(Visit.staff_id == staff.id).first():
        blockers.append("visits")
    if db.query(RewardHistory.id).filter(RewardHistory.staff_id == staff.id).first():
        blockers.append("reward history")
    if db.query(Promotion.id).filter(Promotion.created_by == staff.id).first():
        blockers.append("promotions")
    if db.query(AuditLog.id).filter(AuditLog.staff_id == staff.id).first():
        blockers.append("audit logs")

    if blockers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Cannot delete this staff member because they have related "
                f"{', '.join(blockers)}. Keep them deactivated instead."
            ),
        )

    db.query(SystemSetting).filter(SystemSetting.updated_by == staff.id).update(
        {SystemSetting.updated_by: None},
        synchronize_session=False,
    )
    db.query(StaffInvitation).filter(StaffInvitation.staff_id == staff.id).delete(
        synchronize_session=False
    )
    db.query(RefreshToken).filter(RefreshToken.staff_id == staff.id).delete(
        synchronize_session=False
    )

    db.delete(staff)
    db.commit()
    return None


class SetPasswordRequest(BaseModel):
    token: str
    password: str


@router.post("/set-password")
def set_staff_password(
    body: SetPasswordRequest,
    db: DbSession,
):
    """Set password using invitation token."""
    invitation = db.query(StaffInvitation).filter(
        StaffInvitation.token == body.token,
        StaffInvitation.used == False,
        StaffInvitation.expires_at > datetime.utcnow(),
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )

    staff = db.query(Staff).filter(Staff.id == invitation.staff_id).first()
    staff.password_hash = hash_password(body.password)
    staff.approval_status = "approved"
    staff.is_active = True
    invitation.used = True

    db.commit()
    return {"message": "Password set successfully"}
