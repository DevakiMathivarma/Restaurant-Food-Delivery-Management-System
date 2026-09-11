from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from decimal import Decimal
from app.auth.permissions import require_restaurant_side, require_any_role
from app.database import get_db
from app.models.user import User
from app.schemas.common_schema import MessageResponse
from app.schemas.menu_item_schema import MenuItemCreate, MenuItemUpdate, MenuItemMessageResponse, MenuItemPaginationResponse
from app.services.menu_item_service import create_menu_item, get_menu_item_by_id, get_all_menu_items, update_menu_item, delete_menu_item

router = APIRouter(prefix="/api/v1/menu-items", tags=["Menu Management"])


@router.post("", response_model=MenuItemMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_menu_item(data: MenuItemCreate, db: Session = Depends(get_db), current_user: User = Depends(require_restaurant_side)):

    return create_menu_item(data, current_user, db)


@router.get("", response_model=MenuItemPaginationResponse, dependencies=[Depends(require_any_role)])
def list_menu_items(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    restaurant_id: int | None = Query(None),
    category: str | None = Query(None),
    vegetarian: bool | None = Query(None),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    available_only: bool = Query(False),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_menu_items(
        db=db, page=page, limit=limit, restaurant_id=restaurant_id, category=category, vegetarian=vegetarian,
        min_price=min_price, max_price=max_price, available_only=available_only, search=search, sort_by=sort_by, sort_order=sort_order
    )

@router.get("/{menu_item_id}", response_model=MenuItemMessageResponse, dependencies=[Depends(require_any_role)])
def get_menu_item(menu_item_id: int, db: Session = Depends(get_db)):

    return get_menu_item_by_id(menu_item_id, db)


@router.put("/{menu_item_id}", response_model=MenuItemMessageResponse)
def update_existing_menu_item(menu_item_id: int, data: MenuItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_restaurant_side)):

    return update_menu_item(menu_item_id, data, current_user, db)


@router.delete("/{menu_item_id}", response_model=MessageResponse)
def remove_menu_item(menu_item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_restaurant_side)):

    return delete_menu_item(menu_item_id, current_user, db)