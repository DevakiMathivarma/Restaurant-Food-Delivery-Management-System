from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.models.refund import RefundStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.user_schema import UserBasicResponse


class RefundCreate(AppBaseSchema):
    refund_amount: Decimal = Field(..., gt=0)
    reason: str | None = Field(None, max_length=300)


class RefundResponse(AppBaseSchema):
    id: int
    order_id: int
    refund_amount: Decimal
    reason: str | None
    status: RefundStatus
    refund_date: datetime | None
    processed_by: UserBasicResponse | None
    created_at: datetime


class RefundMessageResponse(AppBaseSchema):
    message: str
    data: RefundResponse


class RefundPaginationResponse(AppBaseSchema):
    message: str
    data: list[RefundResponse]
    pagination: PaginationResponse