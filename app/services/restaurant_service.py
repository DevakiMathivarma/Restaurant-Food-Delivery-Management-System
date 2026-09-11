from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.restaurant import Restaurant, RestaurantStatus
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.restaurant_schema import RestaurantCreate, RestaurantUpdate, RestaurantResponse
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset
from app.utils.redis_cache import get_cache, set_cache, delete_cache

CACHE_TTL = 600


def create_restaurant(data: RestaurantCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating restaurant : {data.restaurant_name}")

        restaurant_repo = RestaurantRepository(db)
        audit_repo = AuditLogRepository(db)

        restaurant = Restaurant(**data.model_dump(), owner_id=current_user.id)

        restaurant_repo.add(restaurant)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Restaurant",
            entity_id=restaurant.id,
            description=f"Restaurant '{data.restaurant_name}' created"
        )

        db.commit()

        restaurant = restaurant_repo.get_by_id_with_details(restaurant.id)

        logger.info(f"Restaurant created successfully : {restaurant.id}")

        return {"message": "Restaurant created successfully.", "data": restaurant}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Restaurant creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create restaurant.")


# get by id - cached (bonus feature, redis)
def get_restaurant_by_id(restaurant_id: int, db: Session) -> dict:

    logger.info(f"Fetching restaurant by id : {restaurant_id}")

    cache_key = f"restaurant:{restaurant_id}"

    cached_restaurant = get_cache(cache_key)

    if cached_restaurant:

        logger.info(f"Restaurant cache hit : {restaurant_id}")

        return {"message": "Restaurant fetched successfully.", "data": cached_restaurant}

    restaurant_repo = RestaurantRepository(db)

    restaurant = restaurant_repo.get_by_id_with_details(restaurant_id)

    if not restaurant:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

    set_cache(cache_key, RestaurantResponse.model_validate(restaurant).model_dump(mode="json"), expire=CACHE_TTL)

    return {"message": "Restaurant fetched successfully.", "data": restaurant}


# level 12-equivalent - filter by city, cuisine type, status
def get_all_restaurants(
    db: Session,
    page: int = 1,
    limit: int = 10,
    city: str | None = None,
    cuisine_type: str | None = None,
    status_filter=None,
    min_rating: float | None = None,
    max_delivery_radius=None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching restaurants list.")

    restaurant_repo = RestaurantRepository(db)

    sortable_columns = {"created_at": Restaurant.created_at, "restaurant_name": Restaurant.restaurant_name}

    sort_column = sortable_columns.get(sort_by, Restaurant.created_at)

    restaurants, total_records = restaurant_repo.list_restaurants(
        city, cuisine_type, status_filter, min_rating, max_delivery_radius, search, sort_column, sort_order, get_offset(page, limit), limit
    )

    return {"message": "Restaurants fetched successfully.", "data": restaurants, "pagination": get_pagination(total_records, page, limit)}

def update_restaurant(restaurant_id: int, data: RestaurantUpdate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Updating restaurant : {restaurant_id}")

        restaurant_repo = RestaurantRepository(db)
        audit_repo = AuditLogRepository(db)

        restaurant = restaurant_repo.get_by_id_with_details(restaurant_id)

        if not restaurant:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

        # a restaurant owner can only update their own restaurant, admin
        # can update any
        if current_user.role.value == "RESTAURANT_OWNER" and restaurant.owner_id != current_user.id:

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own restaurant.")

        update_data = data.model_dump(exclude_unset=True)

        # opening and closing times must be validated - re-checked here
        # since an update might only change one of the two, requiring us
        # to merge with the existing value before comparing
        new_opening = update_data.get("opening_time", restaurant.opening_time)
        new_closing = update_data.get("closing_time", restaurant.closing_time)

        if new_closing <= new_opening:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="closing_time must be after opening_time.")

        for key, value in update_data.items():

            setattr(restaurant, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Restaurant",
            entity_id=restaurant.id,
            description="Restaurant updated"
        )

        db.commit()

        db.refresh(restaurant)

        delete_cache(f"restaurant:{restaurant_id}")

        logger.info(f"Restaurant updated successfully : {restaurant_id}")

        return {"message": "Restaurant updated successfully.", "data": restaurant}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Restaurant update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update restaurant.")