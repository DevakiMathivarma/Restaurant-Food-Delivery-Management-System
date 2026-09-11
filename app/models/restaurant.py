from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RestaurantStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    BUSY = "BUSY"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"


class Restaurant(Base):
    __tablename__ = "restaurants"

    __table_args__ = (
        CheckConstraint("closing_time > opening_time", name="ck_restaurant_hours_valid"),
        CheckConstraint("delivery_radius > 0", name="ck_restaurant_radius_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    restaurant_name = Column(String(200), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    address = Column(String(300), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    phone = Column(String(15), nullable=False)
    cuisine_type = Column(String(100), nullable=False, index=True)

    opening_time = Column(Time, nullable=False)
    closing_time = Column(Time, nullable=False)

    status = Column(SQLEnum(RestaurantStatus), default=RestaurantStatus.CLOSED, nullable=False)

    # delivery_radius in kilometers
    delivery_radius = Column(Numeric(5, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    owner = relationship("User")

    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant")