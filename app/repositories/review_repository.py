from sqlalchemy.orm import Session, joinedload

from app.models.review import Review
from app.repositories.base_repository import BaseRepository


class ReviewRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Review, db)

    def get_by_order_id(self, order_id: int):

        return self.db.query(Review).filter(Review.order_id == order_id).first()

    def list_for_restaurant(self, restaurant_id: int, offset: int, limit: int):

        from app.models.order import Order

        query = (
            self.db.query(Review)
            .join(Order, Review.order_id == Order.id)
            .options(joinedload(Review.customer))
            .filter(Order.restaurant_id == restaurant_id)
            .order_by(Review.created_at.desc())
        )

        total_records = query.count()

        reviews = query.offset(offset).limit(limit).all()

        return reviews, total_records