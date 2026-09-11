from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.menu_item_repository import MenuItemRepository
from app.schemas.menu_item_schema import MenuItemCreate, MenuItemUpdate
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset
from app.utils.redis_cache import delete_cache


def _check_restaurant_ownership(restaurant, current_user):

    if current_user.role.value == "RESTAURANT_OWNER" and restaurant.owner_id != current_user.id:

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only manage menu items for your own restaurant.")


def create_menu_item(data: MenuItemCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating menu item : {data.name}, restaurant {data.restaurant_id}")

        restaurant_repo = BaseRepository(Restaurant, db)
        menu_item_repo = MenuItemRepository(db)
        audit_repo = AuditLogRepository(db)

        restaurant = restaurant_repo.get_by_id(data.restaurant_id)

        if not restaurant:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

        _check_restaurant_ownership(restaurant, current_user)

        menu_item = MenuItem(**data.model_dump())

        menu_item_repo.add(menu_item)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="MenuItem",
            entity_id=menu_item.id,
            description=f"Menu item '{data.name}' created"
        )

        db.commit()

        db.refresh(menu_item)

        logger.info(f"Menu item created successfully : {menu_item.id}")

        return {"message": "Menu item created successfully.", "data": menu_item}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Menu item creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create menu item.")


def get_menu_item_by_id(menu_item_id: int, db: Session) -> dict:

    logger.info(f"Fetching menu item by id : {menu_item_id}")

    menu_item_repo = MenuItemRepository(db)

    menu_item = menu_item_repo.get_by_id(menu_item_id)

    if not menu_item:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found.")

    return {"message": "Menu item fetched successfully.", "data": menu_item}

#  filter by restaurant, category, vegetarian, availability, search
def get_all_menu_items(
    db: Session,
    page: int = 1,
    limit: int = 10,
    restaurant_id: int | None = None,
    category: str | None = None,
    vegetarian: bool | None = None,
    min_price=None,
    max_price=None,
    available_only: bool = False,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching menu items list.")

    menu_item_repo = MenuItemRepository(db)

    sortable_columns = {"created_at": MenuItem.created_at, "price": MenuItem.price}

    sort_column = sortable_columns.get(sort_by, MenuItem.created_at)

    items, total_records = menu_item_repo.list_menu_items(
        restaurant_id, category, vegetarian, min_price, max_price, available_only, search, sort_column, sort_order, get_offset(page, limit), limit
    )

    return {"message": "Menu items fetched successfully.", "data": items, "pagination": get_pagination(total_records, page, limit)}

def update_menu_item(menu_item_id: int, data: MenuItemUpdate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Updating menu item : {menu_item_id}")

        menu_item_repo = MenuItemRepository(db)
        restaurant_repo = BaseRepository(Restaurant, db)
        audit_repo = AuditLogRepository(db)

        menu_item = menu_item_repo.get_by_id(menu_item_id)

        if not menu_item:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found.")

        restaurant = restaurant_repo.get_by_id(menu_item.restaurant_id)

        _check_restaurant_ownership(restaurant, current_user)

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():

            setattr(menu_item, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="MenuItem",
            entity_id=menu_item.id,
            description="Menu item updated"
        )

        db.commit()

        db.refresh(menu_item)

        logger.info(f"Menu item updated successfully : {menu_item_id}")

        return {"message": "Menu item updated successfully.", "data": menu_item}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Menu item update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update menu item.")


def delete_menu_item(menu_item_id: int, current_user, db: Session) -> dict:

    try:

        logger.info(f"Deleting menu item : {menu_item_id}")

        menu_item_repo = MenuItemRepository(db)
        restaurant_repo = BaseRepository(Restaurant, db)
        audit_repo = AuditLogRepository(db)

        menu_item = menu_item_repo.get_by_id(menu_item_id)

        if not menu_item:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found.")

        restaurant = restaurant_repo.get_by_id(menu_item.restaurant_id)

        _check_restaurant_ownership(restaurant, current_user)

        # soft delete via availability, rather than a real database
        # delete - a menu item may already be referenced by real,
        # permanent order history (order_item locks its own name/price
        # copy, but menu_item_id still points back here), so removing it
        # from the menu should never risk breaking that history
        menu_item.availability = False

        audit_repo.log(
            user_id=current_user.id,
            action="DELETE",
            entity_type="MenuItem",
            entity_id=menu_item.id,
            description="Menu item marked unavailable"
        )

        db.commit()

        logger.info(f"Menu item deleted successfully : {menu_item_id}")

        return {"message": "Menu item removed successfully."}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Menu item deletion failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to delete menu item.")