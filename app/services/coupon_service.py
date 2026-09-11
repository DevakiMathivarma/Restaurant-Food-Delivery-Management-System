from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.coupon import Coupon, CouponStatus, DiscountType
from app.models.order import Order
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.coupon_repository import CouponRepository
from app.schemas.coupon_schema import CouponCreate, CouponUpdate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_coupon(data: CouponCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating coupon : {data.coupon_code}")

        coupon_repo = CouponRepository(db)
        audit_repo = AuditLogRepository(db)

        existing_coupon = coupon_repo.get_by_code(data.coupon_code)

        if existing_coupon:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This coupon code already exists.")

        coupon = Coupon(**data.model_dump())

        coupon_repo.add(coupon)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Coupon",
            entity_id=coupon.id,
            description=f"Coupon '{data.coupon_code}' created"
        )

        db.commit()

        db.refresh(coupon)

        logger.info(f"Coupon created successfully : {coupon.id}")

        return {"message": "Coupon created successfully.", "data": coupon}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Coupon creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create coupon.")


def get_all_coupons(db: Session, page: int = 1, limit: int = 10, status_filter=None, sort_by: str = "created_at", sort_order: str = "desc") -> dict:

    logger.info("Fetching coupons list.")

    coupon_repo = CouponRepository(db)

    sortable_columns = {"created_at": Coupon.created_at, "expiry_date": Coupon.expiry_date}

    sort_column = sortable_columns.get(sort_by, Coupon.created_at)

    coupons, total_records = coupon_repo.list_coupons(status_filter, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Coupons fetched successfully.", "data": coupons, "pagination": get_pagination(total_records, page, limit)}


def update_coupon(coupon_id: int, data: CouponUpdate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Updating coupon : {coupon_id}")

        coupon_repo = CouponRepository(db)
        audit_repo = AuditLogRepository(db)

        coupon = coupon_repo.get_by_id(coupon_id)

        if not coupon:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():

            setattr(coupon, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Coupon",
            entity_id=coupon.id,
            description="Coupon updated"
        )

        db.commit()

        db.refresh(coupon)

        logger.info(f"Coupon updated successfully : {coupon_id}")

        return {"message": "Coupon updated successfully.", "data": coupon}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Coupon update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update coupon.")


# used by order_service.py at checkout - validates a coupon code and
# returns the actual discount amount to apply, without mutating anything
# yet (times_used only increments once the order is genuinely placed)
def validate_and_calculate_discount(coupon_code: str, customer_id: int, order_subtotal: Decimal, db: Session) -> tuple[Coupon, Decimal]:

    coupon_repo = CouponRepository(db)

    coupon = coupon_repo.get_by_code(coupon_code)

    if not coupon:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid coupon code.")

    if coupon.status != CouponStatus.ACTIVE:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This coupon is not currently active.")

    now = datetime.now(timezone.utc)

    # sqlite doesn't reliably preserve timezone info on datetime columns -
    # start_date/expiry_date can come back "naive" even though the
    # column is declared timezone=True. attach utc explicitly if it's
    # missing, so the comparison below never fails
    start = coupon.start_date if coupon.start_date.tzinfo else coupon.start_date.replace(tzinfo=timezone.utc)
    expiry = coupon.expiry_date if coupon.expiry_date.tzinfo else coupon.expiry_date.replace(tzinfo=timezone.utc)

    # expired coupons cannot be applied - level 6 business rule
    if now < start or now > expiry:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This coupon is not valid at this time.")

    # minimum order value must be satisfied - level 6 business rule
    if order_subtotal < coupon.minimum_order_value:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"This coupon requires a minimum order value of {coupon.minimum_order_value}.")

    # usage limit cannot be exceeded - level 6 business rule
    if coupon.times_used >= coupon.usage_limit:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This coupon has reached its usage limit.")

    # prevent duplicate coupon usage - level 6 business rule
    already_used = db.query(Order).filter(Order.customer_id == customer_id, Order.coupon_id == coupon.id).first()

    if already_used:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already used this coupon.")

    if coupon.discount_type == DiscountType.FLAT:

        discount = coupon.discount_value

    else:

        discount = order_subtotal * (coupon.discount_value / Decimal("100"))

        if coupon.maximum_discount and discount > coupon.maximum_discount:

            discount = coupon.maximum_discount

    return coupon, discount