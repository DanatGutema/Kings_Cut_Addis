from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from app.database import get_db
from app.models.staff import Staff, StaffInvitation
from app.schemas.staff import StaffCreate, StaffOut, StaffUpdate
from app.api.deps import AdminStaff, DbSession
from app.api.core.security import hash_password
from app.api.services.email_service import send_staff_invitation
from pydantic import BaseModel


router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("/", response_model=list[StaffOut])
def list_staff(
    # db: Session = Depends(get_db),
    # current_staff: Staff = Depends(AdminStaff)
    db: DbSession,
    _: AdminStaff,
):
    """List all staff members (admin only)."""
    return db.query(Staff).filter(Staff.is_active == True).all()


@router.post("/", response_model=StaffOut, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    db: DbSession,
    _: AdminStaff,
):
    """Create a new staff member and send invitation email (admin only)."""
    # Check if email already exists
    existing = db.query(Staff).filter(Staff.email == staff_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create staff with a temporary password hash (will be replaced when they set password)
    new_staff = Staff(
        first_name=staff_data.first_name,
        last_name=staff_data.last_name,
        phone_number=staff_data.phone_number,
        email=staff_data.email,
        password_hash=hash_password("TEMPORARY_PASSWORD_TO_BE_REPLACED"),
        role=staff_data.role,
        is_active=True
    )
    db.add(new_staff)
    db.flush()
    
    # Create invitation token
    token = secrets.token_urlsafe(32)
    invitation = StaffInvitation(
        staff_id=new_staff.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24),
        used=False
    )
    db.add(invitation)
    db.commit()
    db.refresh(new_staff)
    
    # Send invitation email
    await send_staff_invitation(
        email=new_staff.email,
        first_name=new_staff.first_name,
        token=token
    )
    
    return new_staff


@router.put("/{staff_id}", response_model=StaffOut)
def update_staff(
    staff_id: str,
    staff_data: StaffUpdate,
    # db: Session = Depends(get_db),
    # current_staff: Staff = Depends(AdminStaff)
    db: DbSession,
    _: AdminStaff,
):
    """Update staff details (admin only)."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found"
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
            detail="Staff not found"
        )
    
    staff.is_active = False
    db.commit()
    return {"message": "Staff deactivated successfully"}



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
        StaffInvitation.expires_at > datetime.utcnow()
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    staff = db.query(Staff).filter(Staff.id == invitation.staff_id).first()
    staff.password_hash = hash_password(body.password)
    invitation.used = True
    
    db.commit()
    return {"message": "Password set successfully"}