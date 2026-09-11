from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin, require_any_role
from app.database import get_db
from app.models.coupon import CouponStatus
from app.models.user import User
from app.schemas.coupon_schema import CouponCreate, CouponUpdate, CouponMessageResponse, CouponPaginationResponse
from app.services.coupon_service import create_coupon, get_all_coupons, update_coupon

router = APIRouter(prefix="/api/v1/coupons", tags=["Coupon Management"])


@router.post("", response_model=CouponMessageResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_new_coupon(data: CouponCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    return create_coupon(data, current_user, db)


@router.get("", response_model=CouponPaginationResponse, dependencies=[Depends(require_any_role)])
def list_coupons(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: CouponStatus | None = Query(None, alias="status"),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_coupons(db=db, page=page, limit=limit, status_filter=status_filter, sort_by=sort_by, sort_order=sort_order)


@router.put("/{coupon_id}", response_model=CouponMessageResponse, dependencies=[Depends(require_admin)])
def update_existing_coupon(coupon_id: int, data: CouponUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    return update_coupon(coupon_id, data, current_user, db)