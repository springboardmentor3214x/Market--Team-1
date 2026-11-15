"""Registration, login (form + JSON) and current-user endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginJSON, Token, UserCreate, UserOut
from app.security import DUMMY_HASH, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _authenticate(db: Session, identifier: str, password: str) -> User:
    ident = identifier.strip().lower()
    user = db.scalar(
        select(User).where(
            or_(func.lower(User.email) == ident, func.lower(User.username) == ident)
        )
    )
    if user is None:
        verify_password(password, DUMMY_HASH)  # equalise timing
        ok = False
    else:
        ok = verify_password(password, user.hashed_password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    if db.scalar(
        select(User.id).where(func.lower(User.username) == payload.username.lower())
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")

    user = User(
        email=email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two requests racing for the same email/username
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Email or username already registered"
        )
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Form-encoded login (used by the Swagger 'Authorize' button).
    The `username` field accepts either the email or the username."""
    user = _authenticate(db, form.username, form.password)
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/login-json", response_model=Token)
def login_json(payload: LoginJSON, db: Session = Depends(get_db)):
    """JSON login, convenient for the React frontend."""
    user = _authenticate(db, payload.identifier, payload.password)
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
