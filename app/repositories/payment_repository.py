from sqlalchemy.orm import Session, joinedload

from app.models.payment import Payment
from app.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Payment, db)

    def get_by_id_with_details(self, payment_id: int):

        return self.db.query(Payment).options(joinedload(Payment.order)).filter(Payment.id == payment_id).first()

    def get_by_order_id(self, order_id: int):

        return self.db.query(Payment).filter(Payment.order_id == order_id).first()

    def list_payments(self, offset: int, limit: int):

        query = self.db.query(Payment).options(joinedload(Payment.order)).order_by(Payment.payment_date.desc())

        total_records = query.count()

        payments = query.offset(offset).limit(limit).all()

        return payments, total_records