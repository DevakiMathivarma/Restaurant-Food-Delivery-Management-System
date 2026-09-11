from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    __table_args__ = (
        CheckConstraint("price > 0", name="ck_menu_item_price_positive"),
        CheckConstraint("spicy_level >= 0 AND spicy_level <= 5", name="ck_menu_item_spicy_level_range"),
    )

    id = Column(Integer, primary_key=True, index=True)

    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)

    # category isn't given a fixed value list in the task - free text
    # like "Starters", "Main Course", "Desserts"
    category = Column(String(100), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(8, 2), nullable=False)

    # in minutes - a plain estimate, not tied to any live kitchen queue system
    preparation_time = Column(Integer, nullable=True)

    availability = Column(Boolean, default=True, nullable=False)
    vegetarian = Column(Boolean, default=False, nullable=False)

    # 0-5 scale, a simple sensible range since the task doesn't specify
    # exact bounds
    spicy_level = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    restaurant = relationship("Restaurant", back_populates="menu_items")