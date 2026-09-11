from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common_schema import AppBaseSchema, PaginationResponse


class MenuItemCreate(AppBaseSchema):
    restaurant_id: int
    category: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)
    price: Decimal = Field(..., gt=0)
    preparation_time: int | None = Field(None, gt=0)
    vegetarian: bool = False
    spicy_level: int = Field(0, ge=0, le=5)


class MenuItemUpdate(AppBaseSchema):
    category: str | None = Field(None, min_length=2, max_length=100)
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)
    price: Decimal | None = Field(None, gt=0)
    preparation_time: int | None = Field(None, gt=0)
    availability: bool | None = None
    vegetarian: bool | None = None
    spicy_level: int | None = Field(None, ge=0, le=5)


class MenuItemBasicResponse(AppBaseSchema):
    id: int
    name: str
    price: Decimal
    availability: bool


class MenuItemResponse(MenuItemBasicResponse):
    restaurant_id: int
    category: str
    description: str | None
    preparation_time: int | None
    vegetarian: bool
    spicy_level: int
    created_at: datetime
    updated_at: datetime


class MenuItemMessageResponse(AppBaseSchema):
    message: str
    data: MenuItemResponse


class MenuItemPaginationResponse(AppBaseSchema):
    message: str
    data: list[MenuItemResponse]
    pagination: PaginationResponse