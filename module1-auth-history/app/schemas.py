"""Pydantic request/response schemas."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # bcrypt only uses the first 72 bytes, so reject longer passwords explicitly.
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes long")
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one letter and one number")
        return v


class LoginJSON(BaseModel):
    identifier: str = Field(min_length=1, description="Email or username")
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Research history ----------
class HistoryCreate(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    market: Optional[str] = Field(default=None, max_length=50)
    analysis_period: Optional[str] = Field(default=None, max_length=50)
    result_summary: Optional[str] = Field(default=None, max_length=20000)
    result_data: Optional[dict[str, Any]] = None


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    market: Optional[str]
    analysis_period: Optional[str]
    result_summary: Optional[str]
    result_data: Optional[dict[str, Any]]
    created_at: datetime


class HistoryList(BaseModel):
    items: list[HistoryOut]
    total: int
    page: int
    page_size: int
