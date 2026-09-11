from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.order import Order, PaymentStatus
from app.models.payment import Payment, PaymentMethod, PaymentTransactionStatus
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment_schema import PaymentCreate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_payment(order_id: int, data: PaymentCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Recording payment : order {order_id}, method {data.payment_method.value}")

        order_repo = BaseRepository(Order, db)
        payment_repo = PaymentRepository(db)
        audit_repo = AuditLogRepository(db)

        order = order_repo.get_by_id(order_id)

        if not order:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        existing_payment = payment_repo.get_by_order_id(order_id)

        if existing_payment:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This order already has a payment recorded.")

        # prevent duplicate transactions - friendly pre-check, backed by
        # the database's own unique constraint. skipped entirely for
        # cash on delivery, which genuinely has no transaction_id
        if data.transaction_id:

            existing_transaction = db.query(Payment).filter(Payment.transaction_id == data.transaction_id).first()

            if existing_transaction:

                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This transaction ID has already been used.")

        # payment amount must match the order total - level 10 business
        # rule. the amount is always taken from the order itself, never
        # trusted from the client
        payment = Payment(
            order_id=order_id,
            amount=order.total_amount,
            payment_method=data.payment_method,
            transaction_id=data.transaction_id,
            status=PaymentTransactionStatus.SUCCESS,
            created_by_user_id=current_user.id
        )

        payment_repo.add(payment)

        db.flush()

        order.payment_status = PaymentStatus.PAID

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Payment",
            entity_id=payment.id,
            description=f"Payment of {order.total_amount} recorded for order {order_id}"
        )

        db.commit()

        db.refresh(payment)

        from app.tasks import send_payment_success_email

        customer_user = current_user

        send_payment_success_email.delay(customer_user.email, customer_user.full_name, str(order.total_amount), order.order_number)

        logger.info(f"Payment recorded successfully : {payment.id}")

        return {"message": "Payment recorded successfully.", "data": payment}

    except HTTPException:

        raise

    except IntegrityError:

        db.rollback()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This transaction ID has already been used.")

    except Exception as error:

        db.rollback()

        logger.error(f"Payment recording failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to record payment.")


def get_payment_by_id(payment_id: int, db: Session) -> dict:

    logger.info(f"Fetching payment by id : {payment_id}")

    payment_repo = PaymentRepository(db)

    payment = payment_repo.get_by_id_with_details(payment_id)

    if not payment:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

    return {"message": "Payment fetched successfully.", "data": payment}


def get_all_payments(db: Session, page: int = 1, limit: int = 10) -> dict:

    logger.info("Fetching payments list.")

    payment_repo = PaymentRepository(db)

    payments, total_records = payment_repo.list_payments(get_offset(page, limit), limit)

    return {"message": "Payments fetched successfully.", "data": payments, "pagination": get_pagination(total_records, page, limit)}