from datetime import datetime

from pydantic import Field

from app.schemas.common_schema import AppBaseSchema
from app.schemas.user_schema import UserBasicResponse


class OrderTrackingCreate(AppBaseSchema):
    status: str = Field(..., min_length=2, max_length=30)
    notes: str | None = Field(None, max_length=300)


class OrderTrackingResponse(AppBaseSchema):
    id: int
    order_id: int
    status: str
    notes: str | None
    updated_by: UserBasicResponse | None
    created_at: datetime


class OrderTrackingListResponse(AppBaseSchema):
    message: str
    data: list[OrderTrackingResponse]