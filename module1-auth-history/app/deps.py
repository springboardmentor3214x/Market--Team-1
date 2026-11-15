"""Shared dependencies.

TEAMMATES: protect any route with the logged-in user like this:

    from app.deps import get_current_user
    from app.models import User

    @router.get("/something")
    def something(current_user: User = Depends(get_current_user)):
        ...  # use current_user.id to scope data to this user
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    sub = decode_access_token(token)
    if sub is None or not sub.isdigit():
        raise credentials_error
    user = db.get(User, int(sub))
    if user is None:
        raise credentials_error
    return user
