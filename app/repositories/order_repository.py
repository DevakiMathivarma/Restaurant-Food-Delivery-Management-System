# app/repositories/order_repository.py

from sqlalchemy.orm import Session, joinedload

from app.models.order import Order
from app.repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Order, db)

    def get_by_id_with_details(self, order_id: int):

        return (
            self.db.query(Order)
            .options(
                joinedload(Order.customer),
                joinedload(Order.restaurant),
                joinedload(Order.delivery_partner),
                joinedload(Order.items)
            )
            .filter(Order.id == order_id)
            .first()
        )

    def get_by_order_number(self, order_number: str):

        return self.db.query(Order).filter(Order.order_number == order_number).first()

    def list_orders(self, customer_id, restaurant_id, order_status, payment_status, delivery_partner_id, start_date, end_date, sort_column, sort_order, offset, limit):

        query = self.db.query(Order).options(
            joinedload(Order.customer), joinedload(Order.restaurant), joinedload(Order.delivery_partner), joinedload(Order.items)
        )

        if customer_id:

            query = query.filter(Order.customer_id == customer_id)

        if restaurant_id:

            query = query.filter(Order.restaurant_id == restaurant_id)

        if order_status:

            query = query.filter(Order.order_status == order_status)

        if payment_status:

            query = query.filter(Order.payment_status == payment_status)

        if delivery_partner_id:

            query = query.filter(Order.delivery_partner_id == delivery_partner_id)

        if start_date:

            query = query.filter(Order.created_at >= start_date)

        if end_date:

            query = query.filter(Order.created_at <= end_date)

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        orders = query.offset(offset).limit(limit).all()

        return orders, total_records