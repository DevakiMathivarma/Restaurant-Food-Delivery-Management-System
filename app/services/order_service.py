import random
import string
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.address import Address
from app.models.cart_item import CartItem
from app.models.delivery_partner import AvailabilityStatus
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem
from app.models.order_tracking import OrderTracking
from app.models.restaurant import Restaurant, RestaurantStatus
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.delivery_partner_repository import DeliveryPartnerRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order_schema import OrderCreate, OrderStatusUpdate
from app.services.coupon_service import validate_and_calculate_discount
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset

TAX_RATE = Decimal("0.05")
DELIVERY_FEE = Decimal("40.00")


def _generate_order_number() -> str:

    random_suffix = "".join(random.choices(string.digits, k=8))

    return f"ORD-{random_suffix}"


def create_order(data: OrderCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating order : customer {current_user.customer.id}")

        address_repo = BaseRepository(Address, db)
        restaurant_repo = BaseRepository(Restaurant, db)
        cart_repo = CartRepository(db)
        order_repo = OrderRepository(db)
        audit_repo = AuditLogRepository(db)

        address = address_repo.get_by_id(data.address_id)

        if not address or address.customer_id != current_user.customer.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")

        cart = cart_repo.get_by_customer_id(current_user.customer.id)

        if not cart or not cart.items:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty.")

        restaurant = restaurant_repo.get_by_id(cart.restaurant_id)

        if not restaurant:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

        # restaurant cannot accept orders when closed - level 7 business rule
        if restaurant.status != RestaurantStatus.OPEN:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This restaurant is not currently accepting orders.")

        # unavailable items cannot be ordered - re-checked here, since
        # availability could have changed after the item was added to cart
        for cart_item in cart.items:

            if not cart_item.menu_item.availability:

                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{cart_item.menu_item.name}' is no longer available.")

        subtotal = sum((item.menu_item.price * item.quantity for item in cart.items), Decimal("0.00"))

        discount = Decimal("0.00")
        coupon = None

        if data.coupon_code:

            coupon, discount = validate_and_calculate_discount(data.coupon_code, current_user.customer.id, subtotal, db)

        tax = subtotal * TAX_RATE

        # calculate automatically: total = subtotal + tax + delivery fee
        # - discount - level 7's own explicit formula
        total_amount = subtotal + tax + DELIVERY_FEE - discount

        order_number = _generate_order_number()

        while order_repo.get_by_order_number(order_number):

            order_number = _generate_order_number()

        order = Order(
            order_number=order_number,
            customer_id=current_user.customer.id,
            restaurant_id=restaurant.id,
            address_id=address.id,
            coupon_id=coupon.id if coupon else None,
            subtotal=subtotal,
            delivery_fee=DELIVERY_FEE,
            discount=discount,
            tax=tax,
            total_amount=total_amount,
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING
        )

        order_repo.add(order)

        db.flush()

        # lock in each item's real name and price at the moment of
        # ordering - never recalculated later, same principle used
        # throughout every project
        for cart_item in cart.items:

            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=cart_item.menu_item_id,
                item_name=cart_item.menu_item.name,
                price_at_order=cart_item.menu_item.price,
                quantity=cart_item.quantity
            )

            db.add(order_item)

        if coupon:

            coupon.times_used += 1

        # write the first tracking entry
        db.add(OrderTracking(order_id=order.id, status=OrderStatus.PENDING.value, updated_by_user_id=current_user.id))

        # clear the cart now that it's become a real order
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

        cart.restaurant_id = None

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Order",
            entity_id=order.id,
            description=f"Order {order_number} placed, total {total_amount}"
        )

        db.commit()

        order = order_repo.get_by_id_with_details(order.id)

        # level 14-equivalent - order confirmation email + real pdf invoice
        from app.utils.pdf import generate_order_invoice_pdf
        from app.tasks import send_order_confirmation_email

        customer_user = current_user

        invoice_path = generate_order_invoice_pdf(
            order_id=order.id,
            order_number=order.order_number,
            customer_name=customer_user.full_name,
            restaurant_name=restaurant.restaurant_name,
            items=[{"quantity": i.quantity, "item_name": i.item_name, "price_at_order": str(i.price_at_order)} for i in order.items],
            subtotal=str(subtotal),
            delivery_fee=str(DELIVERY_FEE),
            discount=str(discount),
            tax=str(tax),
            total_amount=str(total_amount)
        )

        send_order_confirmation_email.delay(customer_user.email, customer_user.full_name, order.order_number, invoice_path)

        # bonus - live websocket update the moment the order is created
        from app.routes.websocket import broadcast_order_update_sync

        broadcast_order_update_sync(order.id, {"order_id": order.id, "status": OrderStatus.PENDING.value})

        logger.info(f"Order created successfully : {order.id}, number {order_number}")

        return {"message": "Order placed successfully.", "data": order}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Order creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to place order.")


