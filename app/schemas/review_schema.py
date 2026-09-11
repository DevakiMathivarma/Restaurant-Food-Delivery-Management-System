from datetime import datetime

from pydantic import Field

from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.customer_schema import CustomerBasicResponse


class ReviewCreate(AppBaseSchema):
    restaurant_rating: int = Field(..., ge=1, le=5)
    food_review_text: str | None = Field(None, max_length=2000)
    delivery_rating: int | None = Field(None, ge=1, le=5)
    delivery_review_text: str | None = Field(None, max_length=2000)


class ReviewUpdate(AppBaseSchema):
    restaurant_rating: int | None = Field(None, ge=1, le=5)
    food_review_text: str | None = Field(None, max_length=2000)
    delivery_rating: int | None = Field(None, ge=1, le=5)
    delivery_review_text: str | None = Field(None, max_length=2000)


class ReviewResponse(AppBaseSchema):
    id: int
    order_id: int
    customer: CustomerBasicResponse
    restaurant_rating: int
    food_review_text: str | None
    delivery_rating: int | None
    delivery_review_text: str | None
    created_at: datetime
    updated_at: datetime


class ReviewMessageResponse(AppBaseSchema):
    message: str
    data: ReviewResponse


class ReviewPaginationResponse(AppBaseSchema):
    message: str
    data: list[ReviewResponse]
    pagination: PaginationResponse