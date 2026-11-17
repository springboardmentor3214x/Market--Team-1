from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.schemas import LoginResponse, UserLogin
from app.auth.security import verify_password

from app.database.connection import get_db
from app.database.models import User
from app.auth.schemas import UserRegister, RegistrationResponse
from app.auth.security import hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegistrationResponse, status_code=201)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):

    # Check whether the email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    # Hash the password before storing it
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user": new_user
    }

@router.post("/login", response_model=LoginResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):

    # Find user by email
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    # Check email and password
    if not user or not verify_password(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "message": "Login successful",
        "user": user
    }