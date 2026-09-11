from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin
from app.database import get_db
from app.schemas.dashboard_schema import AdminDashboardResponse, TopRestaurantsResponse, TopFoodItemsResponse, DailyOrdersResponse, MonthlyRevenueResponse
from app.services.admin_dashboard_service import (
    get_admin_dashboard, get_top_restaurants_report, get_top_food_items_report, get_daily_orders_report, get_monthly_revenue_report,
    export_top_restaurants_excel, export_monthly_revenue_excel
)

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["Admin Analytics"], dependencies=[Depends(require_admin)])


@router.get("/summary", response_model=AdminDashboardResponse)
def admin_dashboard_summary(db: Session = Depends(get_db)):
    return get_admin_dashboard(db)


@router.get("/top-restaurants", response_model=TopRestaurantsResponse)
def top_restaurants(db: Session = Depends(get_db)):
    return get_top_restaurants_report(db)


@router.get("/top-food-items", response_model=TopFoodItemsResponse)
def top_food_items(db: Session = Depends(get_db)):
    return get_top_food_items_report(db)


@router.get("/daily-orders", response_model=DailyOrdersResponse)
def daily_orders(db: Session = Depends(get_db)):
    return get_daily_orders_report(db)


@router.get("/monthly-revenue", response_model=MonthlyRevenueResponse)
def monthly_revenue(db: Session = Depends(get_db)):
    return get_monthly_revenue_report(db)


@router.get("/top-restaurants/export")
def export_top_restaurants(db: Session = Depends(get_db)):
    return export_top_restaurants_excel(db)


@router.get("/monthly-revenue/export")
def export_monthly_revenue(db: Session = Depends(get_db)):
    return export_monthly_revenue_excel(db)