def get_order_by_id(order_id: int, db: Session) -> dict:

    logger.info(f"Fetching order by id : {order_id}")

    order_repo = OrderRepository(db)

    order = order_repo.get_by_id_with_details(order_id)

    if not order:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    return {"message": "Order fetched successfully.", "data": order}

def get_all_orders(
    db: Session,
    page: int = 1,
    limit: int = 10,
    customer_id: int | None = None,
    restaurant_id: int | None = None,
    order_status=None,
    payment_status=None,
    delivery_partner_id: int | None = None,
    start_date=None,
    end_date=None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching orders list.")

    order_repo = OrderRepository(db)

    sortable_columns = {"created_at": Order.created_at, "total_amount": Order.total_amount}

    sort_column = sortable_columns.get(sort_by, Order.created_at)

    orders, total_records = order_repo.list_orders(
        customer_id, restaurant_id, order_status, payment_status, delivery_partner_id, start_date, end_date, sort_column, sort_order, get_offset(page, limit), limit
    )

    return {"message": "Orders fetched successfully.", "data": orders, "pagination": get_pagination(total_records, page, limit)}

def update_order_status(order_id: int, data: OrderStatusUpdate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Updating order status : {order_id}, new status {data.order_status.value}")

        order_repo = OrderRepository(db)
        audit_repo = AuditLogRepository(db)

        order = order_repo.get_by_id_with_details(order_id)

        if not order:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        # completed or cancelled orders cannot receive further updates -
        # level 9 business rule
        if order.order_status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This order has already been completed or cancelled.")

        order.order_status = data.order_status

        db.add(OrderTracking(order_id=order.id, status=data.order_status.value, notes=data.notes, updated_by_user_id=current_user.id))

        # the moment an order is genuinely delivered, the assigned
        # delivery partner becomes available again - level 8's own rule
        if data.order_status == OrderStatus.DELIVERED and order.delivery_partner:

            order.delivery_partner.availability_status = AvailabilityStatus.AVAILABLE

        audit_repo.log(
            user_id=current_user.id,
            action="STATUS_UPDATE",
            entity_type="Order",
            entity_id=order.id,
            description=f"Status changed to {data.order_status.value}"
        )

        db.commit()

        order = order_repo.get_by_id_with_details(order_id)

        # level 14-equivalent notifications, wired in immediately
        from app.tasks import send_order_status_update_email, send_order_delivered_email

        customer_user = order.customer.user

        if data.order_status == OrderStatus.DELIVERED:

            send_order_delivered_email.delay(customer_user.email, customer_user.full_name, order.order_number)

        else:

            send_order_status_update_email.delay(customer_user.email, customer_user.full_name, order.order_number, data.order_status.value)

        from app.routes.websocket import broadcast_order_update_sync

        broadcast_order_update_sync(order.id, {"order_id": order.id, "status": data.order_status.value})

        logger.info(f"Order status updated successfully : {order_id}")

        return {"message": "Order status updated successfully.", "data": order}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Order status update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update order status.")


def assign_delivery_partner(order_id: int, current_user, db: Session) -> dict:

    try:

        logger.info(f"Assigning delivery partner to order : {order_id}")

        order_repo = OrderRepository(db)
        partner_repo = DeliveryPartnerRepository(db)
        audit_repo = AuditLogRepository(db)

        order = order_repo.get_by_id_with_details(order_id)

        if not order:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        if order.delivery_partner_id is not None:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This order already has a delivery partner assigned.")

        # only available delivery partners can be assigned - level 8
        # business rule
        partner = partner_repo.get_available_partner()

        if not partner:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No delivery partners are currently available.")

        order.delivery_partner_id = partner.id

        partner.availability_status = AvailabilityStatus.ON_DELIVERY

        audit_repo.log(
            user_id=current_user.id,
            action="ASSIGN",
            entity_type="Order",
            entity_id=order.id,
            description=f"Delivery partner {partner.id} assigned"
        )

        db.commit()

        order = order_repo.get_by_id_with_details(order_id)

        from app.tasks import send_delivery_assignment_email

        customer_user = order.customer.user

        send_delivery_assignment_email.delay(customer_user.email, customer_user.full_name, order.order_number, partner.user.full_name)

        from app.routes.websocket import broadcast_order_update_sync

        broadcast_order_update_sync(order.id, {"order_id": order.id, "delivery_partner_assigned": partner.id})

        logger.info(f"Delivery partner assigned successfully : order {order_id}, partner {partner.id}")

        return {"message": "Delivery partner assigned successfully.", "data": order}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Delivery partner assignment failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to assign delivery partner.")