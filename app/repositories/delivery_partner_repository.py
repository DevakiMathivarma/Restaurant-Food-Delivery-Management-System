from sqlalchemy.orm import Session, joinedload

from app.models.delivery_partner import AvailabilityStatus, DeliveryPartner
from app.repositories.base_repository import BaseRepository


class DeliveryPartnerRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(DeliveryPartner, db)

    def get_by_id_with_details(self, partner_id: int):

        return self.db.query(DeliveryPartner).options(joinedload(DeliveryPartner.user)).filter(DeliveryPartner.id == partner_id).first()

    def get_by_vehicle_number(self, vehicle_number: str):

        return self.db.query(DeliveryPartner).filter(DeliveryPartner.vehicle_number == vehicle_number).first()

    def list_partners(self, availability_status, sort_column, sort_order, offset, limit):

        query = self.db.query(DeliveryPartner).options(joinedload(DeliveryPartner.user))

        if availability_status:

            query = query.filter(DeliveryPartner.availability_status == availability_status)

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        partners = query.offset(offset).limit(limit).all()

        return partners, total_records

    def get_available_partner(self):

        # a genuinely simple assignment strategy - the first available
        # partner found. real platforms would factor in proximity, but
        # that needs real live location data from multiple active
        # partners to meaningfully compare, which isn't something we can
        # simulate in testing - flagged honestly rather than pretending
        # a fake "nearest partner" calculation is real
        return self.db.query(DeliveryPartner).filter(DeliveryPartner.availability_status == AvailabilityStatus.AVAILABLE).first()