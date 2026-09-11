from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_customer
from app.database import get_db
from app.models.user import User
from app.schemas.cart_schema import CartItemAdd, CartItemUpdate, CartMessageResponse
from app.schemas.common_schema import MessageResponse
from app.services.cart_service import add_to_cart, get_my_cart, update_cart_item, remove_cart_item, clear_cart

router = APIRouter(prefix="/api/v1/cart", tags=["Cart Management"])


@router.post("/items", response_model=CartMessageResponse, status_code=status.HTTP_201_CREATED)
def add_item(data: CartItemAdd, db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return add_to_cart(data, current_user, db)


@router.get("", response_model=CartMessageResponse)
def get_cart(db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return get_my_cart(current_user, db)


@router.put("/items/{cart_item_id}", response_model=CartMessageResponse)
def update_item(cart_item_id: int, data: CartItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return update_cart_item(cart_item_id, data, current_user, db)


@router.delete("/items/{cart_item_id}", response_model=MessageResponse)
def remove_item(cart_item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return remove_cart_item(cart_item_id, current_user, db)


@router.delete("", response_model=MessageResponse)
def clear_my_cart(db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return clear_cart(current_user, db)