from fastapi import APIRouter

from app.api.deps import CurrentStaff, DbSession
from app.api.services import checkin as checkin_service
from app.schemas.checkin import CheckInResponse, PhoneCheckInRequest, QrCheckInRequest

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("/qr", response_model=CheckInResponse)
def checkin_qr(
    body: QrCheckInRequest,
    db: DbSession,
    _: CurrentStaff,
) -> CheckInResponse:
    return checkin_service.checkin_by_qr(db, body.qr_token, body.staff_id)


@router.post("/phone", response_model=CheckInResponse)
def checkin_phone(
    body: PhoneCheckInRequest,
    db: DbSession,
    _: CurrentStaff,
) -> CheckInResponse:
    return checkin_service.checkin_by_phone(
        db,
        body.phone_number,
        body.staff_id,
        first_name=body.first_name,
        last_name=body.last_name,
    )
