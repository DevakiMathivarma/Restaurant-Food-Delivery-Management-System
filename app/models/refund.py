from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RefundStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Refund(Base):
    __tablename__ = "refunds"

    __table_args__ = (
        CheckConstraint("refund_amount > 0", name="ck_refund_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # one order, one refund - a duplicate refund on the same order
    # should never be possible, enforced at the database level
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)

    refund_amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(300), nullable=True)

    status = Column(SQLEnum(RefundStatus), default=RefundStatus.PENDING, nullable=False)

    refund_date = Column(DateTime(timezone=True), nullable=True)

    processed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    order = relationship("Order")
    processed_by = relationship("User")