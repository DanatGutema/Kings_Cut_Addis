from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_customers: int
    visits_today: int
    total_visits: int
    active_rewards: int
    revenue_today: Decimal
    revenue_this_month: Decimal


class VisitTrendPoint(BaseModel):
    period: date
    visit_count: int


class RevenueByService(BaseModel):
    service_name: str
    total_revenue: Decimal
    visit_count: int


class TopCustomer(BaseModel):
    customer_id: str
    first_name: str
    last_name: str | None
    total_visits: int
    total_spending: Decimal


class LoyaltyMetrics(BaseModel):
    rewards_earned: int
    rewards_redeemed: int
    rewards_expired: int
    earn_rate: float
    redemption_rate: float
    expiry_rate: float
