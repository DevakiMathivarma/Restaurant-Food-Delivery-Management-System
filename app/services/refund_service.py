from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import Payment
from app.models.refund import Refund, RefundStatus
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.refund_repository import RefundRepository
from app.schemas.refund_schema import RefundCreate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_refund(order_id: int, data: RefundCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating refund : order {order_id}")

        order_repo = BaseRepository(Order, db)
        refund_repo = RefundRepository(db)
        audit_repo = AuditLogRepository(db)

        order = order_repo.get_by_id(order_id)

        if not order:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        # only cancelled/eligible orders can be refunded - level 11
        # business rule
        if order.order_status != OrderStatus.CANCELLED:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only cancelled orders can be refunded.")

        # one order, one refund - friendly pre-check, backed by the
        # database's own unique constraint
        existing_refund = refund_repo.get_by_order_id(order_id)

        if existing_refund:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This order has already been refunded.")

        payment = db.query(Payment).filter(Payment.order_id == order_id).first()

        if not payment:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This order has no recorded payment to refund.")

        # refund amount cannot exceed the amount actually paid - level
        # 11 business rule
        if data.refund_amount > payment.amount:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Refund amount cannot exceed the amount paid, which was {payment.amount}.")

        refund = Refund(
            order_id=order_id,
            refund_amount=data.refund_amount,
            reason=data.reason,
            status=RefundStatus.COMPLETED,
            refund_date=datetime.now(timezone.utc),
            processed_by_user_id=current_user.id
        )

        refund_repo.add(refund)

        db.flush()

        order.payment_status = PaymentStatus.REFUNDED

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Refund",
            entity_id=refund.id,
            description=f"Refund of {data.refund_amount} processed for order {order_id}"
        )

        db.commit()

        db.refresh(refund)

        refund = refund_repo.get_by_id_with_details(refund.id)

        from app.tasks import send_refund_email

        customer_user = order.customer.user

        send_refund_email.delay(customer_user.email, customer_user.full_name, order.order_number, str(data.refund_amount))

        logger.info(f"Refund created successfully : {refund.id}")

        return {"message": "Refund processed successfully.", "data": refund}

    except HTTPException:

        raise

    except IntegrityError:

        db.rollback()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This order has already been refunded.")

    except Exception as error:

        db.rollback()

        logger.error(f"Refund creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to process refund.")


def get_refund_by_id(refund_id: int, db: Session) -> dict:

    logger.info(f"Fetching refund by id : {refund_id}")

    refund_repo = RefundRepository(db)

    refund = refund_repo.get_by_id_with_details(refund_id)

    if not refund:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund not found.")

    return {"message": "Refund fetched successfully.", "data": refund}


def get_all_refunds(db: Session, page: int = 1, limit: int = 10) -> dict:

    logger.info("Fetching refunds list.")

    refund_repo = RefundRepository(db)

    refunds, total_records = refund_repo.list_refunds(get_offset(page, limit), limit)

    return {"message": "Refunds fetched successfully.", "data": refunds, "pagination": get_pagination(total_records, page, limit)}