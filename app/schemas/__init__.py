from app.schemas.analytics import (
    DashboardMetrics,
    LoyaltyMetrics,
    RevenueByService,
    TopCustomer,
    VisitTrendPoint,
)
from app.schemas.auth import (
    OtpRequest,
    OtpVerify,
    RefreshTokenOut,
    RefreshTokenRequest,
    StaffLogin,
    TelegramAuthRequest,
    TokenResponse,
)
from app.schemas.checkin import CheckInResponse, PhoneCheckInRequest, QrCheckInRequest
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerSummary, CustomerUpdate
from app.schemas.loyalty_rule import LoyaltyRuleCreate, LoyaltyRuleOut, LoyaltyRuleUpdate
from app.schemas.promotion import (
    PromotionBroadcastRequest,
    PromotionBroadcastResult,
    PromotionCreate,
    PromotionOut,
    PromotionRecipientOut,
    PromotionUpdate,
)
from app.schemas.reward import RewardHistoryOut, RewardOut, RewardRedeem, RewardVoid
from app.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate
from app.schemas.service_order import (
    ServiceOrderCreate,
    ServiceOrderOut,
    ServiceOrderUpdate,
)
from app.schemas.staff import StaffCreate, StaffOut, StaffUpdate
from app.schemas.system import AuditLogOut, SmsLogOut, SystemSettingOut, TelegramLogOut
from app.schemas.visit import VisitCreate, VisitOut, VisitUpdate

__all__ = [
    "AuditLogOut",
    "CheckInResponse",
    "CustomerCreate",
    "CustomerOut",
    "CustomerSummary",
    "CustomerUpdate",
    "DashboardMetrics",
    "LoyaltyMetrics",
    "LoyaltyRuleCreate",
    "LoyaltyRuleOut",
    "LoyaltyRuleUpdate",
    "OtpRequest",
    "OtpVerify",
    "PhoneCheckInRequest",
    "PromotionBroadcastRequest",
    "PromotionBroadcastResult",
    "PromotionCreate",
    "PromotionOut",
    "PromotionRecipientOut",
    "PromotionUpdate",
    "QrCheckInRequest",
    "RefreshTokenOut",
    "RevenueByService",
    "RewardHistoryOut",
    "RewardOut",
    "RewardRedeem",
    "RewardVoid",
    "ServiceCreate",
    "ServiceOrderCreate",
    "ServiceOrderOut",
    "ServiceOrderUpdate",
    "ServiceOut",
    "ServiceUpdate",
    "SmsLogOut",
    "StaffCreate",
    "StaffLogin",
    "StaffOut",
    "StaffUpdate",
    "SystemSettingOut",
    "TelegramAuthRequest",
    "TelegramLogOut",
    "TokenResponse",
    "TopCustomer",
    "VisitCreate",
    "VisitOut",
    "VisitTrendPoint",
    "VisitUpdate",
]
