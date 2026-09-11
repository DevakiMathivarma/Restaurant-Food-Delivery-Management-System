from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from decimal import Decimal
from app.auth.permissions import require_admin_or_owner, require_any_role
from app.database import get_db
from app.models.restaurant import RestaurantStatus
from app.models.user import User
from app.schemas.restaurant_schema import RestaurantCreate, RestaurantUpdate, RestaurantMessageResponse, RestaurantPaginationResponse
from app.services.restaurant_service import create_restaurant, get_restaurant_by_id, get_all_restaurants, update_restaurant

router = APIRouter(prefix="/api/v1/restaurants", tags=["Restaurant Management"])


@router.post("", response_model=RestaurantMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_restaurant(data: RestaurantCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_owner)):

    return create_restaurant(data, current_user, db)

@router.get("", response_model=RestaurantPaginationResponse, dependencies=[Depends(require_any_role)])
def list_restaurants(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    city: str | None = Query(None),
    cuisine_type: str | None = Query(None),
    status_filter: RestaurantStatus | None = Query(None, alias="status"),
    min_rating: float | None = Query(None, ge=0, le=5),
    max_delivery_radius: Decimal | None = Query(None, gt=0, description="Filters by delivery_radius, the closest available proxy for delivery time"),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_restaurants(
        db=db, page=page, limit=limit, city=city, cuisine_type=cuisine_type, status_filter=status_filter,
        min_rating=min_rating, max_delivery_radius=max_delivery_radius, search=search, sort_by=sort_by, sort_order=sort_order
    )


@router.get("/{restaurant_id}", response_model=RestaurantMessageResponse, dependencies=[Depends(require_any_role)])
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):

    return get_restaurant_by_id(restaurant_id, db)


@router.put("/{restaurant_id}", response_model=RestaurantMessageResponse)
def update_existing_restaurant(restaurant_id: int, data: RestaurantUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_owner)):

    return update_restaurant(restaurant_id, data, current_user, db)