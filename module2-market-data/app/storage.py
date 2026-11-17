"""Save collected data to the database (SQLite by default, PostgreSQL in production)."""
from datetime import date, datetime
from typing import Optional

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Company, DataFetchLog, FinancialStatement, PriceHistory


def upsert_company(db: Session, symbol: str, fields: dict, source: str, retrieved_at: datetime) -> None:
    row = db.scalar(select(Company).where(Company.symbol == symbol))
    if row is None:
        row = Company(symbol=symbol)
        db.add(row)
    row.name = fields.get("name")
    row.market = fields.get("market")
    row.exchange = fields.get("exchange")
    row.currency = fields.get("currency")
    row.sector = fields.get("sector")
    row.industry = fields.get("industry")
    row.profile_json = fields.get("profile_json")
    row.source = source
    row.retrieved_at = retrieved_at
    db.commit()


def save_prices(db: Session, symbol: str, df: pd.DataFrame, source: str, retrieved_at: datetime) -> int:
    if df.empty:
        return 0
    lo, hi = min(df["Date"]), max(df["Date"])
    db.execute(delete(PriceHistory).where(
        PriceHistory.symbol == symbol, PriceHistory.trade_date >= lo, PriceHistory.trade_date <= hi))
    rows = []
    for r in df.itertuples(index=False):
        rows.append(PriceHistory(
            symbol=symbol, trade_date=r.Date, open=float(r.Open), high=float(r.High),
            low=float(r.Low), close=float(r.Close),
            adj_close=None if pd.isna(r[5]) else float(r[5]),
            volume=None if pd.isna(r.Volume) else int(r.Volume),
            source=source, retrieved_at=retrieved_at))
    db.add_all(rows)
    db.commit()
    return len(rows)


def save_statement(db: Session, symbol: str, statement_type: str, data: dict,
                   source: str, retrieved_at: datetime) -> None:
    row = db.scalar(select(FinancialStatement).where(
        FinancialStatement.symbol == symbol, FinancialStatement.statement_type == statement_type))
    if row is None:
        row = FinancialStatement(symbol=symbol, statement_type=statement_type)
        db.add(row)
    row.data_json = data
    row.source = source
    row.retrieved_at = retrieved_at
    db.commit()


def log_fetch(db: Session, symbol: str, data_type: str, source: str, retrieved_at: datetime,
              rows_received: Optional[int] = None, rows_stored: Optional[int] = None,
              quality_status: Optional[str] = None, details: Optional[dict] = None,
              message: Optional[str] = None) -> None:
    db.add(DataFetchLog(symbol=symbol, data_type=data_type, source=source,
                        retrieved_at=retrieved_at, rows_received=rows_received,
                        rows_stored=rows_stored, quality_status=quality_status,
                        details_json=details, message=message))
    db.commit()


def recent_logs(db: Session, symbol: str, limit: int = 20) -> list[DataFetchLog]:
    return list(db.scalars(select(DataFetchLog).where(DataFetchLog.symbol == symbol)
                           .order_by(DataFetchLog.retrieved_at.desc(), DataFetchLog.id.desc())
                           .limit(limit)))
