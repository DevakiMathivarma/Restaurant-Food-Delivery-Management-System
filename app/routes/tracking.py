from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.permissions import require_any_role
from app.database import get_db
from app.schemas.order_tracking_schema import OrderTrackingListResponse
from app.services.order_tracking_service import get_tracking_history

router = APIRouter(prefix="/api/v1/orders", tags=["Order Tracking"])


@router.get("/{order_id}/tracking", response_model=OrderTrackingListResponse, dependencies=[Depends(require_any_role)])
def get_order_tracking(order_id: int, db: Session = Depends(get_db)):

    return get_tracking_history(order_id, db)