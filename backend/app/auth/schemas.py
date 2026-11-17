
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Registration request
class UserRegister(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )


# Login request
class UserLogin(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128
    )


# User information returned to the frontend
class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


# Registration success response
class RegistrationResponse(BaseModel):
    message: str
    user: UserResponse

class LoginResponse(BaseModel):
    message: str
    user: UserResponse