from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin, require_delivery_partner, require_any_role
from app.database import get_db
from app.models.delivery_partner import AvailabilityStatus
from app.models.user import User
from app.schemas.delivery_partner_schema import (
    DeliveryPartnerCreate, DeliveryPartnerAvailabilityUpdate, DeliveryPartnerLocationUpdate,
    DeliveryPartnerMessageResponse, DeliveryPartnerPaginationResponse
)
from app.services.delivery_partner_service import create_delivery_partner, get_all_partners, update_availability, update_location

router = APIRouter(prefix="/api/v1/delivery-partners", tags=["Delivery Partner Management"])


@router.post("", response_model=DeliveryPartnerMessageResponse, status_code=status.HTTP_201_CREATED)
def register_delivery_partner(data: DeliveryPartnerCreate, db: Session = Depends(get_db)):

    return create_delivery_partner(data, db)


@router.get("", response_model=DeliveryPartnerPaginationResponse, dependencies=[Depends(require_admin)])
def list_delivery_partners(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    availability_status: AvailabilityStatus | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_partners(db=db, page=page, limit=limit, availability_status=availability_status, sort_by=sort_by, sort_order=sort_order)


@router.put("/availability", response_model=DeliveryPartnerMessageResponse)
def update_my_availability(data: DeliveryPartnerAvailabilityUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_delivery_partner)):

    return update_availability(current_user, data, db)


@router.put("/location", response_model=DeliveryPartnerMessageResponse)
def update_my_location(data: DeliveryPartnerLocationUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_delivery_partner)):

    return update_location(current_user, data, db)