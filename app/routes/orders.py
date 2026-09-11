from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_customer, require_restaurant_side, require_admin_or_owner, require_any_role
from app.database import get_db
from app.models.order import OrderStatus,PaymentStatus
from app.models.user import User
from app.schemas.order_schema import OrderCreate, OrderStatusUpdate, OrderMessageResponse, OrderPaginationResponse
from app.services.order_service import create_order, get_order_by_id, get_all_orders, update_order_status, assign_delivery_partner

router = APIRouter(prefix="/api/v1/orders", tags=["Order Management"])


@router.post("", response_model=OrderMessageResponse, status_code=status.HTTP_201_CREATED)
def place_order(data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return create_order(data, current_user, db)

from datetime import datetime


@router.get("", response_model=OrderPaginationResponse, dependencies=[Depends(require_any_role)])
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    customer_id: int | None = Query(None),
    restaurant_id: int | None = Query(None),
    order_status: OrderStatus | None = Query(None),
    payment_status: PaymentStatus | None = Query(None),
    delivery_partner_id: int | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_orders(
        db=db, page=page, limit=limit, customer_id=customer_id, restaurant_id=restaurant_id, order_status=order_status,
        payment_status=payment_status, delivery_partner_id=delivery_partner_id, start_date=start_date, end_date=end_date,
        sort_by=sort_by, sort_order=sort_order
    )

@router.get("/{order_id}", response_model=OrderMessageResponse, dependencies=[Depends(require_any_role)])
def get_order(order_id: int, db: Session = Depends(get_db)):

    return get_order_by_id(order_id, db)


@router.put("/{order_id}/status", response_model=OrderMessageResponse, dependencies=[Depends(require_restaurant_side)])
def update_status(order_id: int, data: OrderStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_restaurant_side)):

    return update_order_status(order_id, data, current_user, db)


@router.post("/{order_id}/assign-delivery-partner", response_model=OrderMessageResponse, dependencies=[Depends(require_admin_or_owner)])
def assign_partner(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_owner)):

    return assign_delivery_partner(order_id, current_user, db)