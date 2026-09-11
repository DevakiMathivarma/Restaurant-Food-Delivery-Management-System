from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.models.address import AddressType
from app.schemas.common_schema import AppBaseSchema


class AddressCreate(AppBaseSchema):
    address_line: str = Field(..., min_length=5, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., min_length=4, max_length=10)
    address_type: AddressType = AddressType.HOME
    is_default: bool = False


class AddressUpdate(AppBaseSchema):
    address_line: str | None = Field(None, min_length=5, max_length=300)
    city: str | None = Field(None, min_length=2, max_length=100)
    pincode: str | None = Field(None, min_length=4, max_length=10)
    address_type: AddressType | None = None
    is_default: bool | None = None


class AddressResponse(AppBaseSchema):
    id: int
    customer_id: int
    address_line: str
    city: str
    pincode: str
    latitude: Decimal | None
    longitude: Decimal | None
    address_type: AddressType
    is_default: bool
    created_at: datetime
    updated_at: datetime


class AddressMessageResponse(AppBaseSchema):
    message: str
    data: AddressResponse


class AddressListResponse(AppBaseSchema):
    message: str
    data: list[AddressResponse]