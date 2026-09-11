from sqlalchemy.orm import Session, joinedload

from app.models.refund import Refund
from app.repositories.base_repository import BaseRepository


class RefundRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Refund, db)

    def get_by_id_with_details(self, refund_id: int):

        return self.db.query(Refund).options(joinedload(Refund.order), joinedload(Refund.processed_by)).filter(Refund.id == refund_id).first()

    def get_by_order_id(self, order_id: int):

        return self.db.query(Refund).filter(Refund.order_id == order_id).first()

    def list_refunds(self, offset: int, limit: int):

        query = self.db.query(Refund).options(joinedload(Refund.order), joinedload(Refund.processed_by)).order_by(Refund.created_at.desc())

        total_records = query.count()

        refunds = query.offset(offset).limit(limit).all()

        return refunds, total_records