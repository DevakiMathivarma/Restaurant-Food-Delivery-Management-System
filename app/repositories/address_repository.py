from sqlalchemy.orm import Session

from app.models.address import Address
from app.repositories.base_repository import BaseRepository


class AddressRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Address, db)

    def list_for_customer(self, customer_id: int):

        return self.db.query(Address).filter(Address.customer_id == customer_id).order_by(Address.is_default.desc(), Address.created_at.desc()).all()

    def unset_other_defaults(self, customer_id: int, exclude_address_id: int | None = None):

        query = self.db.query(Address).filter(Address.customer_id == customer_id, Address.is_default == True)

        if exclude_address_id:

            query = query.filter(Address.id != exclude_address_id)

        for address in query.all():

            address.is_default = False