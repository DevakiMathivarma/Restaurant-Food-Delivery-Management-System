from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.permissions import require_any_role
from app.database import get_db
from app.models.user import User
from app.schemas.payment_schema import PaymentCreate, PaymentMessageResponse, PaymentPaginationResponse
from app.services.payment_service import create_payment, get_payment_by_id, get_all_payments

router = APIRouter(prefix="/api/v1", tags=["Payment Management"])


@router.post("/orders/{order_id}/payment", response_model=PaymentMessageResponse, status_code=status.HTTP_201_CREATED)
def pay_for_order(order_id: int, data: PaymentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return create_payment(order_id, data, current_user, db)


@router.get("/payments", response_model=PaymentPaginationResponse, dependencies=[Depends(require_any_role)])
def list_payments(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):

    return get_all_payments(db, page, limit)


@router.get("/payments/{payment_id}", response_model=PaymentMessageResponse, dependencies=[Depends(require_any_role)])
def get_payment(payment_id: int, db: Session = Depends(get_db)):

    return get_payment_by_id(payment_id, db)