from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    __table_args__ = (
        CheckConstraint("restaurant_rating >= 1 AND restaurant_rating <= 5", name="ck_review_restaurant_rating_range"),
        CheckConstraint(
            "delivery_rating IS NULL OR (delivery_rating >= 1 AND delivery_rating <= 5)",
            name="ck_review_delivery_rating_range"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    # one order, one review - a customer shouldn't be able to review the
    # same order twice, enforced at the database level
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)

    restaurant_rating = Column(Integer, nullable=False)
    food_review_text = Column(Text, nullable=True)

    # delivery_rating is nullable 
    delivery_rating = Column(Integer, nullable=True)
    delivery_review_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    order = relationship("Order", back_populates="reviews")
    customer = relationship("Customer", back_populates="reviews")