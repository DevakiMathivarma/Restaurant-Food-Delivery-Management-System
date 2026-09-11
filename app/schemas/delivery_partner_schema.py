

from datetime import datetime
from decimal import Decimal

from pydantic import EmailStr, Field

from app.models.delivery_partner import AvailabilityStatus, VehicleType
from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.user_schema import UserBasicResponse


# creates both the login account and the delivery partner profile
# together, in one call 
class DeliveryPartnerCreate(AppBaseSchema):
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=100)
    vehicle_type: VehicleType
    vehicle_number: str = Field(..., min_length=3, max_length=20)


class DeliveryPartnerUpdate(AppBaseSchema):
    vehicle_type: VehicleType | None = None
    vehicle_number: str | None = Field(None, min_length=3, max_length=20)


class DeliveryPartnerAvailabilityUpdate(AppBaseSchema):
    availability_status: AvailabilityStatus


class DeliveryPartnerLocationUpdate(AppBaseSchema):
    current_latitude: Decimal
    current_longitude: Decimal


class DeliveryPartnerBasicResponse(AppBaseSchema):
    id: int
    user: UserBasicResponse
    vehicle_type: VehicleType
    availability_status: AvailabilityStatus


class DeliveryPartnerResponse(DeliveryPartnerBasicResponse):
    vehicle_number: str
    current_latitude: Decimal | None
    current_longitude: Decimal | None
    created_at: datetime
    updated_at: datetime


class DeliveryPartnerMessageResponse(AppBaseSchema):
    message: str
    data: DeliveryPartnerResponse


class DeliveryPartnerPaginationResponse(AppBaseSchema):
    message: str
    data: list[DeliveryPartnerResponse]
    pagination: PaginationResponse