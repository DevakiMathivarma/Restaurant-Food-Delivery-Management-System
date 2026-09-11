from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.user import User, UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.user_repository import UserRepository
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate
from app.utils.hashing import hash_password
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset


def create_customer(data: CustomerCreate, db: Session) -> dict:

    try:

        logger.info(f"Creating customer : {data.email}")

        user_repo = UserRepository(db)
        customer_repo = CustomerRepository(db)
        audit_repo = AuditLogRepository(db)

        existing_user = user_repo.get_by_email_or_phone(data.email, data.phone)

        if existing_user:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone number already registered.")

        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=UserRole.CUSTOMER
        )

        user_repo.add(user)

        db.flush()

        customer = Customer(user_id=user.id)

        customer_repo.add(customer)

        db.flush()

        audit_repo.log(
            user_id=user.id,
            action="CREATE",
            entity_type="Customer",
            entity_id=customer.id,
            description="Customer self-registered"
        )

        db.commit()

        customer = customer_repo.get_by_id_with_details(customer.id)

        logger.info(f"Customer created successfully : {customer.id}")

        return {"message": "Customer registered successfully.", "data": customer}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Customer creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create customer.")


def get_customer_by_id(customer_id: int, db: Session) -> dict:

    logger.info(f"Fetching customer by id : {customer_id}")

    customer_repo = CustomerRepository(db)

    customer = customer_repo.get_by_id_with_details(customer_id)

    if not customer:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

    return {"message": "Customer fetched successfully.", "data": customer}


def get_all_customers(db: Session, page: int = 1, limit: int = 10, search: str | None = None, sort_by: str = "created_at", sort_order: str = "desc") -> dict:

    logger.info("Fetching customers list.")

    customer_repo = CustomerRepository(db)

    sortable_columns = {"created_at": Customer.created_at}

    sort_column = sortable_columns.get(sort_by, Customer.created_at)

    customers, total_records = customer_repo.list_customers(search, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Customers fetched successfully.", "data": customers, "pagination": get_pagination(total_records, page, limit)}


def update_customer(customer_id: int, data: CustomerUpdate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Updating customer : {customer_id}")

        customer_repo = CustomerRepository(db)
        audit_repo = AuditLogRepository(db)

        customer = customer_repo.get_by_id_with_details(customer_id)

        if not customer:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        # a customer can only update their own profile
        if customer.user_id != current_user.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():

            setattr(customer.user, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Customer",
            entity_id=customer.id,
            description="Customer profile updated"
        )

        db.commit()

        db.refresh(customer)

        logger.info(f"Customer updated successfully : {customer_id}")

        return {"message": "Customer updated successfully.", "data": customer}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Customer update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update customer.")