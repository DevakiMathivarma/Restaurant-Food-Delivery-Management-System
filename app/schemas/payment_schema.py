from datetime import datetime
from decimal import Decimal

from pydantic import Field, model_validator

from app.models.payment import PaymentMethod, PaymentTransactionStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse


class PaymentCreate(AppBaseSchema):
    payment_method: PaymentMethod
    transaction_id: str | None = Field(None, min_length=5, max_length=100)

    # transaction_id is required for every real electronic payment
    # method, but genuinely doesn't apply to cash on delivery - this
    # mirrors the model's own nullable column, enforced here too
    @model_validator(mode="after")
    def check_transaction_id_required(self):
        if self.payment_method != PaymentMethod.CASH_ON_DELIVERY and not self.transaction_id:
            raise ValueError("transaction_id is required for all payment methods except cash on delivery.")
        return self


class PaymentResponse(AppBaseSchema):
    id: int
    order_id: int
    amount: Decimal
    payment_method: PaymentMethod
    transaction_id: str | None
    status: PaymentTransactionStatus
    payment_date: datetime


class PaymentMessageResponse(AppBaseSchema):
    message: str
    data: PaymentResponse


class PaymentPaginationResponse(AppBaseSchema):
    message: str
    data: list[PaymentResponse]
    pagination: PaginationResponse