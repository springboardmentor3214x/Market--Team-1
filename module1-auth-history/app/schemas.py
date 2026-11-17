
"""Pydantic request/response schemas."""
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
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


# ---------- Saved Stocks and Watchlist ----------

class WatchlistCreate(BaseModel):
    stock_symbol: str = Field(min_length=1, max_length=20)
    market: str = Field(default="NSE", min_length=1, max_length=20)

    @field_validator("stock_symbol", "market")
    @classmethod
    def validate_not_empty(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("This field cannot be empty")
        return value


class WatchlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    stock_symbol: str
    market: str
    created_at: datetime


# ---------- User preferences ----------

Market = Literal["NSE", "BSE", "NYSE", "NASDAQ"]
AnalysisPeriod = Literal["1M", "3M", "6M", "1Y", "3Y", "5Y"]

DEFAULT_MARKET = "NSE"
DEFAULT_PERIOD = "1Y"


class PreferenceUpdate(BaseModel):
    preferred_market: Market
    analysis_period: AnalysisPeriod

    @field_validator("preferred_market", mode="before")
    @classmethod
    def normalise_market(cls, v):
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("analysis_period", mode="before")
    @classmethod
    def normalise_period(cls, v):
        return v.strip().upper() if isinstance(v, str) else v


class PreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    preferred_market: str
    analysis_period: str
    updated_at: Optional[datetime] = None
    is_default: bool = False
