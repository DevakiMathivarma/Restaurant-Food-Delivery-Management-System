from datetime import datetime, time
from decimal import Decimal

from pydantic import Field, model_validator

from app.models.restaurant import RestaurantStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.user_schema import UserBasicResponse


class RestaurantCreate(AppBaseSchema):
    restaurant_name: str = Field(..., min_length=2, max_length=200)
    address: str = Field(..., min_length=5, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    cuisine_type: str = Field(..., min_length=2, max_length=100)
    opening_time: time
    closing_time: time
    delivery_radius: Decimal = Field(..., gt=0)

    # opening and closing times must be validated 
    @model_validator(mode="after")
    def check_hours(self):
        if self.closing_time <= self.opening_time:
            raise ValueError("closing_time must be after opening_time.")
        return self


class RestaurantUpdate(AppBaseSchema):
    restaurant_name: str | None = Field(None, min_length=2, max_length=200)
    address: str | None = Field(None, min_length=5, max_length=300)
    phone: str | None = Field(None, min_length=10, max_length=15)
    cuisine_type: str | None = Field(None, min_length=2, max_length=100)
    opening_time: time | None = None
    closing_time: time | None = None
    delivery_radius: Decimal | None = Field(None, gt=0)
    status: RestaurantStatus | None = None


class RestaurantBasicResponse(AppBaseSchema):
    id: int
    restaurant_name: str
    cuisine_type: str
    status: RestaurantStatus


class RestaurantResponse(RestaurantBasicResponse):
    address: str
    city: str
    phone: str
    opening_time: time
    closing_time: time
    delivery_radius: Decimal
    owner: UserBasicResponse
    created_at: datetime
    updated_at: datetime


class RestaurantMessageResponse(AppBaseSchema):
    message: str
    data: RestaurantResponse


class RestaurantPaginationResponse(AppBaseSchema):
    message: str
    data: list[RestaurantResponse]
    pagination: PaginationResponse