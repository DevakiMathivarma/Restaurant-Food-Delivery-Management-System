from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.order import Order
from app.repositories.base_repository import BaseRepository


class RestaurantRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(Restaurant, db)

    def get_by_id_with_details(self, restaurant_id: int):

        return self.db.query(Restaurant).options(joinedload(Restaurant.owner)).filter(Restaurant.id == restaurant_id).first()

    def list_restaurants(self, city, cuisine_type, status, min_rating, max_delivery_radius, search, sort_column, sort_order, offset, limit):

        query = self.db.query(Restaurant).options(joinedload(Restaurant.owner))

        if city:

            query = query.filter(Restaurant.city.ilike(f"%{city}%"))

        if cuisine_type:

            query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine_type}%"))

        if status:

            query = query.filter(Restaurant.status == status)

        # delivery time isn't a stored field anywhere in this schema -
        # delivery_radius is the closest real proxy available, filtering
        # to restaurants within a given radius (smaller radius roughly
        # correlating with faster delivery)
        if max_delivery_radius is not None:

            query = query.filter(Restaurant.delivery_radius <= max_delivery_radius)

        if search:

            search_term = f"%{search}%"

            query = query.filter(or_(Restaurant.restaurant_name.ilike(search_term), Restaurant.address.ilike(search_term)))

        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        all_restaurants = query.all()

        # rating filtering happens in python after the query, since it
        # needs a live calculation across each restaurant's reviews, not
        # a stored column that sql can filter on directly
        if min_rating is not None:

            filtered = []

            for restaurant in all_restaurants:

                ratings = [
                    r.restaurant_rating for r in
                    self.db.query(Review).join(Order, Review.order_id == Order.id).filter(Order.restaurant_id == restaurant.id).all()
                ]

                average_rating = sum(ratings) / len(ratings) if ratings else 0

                if average_rating >= min_rating:

                    filtered.append(restaurant)

            all_restaurants = filtered

        total_records = len(all_restaurants)

        restaurants = all_restaurants[offset:offset + limit]

        return restaurants, total_records