from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_customer, require_any_role
from app.database import get_db
from app.models.user import User
from app.schemas.review_schema import ReviewCreate, ReviewUpdate, ReviewMessageResponse, ReviewPaginationResponse
from app.services.review_service import create_review, get_reviews_for_restaurant, update_review

router = APIRouter(prefix="/api/v1", tags=["Review Management"])


@router.post("/orders/{order_id}/review", response_model=ReviewMessageResponse, status_code=status.HTTP_201_CREATED)
def submit_review(order_id: int, data: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return create_review(order_id, data, current_user, db)


@router.get("/restaurants/{restaurant_id}/reviews", response_model=ReviewPaginationResponse, dependencies=[Depends(require_any_role)])
def list_restaurant_reviews(restaurant_id: int, page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):

    return get_reviews_for_restaurant(restaurant_id, db, page, limit)


@router.put("/reviews/{review_id}", response_model=ReviewMessageResponse)
def update_existing_review(review_id: int, data: ReviewUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_customer)):

    return update_review(review_id, data, current_user, db)