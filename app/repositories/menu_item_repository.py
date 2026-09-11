from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.menu_item import MenuItem
from app.repositories.base_repository import BaseRepository


class MenuItemRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(MenuItem, db)

    def list_menu_items(self, restaurant_id, category, vegetarian, min_price, max_price, available_only, search, sort_column, sort_order, offset, limit):

        query = self.db.query(MenuItem)

        if restaurant_id:

            query = query.filter(MenuItem.restaurant_id == restaurant_id)

        if category:

            query = query.filter(MenuItem.category.ilike(f"%{category}%"))

        if vegetarian is not None:

            query = query.filter(MenuItem.vegetarian == vegetarian)

        if min_price is not None:

            query = query.filter(MenuItem.price >= min_price)

        if max_price is not None:

            query = query.filter(MenuItem.price <= max_price)

        if available_only:

            query = query.filter(MenuItem.availability == True)

        if search:

            search_term = f"%{search}%"

            query = query.filter(or_(MenuItem.name.ilike(search_term), MenuItem.description.ilike(search_term)))

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        total_records = query.count()

        items = query.offset(offset).limit(limit).all()

        return items, total_records