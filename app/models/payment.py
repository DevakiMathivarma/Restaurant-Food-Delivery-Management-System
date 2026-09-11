from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PaymentMethod(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
    WALLET = "WALLET"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"


class PaymentTransactionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class Payment(Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)

    # unique transaction reference - the real mechanism behind "prevent
    # duplicate transactions", not required for cash on delivery, so
    # nullable, but unique whenever it is provided
    transaction_id = Column(String(100), unique=True, nullable=True, index=True)

    status = Column(SQLEnum(PaymentTransactionStatus), default=PaymentTransactionStatus.PENDING, nullable=False)

    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # relationships
    order = relationship("Order", back_populates="payments")
    created_by = relationship("User")