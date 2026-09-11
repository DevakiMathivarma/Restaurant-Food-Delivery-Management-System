# app/auth/current_user.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User
from app.utils.jwt import verify_token_type

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials."
    )

    try:

        payload = verify_token_type(token, expected_type="access")

        email = payload.get("sub")

        if not email:

            raise credentials_exception

    except JWTError:

        raise credentials_exception

    # eager-load customer and delivery_partner profiles here, at the one
    # place every authenticated request passes through - avoids a
    # separate lazy-load query every time a service accesses
    # current_user.customer or current_user.delivery_partner
    user = (
        db.query(User)
        .options(joinedload(User.customer), joinedload(User.delivery_partner))
        .filter(User.email == email)
        .first()
    )

    if not user:

        raise credentials_exception

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated."
        )

    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> User | None:

    if not token:

        return None

    try:

        return get_current_user(token=token, db=db)

    except HTTPException:

        return None