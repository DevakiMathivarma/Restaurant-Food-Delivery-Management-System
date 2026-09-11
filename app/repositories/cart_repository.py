from sqlalchemy.orm import Session, joinedload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.repositories.base_repository import BaseRepository


class CartRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Cart, db)

    def get_by_customer_id(self, customer_id: int):

        return (
            self.db.query(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.menu_item))
            .filter(Cart.customer_id == customer_id)
            .first()
        )

    def get_item(self, cart_id: int, menu_item_id: int):

        return self.db.query(CartItem).filter(CartItem.cart_id == cart_id, CartItem.menu_item_id == menu_item_id).first()