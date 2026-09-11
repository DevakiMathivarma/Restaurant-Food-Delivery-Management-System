

from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common_schema import AppBaseSchema, PaginationResponse
from app.schemas.user_schema import UserBasicResponse


# creates both the login account and the customer profile together, in
# one call 
class CustomerCreate(AppBaseSchema):
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=100)


class CustomerUpdate(AppBaseSchema):
    full_name: str | None = Field(None, min_length=3, max_length=100)
    phone: str | None = Field(None, min_length=10, max_length=15)


class CustomerBasicResponse(AppBaseSchema):
    id: int
    user: UserBasicResponse


class CustomerResponse(CustomerBasicResponse):
    created_at: datetime
    updated_at: datetime


class CustomerMessageResponse(AppBaseSchema):
    message: str
    data: CustomerResponse


class CustomerPaginationResponse(AppBaseSchema):
    message: str
    data: list[CustomerResponse]
    pagination: PaginationResponse