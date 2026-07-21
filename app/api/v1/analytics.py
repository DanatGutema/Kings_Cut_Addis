from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func, select

from app.api.deps import CurrentStaff, DbSession
from app.models.customer import Customer
from app.models.reward import Reward
from app.models.service import Service
from app.models.visit import Visit
from app.models.visit_service import VisitService
from app.schemas.analytics import (
    DashboardMetrics,
    LoyaltyMetrics,
    RevenueByService,
    TopCustomer,
    VisitTrendPoint,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _day_start(d: date | None = None) -> datetime:
    day = d or date.today()
    return datetime.combine(day, datetime.min.time())


@router.get("/dashboard", response_model=DashboardMetrics)
def dashboard_metrics(db: DbSession, _: CurrentStaff) -> DashboardMetrics:
    today_start = _day_start()
    month_start = _day_start(date.today().replace(day=1))

    total_customers = db.scalar(select(func.count()).select_from(Customer)) or 0
    visits_today = (
        db.scalar(select(func.count()).select_from(Visit).where(Visit.visit_date >= today_start))
        or 0
    )
    active_rewards = (
        db.scalar(
            select(func.count()).select_from(Reward).where(Reward.status == "pending")
        )
        or 0
    )
    revenue_today = db.scalar(
        select(func.coalesce(func.sum(Visit.total_amount), 0)).where(Visit.visit_date >= today_start)
    )
    revenue_month = db.scalar(
        select(func.coalesce(func.sum(Visit.total_amount), 0)).where(
            Visit.visit_date >= month_start
        )
    )

    return DashboardMetrics(
        total_customers=total_customers,
        visits_today=visits_today,
        active_rewards=active_rewards,
        revenue_today=Decimal(revenue_today or 0),
        revenue_this_month=Decimal(revenue_month or 0),
    )


@router.get("/visits/trend", response_model=list[VisitTrendPoint])
def visit_trend(
    db: DbSession,
    _: CurrentStaff,
    days: int = Query(30, ge=7, le=365),
) -> list[VisitTrendPoint]:
    start = _day_start(date.today() - timedelta(days=days - 1))
    rows = db.execute(
        select(
            func.date(Visit.visit_date).label("period"),
            func.count().label("visit_count"),
        )
        .where(Visit.visit_date >= start)
        .group_by(func.date(Visit.visit_date))
        .order_by(func.date(Visit.visit_date))
    ).all()

    by_day = {row.period: row.visit_count for row in rows}
    points: list[VisitTrendPoint] = []
    for i in range(days):
        d = date.today() - timedelta(days=days - 1 - i)
        points.append(VisitTrendPoint(period=d, visit_count=int(by_day.get(d, 0))))
    return points


@router.get("/revenue/by-service", response_model=list[RevenueByService])
def revenue_by_service(db: DbSession, _: CurrentStaff) -> list[RevenueByService]:
    rows = db.execute(
        select(
            Service.name,
            func.coalesce(func.sum(VisitService.subtotal), 0).label("total_revenue"),
            func.count(VisitService.id).label("visit_count"),
        )
        .join(Service, Service.id == VisitService.service_id)
        .group_by(Service.name)
        .order_by(func.sum(VisitService.subtotal).desc())
    ).all()
    return [
        RevenueByService(
            service_name=row.name,
            total_revenue=Decimal(row.total_revenue or 0),
            visit_count=int(row.visit_count or 0),
        )
        for row in rows
    ]


@router.get("/customers/top", response_model=list[TopCustomer])
def top_customers(
    db: DbSession,
    _: CurrentStaff,
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("spending", pattern="^(spending|visits)$"),
) -> list[TopCustomer]:
    order = Customer.total_spending.desc() if sort_by == "spending" else Customer.total_visits.desc()
    customers = db.scalars(select(Customer).order_by(order).limit(limit)).all()
    return [
        TopCustomer(
            customer_id=str(c.id),
            first_name=c.first_name,
            last_name=c.last_name,
            total_visits=c.total_visits,
            total_spending=Decimal(c.total_spending or 0),
        )
        for c in customers
    ]


@router.get("/loyalty", response_model=LoyaltyMetrics)
def loyalty_metrics(db: DbSession, _: CurrentStaff) -> LoyaltyMetrics:
    earned = db.scalar(select(func.count()).select_from(Reward)) or 0
    redeemed = (
        db.scalar(select(func.count()).select_from(Reward).where(Reward.status == "redeemed"))
        or 0
    )
    expired = (
        db.scalar(select(func.count()).select_from(Reward).where(Reward.status == "expired"))
        or 0
    )
    denom = earned or 1
    return LoyaltyMetrics(
        rewards_earned=earned,
        rewards_redeemed=redeemed,
        rewards_expired=expired,
        earn_rate=1.0 if earned else 0.0,
        redemption_rate=round(redeemed / denom, 4),
        expiry_rate=round(expired / denom, 4),
    )


@router.get("/export/xlsx")
def export_xlsx(db: DbSession, _: CurrentStaff) -> StreamingResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = "Customers"
    ws.append(["ID", "First Name", "Last Name", "Phone", "Visits", "Spending", "Status"])
    for c in db.scalars(select(Customer).order_by(Customer.created_at.desc())).all():
        ws.append(
            [
                str(c.id),
                c.first_name,
                c.last_name or "",
                c.phone_number,
                c.total_visits,
                float(c.total_spending or 0),
                c.loyalty_status,
            ]
        )

    visits_sheet = wb.create_sheet("Visits")
    visits_sheet.append(["ID", "Customer ID", "Staff ID", "Date", "Amount", "Notes"])
    for v in db.scalars(select(Visit).order_by(Visit.visit_date.desc()).limit(2000)).all():
        visits_sheet.append(
            [
                str(v.id),
                str(v.customer_id),
                str(v.staff_id),
                v.visit_date.isoformat() if v.visit_date else "",
                float(v.total_amount or 0),
                v.notes or "",
            ]
        )

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=kings_cut_report.xlsx"},
    )


@router.get("/export/pdf")
def export_pdf(db: DbSession, current_staff: CurrentStaff) -> StreamingResponse:
    metrics = dashboard_metrics(db, current_staff)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    _width, height = A4
    y = height - 50
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, "Kings Cut Addis — Summary Report")
    y -= 30
    pdf.setFont("Helvetica", 11)
    lines = [
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Total customers: {metrics.total_customers}",
        f"Visits today: {metrics.visits_today}",
        f"Active rewards: {metrics.active_rewards}",
        f"Revenue today: {metrics.revenue_today} ETB",
        f"Revenue this month: {metrics.revenue_this_month} ETB",
    ]
    for line in lines:
        pdf.drawString(40, y, line)
        y -= 18
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=kings_cut_summary.pdf"},
    )
