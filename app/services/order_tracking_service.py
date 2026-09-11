from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order import Order
from app.repositories.base_repository import BaseRepository
from app.repositories.order_tracking_repository import OrderTrackingRepository
from app.utils.logger import logger


def get_tracking_history(order_id: int, db: Session) -> dict:

    logger.info(f"Fetching tracking history for order : {order_id}")

    order_repo = BaseRepository(Order, db)
    tracking_repo = OrderTrackingRepository(db)

    order = order_repo.get_by_id(order_id)

    if not order:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    tracking_history = tracking_repo.list_for_order(order_id)

    return {"message": "Tracking history fetched successfully.", "data": tracking_history}