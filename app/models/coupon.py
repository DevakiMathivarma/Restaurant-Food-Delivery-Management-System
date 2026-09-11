from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FLAT = "FLAT"


class CouponStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Coupon(Base):
    __tablename__ = "coupons"

    __table_args__ = (
        CheckConstraint("discount_value > 0", name="ck_coupon_discount_positive"),
        CheckConstraint("expiry_date > start_date", name="ck_coupon_dates_valid"),
        CheckConstraint("usage_limit > 0", name="ck_coupon_usage_limit_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    coupon_code = Column(String(50), unique=True, nullable=False, index=True)

    discount_type = Column(SQLEnum(DiscountType), nullable=False)
    discount_value = Column(Numeric(8, 2), nullable=False)

    minimum_order_value = Column(Numeric(8, 2), default=0, nullable=False)

    # only meaningful when discount_type is PERCENTAGE - caps how much a
    # percentage discount can actually take off, nullable since a FLAT
    # discount has no need for this
    maximum_discount = Column(Numeric(8, 2), nullable=True)

    start_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=False)

    usage_limit = Column(Integer, nullable=False)

    # how many times this coupon has actually been used so far - the
    # real counter behind "usage limit cannot be exceeded"
    times_used = Column(Integer, default=0, nullable=False)

    status = Column(SQLEnum(CouponStatus), default=CouponStatus.ACTIVE, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    orders = relationship("Order", back_populates="coupon")