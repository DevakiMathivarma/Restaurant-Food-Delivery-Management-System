from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.schemas.dashboard_schema import RestaurantDashboardSummary
from app.utils.logger import logger


def get_restaurant_dashboard(restaurant_id: int, current_user, db: Session) -> dict:

    logger.info(f"Generating dashboard for restaurant : {restaurant_id}")

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

    if current_user.role.value == "RESTAURANT_OWNER" and restaurant.owner_id != current_user.id:

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own restaurant's dashboard.")

    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    month_start = datetime.combine(today.replace(day=1), datetime.min.time())

    orders = db.query(Order).filter(Order.restaurant_id == restaurant_id).all()

    todays_orders = [o for o in orders if o.created_at.replace(tzinfo=None) >= today_start]
    pending_orders = [o for o in orders if o.order_status in (OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.READY)]
    completed_orders = [o for o in orders if o.order_status == OrderStatus.DELIVERED]
    cancelled_orders = [o for o in orders if o.order_status == OrderStatus.CANCELLED]

    todays_revenue = sum((o.total_amount for o in completed_orders if o.created_at.replace(tzinfo=None) >= today_start), Decimal("0.00"))
    monthly_revenue = sum((o.total_amount for o in completed_orders if o.created_at.replace(tzinfo=None) >= month_start), Decimal("0.00"))

    item_counts = defaultdict(int)

    order_ids = [o.id for o in orders]

    if order_ids:

        order_items = db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).all()

        for item in order_items:

            item_counts[item.item_name] += item.quantity

    most_ordered_food = max(item_counts, key=item_counts.get) if item_counts else None

    ratings = [r.restaurant_rating for r in db.query(Review).join(Order, Review.order_id == Order.id).filter(Order.restaurant_id == restaurant_id).all()]

    average_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    total_customers = len(set(o.customer_id for o in orders))

    summary = RestaurantDashboardSummary(
        todays_orders=len(todays_orders),
        pending_orders=len(pending_orders),
        completed_orders=len(completed_orders),
        cancelled_orders=len(cancelled_orders),
        todays_revenue=todays_revenue,
        monthly_revenue=monthly_revenue,
        most_ordered_food=most_ordered_food,
        average_rating=average_rating,
        total_customers=total_customers
    )

    return {"message": "Restaurant dashboard generated successfully.", "data": summary}