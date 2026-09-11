from decimal import Decimal

from app.schemas.common_schema import AppBaseSchema


class RestaurantDashboardSummary(AppBaseSchema):
    todays_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    todays_revenue: Decimal
    monthly_revenue: Decimal
    most_ordered_food: str | None
    average_rating: float | None
    total_customers: int


class RestaurantDashboardResponse(AppBaseSchema):
    message: str
    data: RestaurantDashboardSummary


class AdminDashboardSummary(AppBaseSchema):
    total_restaurants: int
    total_customers: int
    total_orders: int
    total_revenue: Decimal
    total_refunds: Decimal
    active_delivery_partners: int
    most_popular_cuisine: str | None
    cancellation_rate: float


class AdminDashboardResponse(AppBaseSchema):
    message: str
    data: AdminDashboardSummary


class TopRestaurantEntry(AppBaseSchema):
    restaurant_id: int
    restaurant_name: str
    total_orders: int
    total_revenue: Decimal


class TopRestaurantsResponse(AppBaseSchema):
    message: str
    data: list[TopRestaurantEntry]


class TopFoodItemEntry(AppBaseSchema):
    menu_item_id: int
    item_name: str
    total_ordered: int


class TopFoodItemsResponse(AppBaseSchema):
    message: str
    data: list[TopFoodItemEntry]


class DailyOrdersEntry(AppBaseSchema):
    date: str
    order_count: int


class DailyOrdersResponse(AppBaseSchema):
    message: str
    data: list[DailyOrdersEntry]


class MonthlyRevenueEntry(AppBaseSchema):
    month: str
    total_revenue: Decimal


class MonthlyRevenueResponse(AppBaseSchema):
    message: str
    data: list[MonthlyRevenueEntry]