from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.menu_item import MenuItem
from app.repositories.base_repository import BaseRepository
from app.repositories.cart_repository import CartRepository
from app.schemas.cart_schema import CartItemAdd, CartItemUpdate, CartItemResponse, CartResponse
from app.utils.logger import logger


def _get_or_create_cart(customer_id: int, cart_repo: CartRepository, db: Session) -> Cart:

    cart = cart_repo.get_by_customer_id(customer_id)

    if not cart:

        cart = Cart(customer_id=customer_id)

        cart_repo.add(cart)

        db.flush()

    return cart


def _build_cart_response(cart: Cart) -> dict:

    item_responses = []
    subtotal = Decimal("0.00")

    for item in cart.items:

        line_total = item.menu_item.price * item.quantity

        subtotal += line_total

        item_responses.append(CartItemResponse(
            id=item.id,
            menu_item_id=item.menu_item_id,
            menu_item_name=item.menu_item.name,
            unit_price=item.menu_item.price,
            quantity=item.quantity,
            line_total=line_total
        ))

    return CartResponse(id=cart.id, restaurant_id=cart.restaurant_id, items=item_responses, subtotal=subtotal)


def add_to_cart(data: CartItemAdd, current_user, db: Session) -> dict:

    try:

        logger.info(f"Adding to cart : customer {current_user.customer.id}, menu item {data.menu_item_id}")

        menu_item_repo = BaseRepository(MenuItem, db)
        cart_repo = CartRepository(db)

        menu_item = menu_item_repo.get_by_id(data.menu_item_id)

        if not menu_item:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found.")

        # unavailable items cannot be added to cart - level 5 business rule
        if not menu_item.availability:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This item is currently unavailable.")

        cart = _get_or_create_cart(current_user.customer.id, cart_repo, db)

        # cart should contain items from only one restaurant - level 5
        # business rule, the real enforcement using the cart's own
        # restaurant_id lock
        if cart.restaurant_id is not None and cart.restaurant_id != menu_item.restaurant_id:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your cart already contains items from a different restaurant. Clear your cart to order from here instead."
            )

        existing_item = cart_repo.get_item(cart.id, data.menu_item_id)

        if existing_item:

            existing_item.quantity += data.quantity

        else:

            new_item = CartItem(cart_id=cart.id, menu_item_id=data.menu_item_id, quantity=data.quantity)

            db.add(new_item)

        # lock the cart to this restaurant, if it wasn't already
        if cart.restaurant_id is None:

            cart.restaurant_id = menu_item.restaurant_id

        db.commit()

        cart = cart_repo.get_by_customer_id(current_user.customer.id)

        logger.info(f"Item added to cart successfully : customer {current_user.customer.id}")

        return {"message": "Item added to cart successfully.", "data": _build_cart_response(cart)}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Add to cart failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to add item to cart.")


def get_my_cart(current_user, db: Session) -> dict:

    logger.info(f"Fetching cart for customer : {current_user.customer.id}")

    cart_repo = CartRepository(db)

    cart = _get_or_create_cart(current_user.customer.id, cart_repo, db)

    db.commit()

    cart = cart_repo.get_by_customer_id(current_user.customer.id)

    return {"message": "Cart fetched successfully.", "data": _build_cart_response(cart)}


def update_cart_item(cart_item_id: int, data: CartItemUpdate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Updating cart item : {cart_item_id}")

        cart_item_repo = BaseRepository(CartItem, db)
        cart_repo = CartRepository(db)

        cart_item = cart_item_repo.get_by_id(cart_item_id)

        if not cart_item or cart_item.cart.customer_id != current_user.customer.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")

        cart_item.quantity = data.quantity

        db.commit()

        cart = cart_repo.get_by_customer_id(current_user.customer.id)

        logger.info(f"Cart item updated successfully : {cart_item_id}")

        return {"message": "Cart item updated successfully.", "data": _build_cart_response(cart)}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Cart item update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update cart item.")


def remove_cart_item(cart_item_id: int, current_user, db: Session) -> dict:

    try:

        logger.info(f"Removing cart item : {cart_item_id}")

        cart_item_repo = BaseRepository(CartItem, db)
        cart_repo = CartRepository(db)

        cart_item = cart_item_repo.get_by_id(cart_item_id)

        if not cart_item or cart_item.cart.customer_id != current_user.customer.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")

        cart = cart_item.cart

        cart_item_repo.delete(cart_item)

        db.flush()

        # if the cart is now empty, release its restaurant lock so the
        # customer can freely start ordering from anywhere again
        remaining_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).count()

        if remaining_items == 0:

            cart.restaurant_id = None

        db.commit()

        logger.info(f"Cart item removed successfully : {cart_item_id}")

        return {"message": "Cart item removed successfully."}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Cart item removal failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to remove cart item.")


def clear_cart(current_user, db: Session) -> dict:

    try:

        logger.info(f"Clearing cart for customer : {current_user.customer.id}")

        cart_repo = CartRepository(db)

        cart = cart_repo.get_by_customer_id(current_user.customer.id)

        if cart:

            db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

            cart.restaurant_id = None

            db.commit()

        logger.info(f"Cart cleared successfully : customer {current_user.customer.id}")

        return {"message": "Cart cleared successfully."}

    except Exception as error:

        db.rollback()

        logger.error(f"Cart clear failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to clear cart.")