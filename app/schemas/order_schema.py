from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.models.order import OrderStatus, PaymentStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.customer_schema import CustomerBasicResponse
from app.schemas.delivery_partner_schema import DeliveryPartnerBasicResponse
from app.schemas.restaurant_schema import RestaurantBasicResponse


class OrderCreate(AppBaseSchema):
    address_id: int
    coupon_code: str | None = Field(None, max_length=50)


class OrderItemResponse(AppBaseSchema):
    id: int
    menu_item_id: int
    item_name: str
    price_at_order: Decimal
    quantity: int


class OrderStatusUpdate(AppBaseSchema):
    order_status: OrderStatus
    notes: str | None = Field(None, max_length=300)


class OrderBasicResponse(AppBaseSchema):
    id: int
    order_number: str
    order_status: OrderStatus
    payment_status: PaymentStatus


class OrderResponse(OrderBasicResponse):
    customer: CustomerBasicResponse
    restaurant: RestaurantBasicResponse
    delivery_partner: DeliveryPartnerBasicResponse | None
    items: list[OrderItemResponse]
    subtotal: Decimal
    delivery_fee: Decimal
    discount: Decimal
    tax: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime


class OrderMessageResponse(AppBaseSchema):
    message: str
    data: OrderResponse


class OrderPaginationResponse(AppBaseSchema):
    message: str
    data: list[OrderResponse]
    pagination: PaginationResponse