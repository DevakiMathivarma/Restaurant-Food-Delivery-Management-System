from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)

    # one customer, one cart 
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), unique=True, nullable=False)

    # tracks which restaurant this cart currently belongs to - the real
    # mechanism behind "cart should contain items from only one
    # restaurant." null when the cart is genuinely empty, since an
    # empty cart isn't committed to any restaurant yet
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    customer = relationship("Customer", back_populates="cart")
    restaurant = relationship("Restaurant")

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")