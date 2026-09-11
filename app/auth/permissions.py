from fastapi import Depends, HTTPException, status

from app.auth.current_user import get_current_user
from app.models.user import User, UserRole


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user


def require_restaurant_owner(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.RESTAURANT_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restaurant Owner access required.")
    return current_user


def require_restaurant_staff(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.RESTAURANT_STAFF:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restaurant Staff access required.")
    return current_user


def require_delivery_partner(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.DELIVERY_PARTNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Delivery Partner access required.")
    return current_user


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer access required.")
    return current_user


# admin or restaurant owner - restaurant setup, and creating restaurant
# staff for their own kitchen team
def require_admin_or_owner(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.RESTAURANT_OWNER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or Restaurant Owner access required.")
    return current_user


# restaurant owner or their own staff - day-to-day menu/order management
def require_restaurant_side(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.RESTAURANT_OWNER, UserRole.RESTAURANT_STAFF):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restaurant access required.")
    return current_user


def require_any_role(current_user: User = Depends(get_current_user)) -> User:
    return current_user