from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.address import Address
from app.repositories.address_repository import AddressRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.address_schema import AddressCreate, AddressUpdate
from app.utils.google_maps import geocode_address
from app.utils.logger import logger


def create_address(data: AddressCreate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Creating address for customer : {current_user.customer.id}")

        address_repo = AddressRepository(db)
        audit_repo = AuditLogRepository(db)

        existing_addresses = address_repo.list_for_customer(current_user.customer.id)

        # a customer's very first address is automatically their
        # default, regardless of what they passed in - there's no
        # sensible alternative when it's the only address they have
        is_first_address = len(existing_addresses) == 0

        should_be_default = data.is_default or is_first_address

        # real google maps geocoding call - degrades gracefully to
        # (None, None) if GOOGLE_MAPS_API_KEY isn't configured, address
        # creation still succeeds either way
        latitude, longitude = geocode_address(data.address_line, data.city, data.pincode)

        address = Address(
            customer_id=current_user.customer.id,
            address_line=data.address_line,
            city=data.city,
            pincode=data.pincode,
            latitude=latitude,
            longitude=longitude,
            address_type=data.address_type,
            is_default=should_be_default
        )

        address_repo.add(address)

        db.flush()

        # ensure each customer can maintain multiple addresses with only
        # one default - unmark every other address now that this one is
        # the new default
        if should_be_default:

            address_repo.unset_other_defaults(current_user.customer.id, exclude_address_id=address.id)

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Address",
            entity_id=address.id,
            description=f"Address added, geocoded={latitude is not None}"
        )

        db.commit()

        db.refresh(address)

        logger.info(f"Address created successfully : {address.id}, geocoded={latitude is not None}")

        return {"message": "Address added successfully.", "data": address}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Address creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to add address.")


def get_addresses_for_customer(current_user, db: Session) -> dict:

    logger.info(f"Fetching addresses for customer : {current_user.customer.id}")

    address_repo = AddressRepository(db)

    addresses = address_repo.list_for_customer(current_user.customer.id)

    return {"message": "Addresses fetched successfully.", "data": addresses}


def update_address(address_id: int, data: AddressUpdate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Updating address : {address_id}")

        address_repo = AddressRepository(db)
        audit_repo = AuditLogRepository(db)

        address = address_repo.get_by_id(address_id)

        if not address or address.customer_id != current_user.customer.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")

        update_data = data.model_dump(exclude_unset=True)

        # if the address text itself changed, re-geocode it for real,
        # updated coordinates
        location_fields_changed = any(field in update_data for field in ("address_line", "city", "pincode"))

        for key, value in update_data.items():

            setattr(address, key, value)

        if location_fields_changed:

            latitude, longitude = geocode_address(address.address_line, address.city, address.pincode)

            address.latitude = latitude
            address.longitude = longitude

        if update_data.get("is_default") is True:

            address_repo.unset_other_defaults(current_user.customer.id, exclude_address_id=address.id)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Address",
            entity_id=address.id,
            description="Address updated"
        )

        db.commit()

        db.refresh(address)

        logger.info(f"Address updated successfully : {address_id}")

        return {"message": "Address updated successfully.", "data": address}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Address update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update address.")


def delete_address(address_id: int, current_user, db: Session) -> dict:

    try:

        logger.info(f"Deleting address : {address_id}")

        address_repo = AddressRepository(db)
        audit_repo = AuditLogRepository(db)

        address = address_repo.get_by_id(address_id)

        if not address or address.customer_id != current_user.customer.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")

        address_repo.delete(address)

        audit_repo.log(
            user_id=current_user.id,
            action="DELETE",
            entity_type="Address",
            entity_id=address_id,
            description="Address removed"
        )

        db.commit()

        logger.info(f"Address deleted successfully : {address_id}")

        return {"message": "Address deleted successfully."}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Address deletion failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to delete address.")