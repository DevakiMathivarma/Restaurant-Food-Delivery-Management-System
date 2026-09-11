from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.delivery_partner import AvailabilityStatus, DeliveryPartner
from app.models.user import User, UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.delivery_partner_repository import DeliveryPartnerRepository
from app.repositories.user_repository import UserRepository
from app.schemas.delivery_partner_schema import DeliveryPartnerCreate, DeliveryPartnerUpdate, DeliveryPartnerAvailabilityUpdate, DeliveryPartnerLocationUpdate
from app.utils.hashing import hash_password
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_delivery_partner(data: DeliveryPartnerCreate, db: Session) -> dict:

    try:

        logger.info(f"Creating delivery partner : {data.email}")

        user_repo = UserRepository(db)
        partner_repo = DeliveryPartnerRepository(db)
        audit_repo = AuditLogRepository(db)

        existing_user = user_repo.get_by_email_or_phone(data.email, data.phone)

        if existing_user:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone number already registered.")

        existing_vehicle = partner_repo.get_by_vehicle_number(data.vehicle_number)

        if existing_vehicle:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This vehicle number is already registered.")

        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=UserRole.DELIVERY_PARTNER
        )

        user_repo.add(user)

        db.flush()

        partner = DeliveryPartner(
            user_id=user.id,
            vehicle_type=data.vehicle_type,
            vehicle_number=data.vehicle_number
        )

        partner_repo.add(partner)

        db.flush()

        audit_repo.log(
            user_id=user.id,
            action="CREATE",
            entity_type="DeliveryPartner",
            entity_id=partner.id,
            description="Delivery partner self-registered"
        )

        db.commit()

        partner = partner_repo.get_by_id_with_details(partner.id)

        logger.info(f"Delivery partner created successfully : {partner.id}")

        return {"message": "Delivery partner registered successfully.", "data": partner}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Delivery partner creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to register delivery partner.")


def get_all_partners(db: Session, page: int = 1, limit: int = 10, availability_status=None, sort_by: str = "created_at", sort_order: str = "desc") -> dict:

    logger.info("Fetching delivery partners list.")

    partner_repo = DeliveryPartnerRepository(db)

    sortable_columns = {"created_at": DeliveryPartner.created_at}

    sort_column = sortable_columns.get(sort_by, DeliveryPartner.created_at)

    partners, total_records = partner_repo.list_partners(availability_status, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Delivery partners fetched successfully.", "data": partners, "pagination": get_pagination(total_records, page, limit)}


def update_availability(current_user, data: DeliveryPartnerAvailabilityUpdate, db: Session) -> dict:

    try:

        logger.info(f"Updating availability : partner {current_user.delivery_partner.id}, status {data.availability_status.value}")

        partner_repo = DeliveryPartnerRepository(db)

        partner = partner_repo.get_by_id(current_user.delivery_partner.id)

        # one driver cannot handle conflicting active deliveries - level
        # 8 business rule. a partner currently on a delivery shouldn't
        # be able to manually change their status away from ON_DELIVERY
        # at all - not to AVAILABLE, and not to OFFLINE either. their
        # status only genuinely changes back automatically once
        # order_service.py marks the order DELIVERED
        if partner.availability_status == AvailabilityStatus.ON_DELIVERY:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your availability while on an active delivery.")

        partner.availability_status = data.availability_status

        db.commit()

        db.refresh(partner)

        logger.info(f"Availability updated successfully : partner {partner.id}")

        return {"message": "Availability updated successfully.", "data": partner}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Availability update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update availability.")


def update_location(current_user, data: DeliveryPartnerLocationUpdate, db: Session) -> dict:

    try:

        partner_repo = DeliveryPartnerRepository(db)

        partner = partner_repo.get_by_id(current_user.delivery_partner.id)

        partner.current_latitude = data.current_latitude
        partner.current_longitude = data.current_longitude

        db.commit()

        db.refresh(partner)

        # push the location update live through websocket, for any
        # active order this partner is currently delivering - bonus
        # feature, genuinely wired in now
        from app.models.order import Order, OrderStatus
        from app.routes.websocket import broadcast_order_update_sync

        active_order = db.query(Order).filter(
            Order.delivery_partner_id == partner.id,
            Order.order_status.in_([OrderStatus.PICKED_UP, OrderStatus.OUT_FOR_DELIVERY])
        ).first()

        if active_order:

            broadcast_order_update_sync(active_order.id, {
                "order_id": active_order.id,
                "delivery_partner_location": {"latitude": float(data.current_latitude), "longitude": float(data.current_longitude)}
            })

        logger.info(f"Location updated : partner {partner.id}")

        return {"message": "Location updated successfully.", "data": partner}

    except Exception as error:

        db.rollback()

        logger.error(f"Location update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update location.")