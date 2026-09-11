from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.permissions import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate, CustomerMessageResponse, CustomerPaginationResponse
from app.services.customer_service import create_customer, get_customer_by_id, get_all_customers, update_customer


from app.auth.permissions import require_customer
from app.schemas.address_schema import AddressCreate, AddressUpdate, AddressMessageResponse, AddressListResponse
from app.schemas.common_schema import MessageResponse
from app.services.address_service import create_address, get_addresses_for_customer, update_address, delete_address

router = APIRouter(prefix="/api/v1/customers", tags=["Customer Management"])


# genuinely public, no token, no hybrid logic - customers always sign
# themselves up, confirmed decision
@router.post("", response_model=CustomerMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_customer(data: CustomerCreate, db: Session = Depends(get_db)):

    return create_customer(data, db)


@router.get("", response_model=CustomerPaginationResponse, dependencies=[Depends(require_admin)])
def list_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_customers(db=db, page=page, limit=limit, search=search, sort_by=sort_by, sort_order=sort_order)


@router.get("/{customer_id}", response_model=CustomerMessageResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return get_customer_by_id(customer_id, db)


@router.put("/{customer_id}", response_model=CustomerMessageResponse)
def update_existing_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return update_customer(customer_id, data, current_user, db)



@router.post("/addresses", response_model=AddressMessageResponse, status_code=status.HTTP_201_CREATED)
def add_address(data: AddressCreate, db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return create_address(data, current_user, db)


@router.get("/addresses", response_model=AddressListResponse)
def list_my_addresses(db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return get_addresses_for_customer(current_user, db)


@router.put("/addresses/{address_id}", response_model=AddressMessageResponse)
def update_existing_address(address_id: int, data: AddressUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return update_address(address_id, data, current_user, db)


@router.delete("/addresses/{address_id}", response_model=MessageResponse)
def remove_address(address_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return delete_address(address_id, current_user, db)