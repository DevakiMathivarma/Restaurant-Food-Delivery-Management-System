from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_owner
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard_schema import RestaurantDashboardResponse
from app.services.restaurant_dashboard_service import get_restaurant_dashboard

router = APIRouter(prefix="/api/v1/restaurants", tags=["Restaurant Dashboard"])


@router.get("/{restaurant_id}/dashboard", response_model=RestaurantDashboardResponse)
def restaurant_dashboard(restaurant_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_owner)):

    return get_restaurant_dashboard(restaurant_id, current_user, db)