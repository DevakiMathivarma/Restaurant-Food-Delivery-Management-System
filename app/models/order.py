from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    PREPARING = "PREPARING"
    READY = "READY"
    PICKED_UP = "PICKED_UP"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint("subtotal > 0", name="ck_order_subtotal_positive"),
        CheckConstraint("delivery_fee >= 0", name="ck_order_delivery_fee_not_negative"),
        CheckConstraint("discount >= 0", name="ck_order_discount_not_negative"),
        CheckConstraint("tax >= 0", name="ck_order_tax_not_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # unique, human-readable reference, same pattern as every project's
    # auto-generated reference number
    order_number = Column(String(50), unique=True, nullable=False, index=True)

    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="RESTRICT"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True)
    delivery_partner_id = Column(Integer, ForeignKey("delivery_partners.id", ondelete="SET NULL"), nullable=True)

    subtotal = Column(Numeric(10, 2), nullable=False)
    delivery_fee = Column(Numeric(8, 2), default=0, nullable=False)
    discount = Column(Numeric(8, 2), default=0, nullable=False)
    tax = Column(Numeric(8, 2), default=0, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)

    order_status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    customer = relationship("Customer", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    address = relationship("Address")
    coupon = relationship("Coupon", back_populates="orders")
    delivery_partner = relationship("DeliveryPartner", back_populates="orders")

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    tracking_history = relationship("OrderTracking", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="order")