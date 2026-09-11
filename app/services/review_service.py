from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.review import Review
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review_schema import ReviewCreate, ReviewUpdate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_review(order_id: int, data: ReviewCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating review : order {order_id}")

        order_repo = BaseRepository(Order, db)
        review_repo = ReviewRepository(db)
        audit_repo = AuditLogRepository(db)

        order = order_repo.get_by_id(order_id)

        if not order:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        if order.customer_id != current_user.customer.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        # reviews can only be added to completed/delivered orders -
        # level 12 business rule
        if order.order_status != OrderStatus.DELIVERED:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can only review orders that have been delivered.")

        # one review per order - friendly pre-check, backed by the
        # database's own unique constraint
        existing_review = review_repo.get_by_order_id(order_id)

        if existing_review:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already reviewed this order.")

        review = Review(order_id=order_id, customer_id=current_user.customer.id, **data.model_dump())

        review_repo.add(review)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Review",
            entity_id=review.id,
            description=f"Review submitted for order {order_id}"
        )

        db.commit()

        db.refresh(review)

        logger.info(f"Review created successfully : {review.id}")

        return {"message": "Review submitted successfully.", "data": review}

    except HTTPException:

        raise

    except IntegrityError:

        db.rollback()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already reviewed this order.")

    except Exception as error:

        db.rollback()

        logger.error(f"Review creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to submit review.")


def get_reviews_for_restaurant(restaurant_id: int, db: Session, page: int = 1, limit: int = 10) -> dict:

    logger.info(f"Fetching reviews for restaurant : {restaurant_id}")

    review_repo = ReviewRepository(db)

    reviews, total_records = review_repo.list_for_restaurant(restaurant_id, get_offset(page, limit), limit)

    return {"message": "Reviews fetched successfully.", "data": reviews, "pagination": get_pagination(total_records, page, limit)}


def update_review(review_id: int, data: ReviewUpdate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Updating review : {review_id}")

        review_repo = ReviewRepository(db)
        audit_repo = AuditLogRepository(db)

        review = review_repo.get_by_id(review_id)

        if not review or review.customer_id != current_user.customer.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():

            setattr(review, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Review",
            entity_id=review.id,
            description="Review updated"
        )

        db.commit()

        db.refresh(review)

        logger.info(f"Review updated successfully : {review_id}")

        return {"message": "Review updated successfully.", "data": review}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Review update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update review.")