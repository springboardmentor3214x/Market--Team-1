"""Tables for collected market data.

retrieved_at  = when WE downloaded the data (changes every fetch)
trade_date    = the trading day a price row belongs to (never changes)
These are kept in separate columns on purpose.
"""
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    market: Mapped[Optional[str]] = mapped_column(String(10))
    exchange: Mapped[Optional[str]] = mapped_column(String(30))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(150))
    profile_json: Mapped[Optional[dict]] = mapped_column(JSON)
    source: Mapped[Optional[str]] = mapped_column(String(150))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("symbol", "trade_date", name="uq_symbol_trade_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(30), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    adj_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(150))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    __table_args__ = (UniqueConstraint("symbol", "statement_type", name="uq_symbol_statement"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(30), index=True)
    statement_type: Mapped[str] = mapped_column(String(30))  # income_statement|balance_sheet|cash_flow
    data_json: Mapped[dict] = mapped_column(JSON)
    source: Mapped[Optional[str]] = mapped_column(String(150))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DataFetchLog(Base):
    """Audit trail: what was fetched, from where, when, and how clean it was."""

    __tablename__ = "data_fetch_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(30), index=True)
    data_type: Mapped[str] = mapped_column(String(30))  # prices|profile|financials
    source: Mapped[str] = mapped_column(String(150))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    rows_received: Mapped[Optional[int]] = mapped_column(Integer)
    rows_stored: Mapped[Optional[int]] = mapped_column(Integer)
    quality_status: Mapped[Optional[str]] = mapped_column(String(20))
    details_json: Mapped[Optional[dict]] = mapped_column(JSON)
    message: Mapped[Optional[str]] = mapped_column(Text)
