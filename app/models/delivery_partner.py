from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class VehicleType(str, Enum):
    BIKE = "BIKE"
    SCOOTER = "SCOOTER"
    BICYCLE = "BICYCLE"
    CAR = "CAR"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ON_DELIVERY = "ON_DELIVERY"
    OFFLINE = "OFFLINE"


class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"

    id = Column(Integer, primary_key=True, index=True)

    # one login account, one delivery partner profile 
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    vehicle_type = Column(SQLEnum(VehicleType), nullable=False)
    vehicle_number = Column(String(20), unique=True, nullable=False)

    availability_status = Column(SQLEnum(AvailabilityStatus), default=AvailabilityStatus.OFFLINE, nullable=False)

    # live location, updated by the partner themselves as they move -
    # plain stored coordinates, no live maps api call needed for this
    # part, matching our earlier scoping decision. pushed live through
    # websocket when it changes during an active delivery
    current_latitude = Column(Numeric(9, 6), nullable=True)
    current_longitude = Column(Numeric(9, 6), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    user = relationship("User", back_populates="delivery_partner", foreign_keys=[user_id])

    orders = relationship("Order", back_populates="delivery_partner")