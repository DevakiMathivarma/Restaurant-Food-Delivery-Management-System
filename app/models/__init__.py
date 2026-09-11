# importing every model here ensures they're all registered with
# SQLAlchemy's mapper registry before any mapper configuration happens -
# a real bug we hit in the property platform, where a model referenced
# only by string name inside a relationship (not directly imported
# anywhere) caused a mapper resolution failure under pytest
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.customer import Customer
from app.models.address import Address
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.coupon import Coupon
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.delivery_partner import DeliveryPartner
from app.models.order_tracking import OrderTracking
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.review import Review
from app.models.audit_log import AuditLog