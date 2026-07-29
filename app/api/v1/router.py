from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    appointments,
    auth,
    barbers,
    checkin,
    customer_visits,
    customers,
    loyalty_rules,
    mini_app,
    promotions,
    rewards,
    services,
    visits,
    staff
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(customer_visits.router, prefix="/customers")
api_router.include_router(services.router)
api_router.include_router(visits.router)
api_router.include_router(appointments.router)
api_router.include_router(checkin.router)
api_router.include_router(loyalty_rules.router)
api_router.include_router(rewards.router)
api_router.include_router(rewards.loyalty_router)
api_router.include_router(promotions.router)
api_router.include_router(mini_app.router)
api_router.include_router(analytics.router)
api_router.include_router(staff.router)
api_router.include_router(barbers.router)
