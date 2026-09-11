from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AddressType(str, Enum):
    HOME = "HOME"
    WORK = "WORK"
    OTHER = "OTHER"


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)

    address_line = Column(String(300), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    pincode = Column(String(10), nullable=False)

    # real coordinates, filled in via the google maps geocoding call when the address is created 
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)

    address_type = Column(SQLEnum(AddressType), default=AddressType.HOME, nullable=False)

    is_default = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    customer = relationship("Customer", back_populates="addresses")