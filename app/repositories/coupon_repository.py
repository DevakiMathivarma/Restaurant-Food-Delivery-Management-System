
from sqlalchemy.orm import Session
from app.models.coupon import Coupon
from app.repositories.base_repository import BaseRepository


class CouponRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Coupon, db)

    def get_by_code(self, coupon_code: str):

        return self.db.query(Coupon).filter(Coupon.coupon_code == coupon_code).first()

    def list_coupons(self, status, sort_column, sort_order, offset, limit):

        query = self.db.query(Coupon)

        if status:

            query = query.filter(Coupon.status == status)

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        coupons = query.offset(offset).limit(limit).all()

        return coupons, total_records