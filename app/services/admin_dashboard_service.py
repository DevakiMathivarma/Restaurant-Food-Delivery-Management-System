import io
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session, joinedload

from app.models.delivery_partner import AvailabilityStatus, DeliveryPartner
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.refund import Refund
from app.models.restaurant import Restaurant
from app.models.customer import Customer
from app.schemas.dashboard_schema import (
    AdminDashboardSummary, TopRestaurantEntry, TopFoodItemEntry, DailyOrdersEntry, MonthlyRevenueEntry
)
from app.utils.logger import logger

TOP_LIMIT = 10
DAILY_ORDERS_WINDOW_DAYS = 30


def get_admin_dashboard(db: Session) -> dict:

    logger.info("Generating admin dashboard.")

    total_restaurants = db.query(Restaurant).count()
    total_customers = db.query(Customer).count()

    delivered_orders = db.query(Order).filter(Order.order_status == OrderStatus.DELIVERED).all()
    all_orders_count = db.query(Order).count()
    cancelled_count = db.query(Order).filter(Order.order_status == OrderStatus.CANCELLED).count()

    total_revenue = sum((o.total_amount for o in delivered_orders), Decimal("0.00"))

    refund_amounts = db.query(Refund.refund_amount).all()
    total_refunds = sum((row[0] for row in refund_amounts), Decimal("0.00"))

    active_delivery_partners = db.query(DeliveryPartner).filter(DeliveryPartner.availability_status != AvailabilityStatus.OFFLINE).count()

    cuisine_counts = defaultdict(int)

    for restaurant_id, in db.query(Order.restaurant_id).filter(Order.order_status == OrderStatus.DELIVERED).all():

        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

        if restaurant:

            cuisine_counts[restaurant.cuisine_type] += 1

    most_popular_cuisine = max(cuisine_counts, key=cuisine_counts.get) if cuisine_counts else None

    cancellation_rate = round((cancelled_count / all_orders_count) * 100, 2) if all_orders_count > 0 else 0.0

    summary = AdminDashboardSummary(
        total_restaurants=total_restaurants,
        total_customers=total_customers,
        total_orders=all_orders_count,
        total_revenue=total_revenue,
        total_refunds=total_refunds,
        active_delivery_partners=active_delivery_partners,
        most_popular_cuisine=most_popular_cuisine,
        cancellation_rate=cancellation_rate
    )

    return {"message": "Admin dashboard generated successfully.", "data": summary}


def get_top_restaurants_report(db: Session) -> dict:

    restaurants = db.query(Restaurant).all()

    delivered_orders = db.query(Order).filter(Order.order_status == OrderStatus.DELIVERED).all()

    stats = defaultdict(lambda: {"count": 0, "revenue": Decimal("0.00")})

    for order in delivered_orders:

        stats[order.restaurant_id]["count"] += 1
        stats[order.restaurant_id]["revenue"] += order.total_amount

    ranked = sorted(restaurants, key=lambda r: stats[r.id]["revenue"], reverse=True)[:TOP_LIMIT]

    data = [
        TopRestaurantEntry(restaurant_id=r.id, restaurant_name=r.restaurant_name, total_orders=stats[r.id]["count"], total_revenue=stats[r.id]["revenue"])
        for r in ranked
    ]

    return {"message": "Top restaurants report generated successfully.", "data": data}


def get_top_food_items_report(db: Session) -> dict:

    order_items = db.query(OrderItem).all()

    counts = defaultdict(int)
    names = {}

    for item in order_items:

        counts[item.menu_item_id] += item.quantity
        names[item.menu_item_id] = item.item_name

    top_item_ids = sorted(counts.keys(), key=lambda mid: counts[mid], reverse=True)[:TOP_LIMIT]

    data = [TopFoodItemEntry(menu_item_id=mid, item_name=names[mid], total_ordered=counts[mid]) for mid in top_item_ids]

    return {"message": "Top food items report generated successfully.", "data": data}


def get_daily_orders_report(db: Session) -> dict:

    cutoff = datetime.combine(date.today() - timedelta(days=DAILY_ORDERS_WINDOW_DAYS), datetime.min.time())

    orders = db.query(Order).filter(Order.created_at >= cutoff).all()

    daily_counts = defaultdict(int)

    for order in orders:

        day_key = order.created_at.strftime("%Y-%m-%d")
        daily_counts[day_key] += 1

    data = [DailyOrdersEntry(date=day, order_count=count) for day, count in sorted(daily_counts.items())]

    return {"message": "Daily orders report generated successfully.", "data": data}


def get_monthly_revenue_report(db: Session) -> dict:

    delivered_orders = db.query(Order).filter(Order.order_status == OrderStatus.DELIVERED).all()

    monthly = defaultdict(lambda: Decimal("0.00"))

    for order in delivered_orders:

        month_key = order.created_at.strftime("%Y-%m")
        monthly[month_key] += order.total_amount

    data = [MonthlyRevenueEntry(month=month, total_revenue=total) for month, total in sorted(monthly.items())]

    return {"message": "Monthly revenue report generated successfully.", "data": data}


def _build_excel_response(filename: str, headers: list[str], rows: list[list]) -> StreamingResponse:

    workbook = Workbook()

    sheet = workbook.active

    sheet.append(headers)

    for cell in sheet[1]:

        cell.font = Font(bold=True)

    for row in rows:

        sheet.append(row)

    buffer = io.BytesIO()

    workbook.save(buffer)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def export_top_restaurants_excel(db: Session) -> StreamingResponse:

    report = get_top_restaurants_report(db)

    rows = [[entry.restaurant_id, entry.restaurant_name, entry.total_orders, float(entry.total_revenue)] for entry in report["data"]]

    return _build_excel_response("top_restaurants.xlsx", ["Restaurant ID", "Restaurant Name", "Total Orders", "Total Revenue"], rows)


def export_monthly_revenue_excel(db: Session) -> StreamingResponse:

    report = get_monthly_revenue_report(db)

    rows = [[entry.month, float(entry.total_revenue)] for entry in report["data"]]

    return _build_excel_response("monthly_revenue.xlsx", ["Month", "Total Revenue"], rows)