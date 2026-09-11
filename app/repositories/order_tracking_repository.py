from sqlalchemy.orm import Session, joinedload

from app.models.order_tracking import OrderTracking
from app.repositories.base_repository import BaseRepository


class OrderTrackingRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(OrderTracking, db)

    def list_for_order(self, order_id: int):

        return (
            self.db.query(OrderTracking)
            .options(joinedload(OrderTracking.updated_by))
            .filter(OrderTracking.order_id == order_id)
            .order_by(OrderTracking.created_at.asc())
            .all()
        )