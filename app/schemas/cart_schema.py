from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common_schema import AppBaseSchema


class CartItemAdd(AppBaseSchema):
    menu_item_id: int
    quantity: int = Field(..., gt=0)


class CartItemUpdate(AppBaseSchema):
    quantity: int = Field(..., gt=0)


class CartItemResponse(AppBaseSchema):
    id: int
    menu_item_id: int
    menu_item_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class CartResponse(AppBaseSchema):
    id: int
    restaurant_id: int | None
    items: list[CartItemResponse]
    subtotal: Decimal


class CartMessageResponse(AppBaseSchema):
    message: str
    data: CartResponse