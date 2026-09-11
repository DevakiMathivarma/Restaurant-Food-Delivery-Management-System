from datetime import datetime
from decimal import Decimal

from pydantic import Field, model_validator

from app.models.coupon import CouponStatus, DiscountType
from app.schemas.common_schema import AppBaseSchema, PaginationResponse


class CouponCreate(AppBaseSchema):
    coupon_code: str = Field(..., min_length=3, max_length=50)
    discount_type: DiscountType
    discount_value: Decimal = Field(..., gt=0)
    minimum_order_value: Decimal = Field(Decimal("0.00"), ge=0)
    maximum_discount: Decimal | None = Field(None, gt=0)
    start_date: datetime
    expiry_date: datetime
    usage_limit: int = Field(..., gt=0)

    @model_validator(mode="after")
    def check_coupon_rules(self):
        if self.expiry_date <= self.start_date:
            raise ValueError("expiry_date must be after start_date.")

        # a percentage discount without a cap could theoretically wipe
        # out the entire order total on a large enough order - a flat
        # discount has no such risk, so this check only applies to
        # percentage-type coupons
        if self.discount_type == DiscountType.PERCENTAGE and self.discount_value > 100:
            raise ValueError("A percentage discount cannot exceed 100.")

        return self


class CouponUpdate(AppBaseSchema):
    minimum_order_value: Decimal | None = Field(None, ge=0)
    maximum_discount: Decimal | None = Field(None, gt=0)
    expiry_date: datetime | None = None
    usage_limit: int | None = Field(None, gt=0)
    status: CouponStatus | None = None


class CouponResponse(AppBaseSchema):
    id: int
    coupon_code: str
    discount_type: DiscountType
    discount_value: Decimal
    minimum_order_value: Decimal
    maximum_discount: Decimal | None
    start_date: datetime
    expiry_date: datetime
    usage_limit: int
    times_used: int
    status: CouponStatus
    created_at: datetime


class CouponMessageResponse(AppBaseSchema):
    message: str
    data: CouponResponse


class CouponPaginationResponse(AppBaseSchema):
    message: str
    data: list[CouponResponse]
    pagination: PaginationResponse