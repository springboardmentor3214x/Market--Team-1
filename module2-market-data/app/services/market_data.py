"""The Module 2 workflow, step by step:

 resolve symbol -> fetch history -> VALIDATE -> fetch profile -> fetch financials
 -> record source + retrieval timestamp -> save to DB -> return structured result.

`retrieved_at` (when WE fetched) is always separate from each row's `date` (trading day).
"""
import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app import storage
from app.markets import (PERIOD_DAYS, SUPPORTED_MARKETS, UnsupportedSymbol, currency_for,
                         market_from_symbol, market_from_yahoo_exchange, normalize_market,
                         normalize_symbol)
from app.providers.base import MarketDataProvider, NoDataError, ProviderError
from app.services.financials import STATEMENT_LABELS, statement_to_dict
from app.services.validation import df_to_rows, validate_ohlcv

log = logging.getLogger(__name__)
SYMBOL_RE = re.compile(r"^[A-Z0-9.\-&^=]{1,20}$")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_period(period: str) -> str:
    p = (period or "").strip().upper()
    if p not in PERIOD_DAYS:
        raise ValueError(f"Invalid period '{period}'. Choose one of: {', '.join(PERIOD_DAYS)}")
    return p


def resolve_symbol(symbol: str, market: Optional[str]) -> tuple[str, Optional[str]]:
    """-> (clean provider symbol, market if known from the suffix or the user's choice)"""
    mkt = normalize_market(market)
    sym = normalize_symbol(symbol, mkt)
    if not SYMBOL_RE.match(sym):
        raise ValueError(f"'{symbol}' is not a valid ticker symbol.")
    from_suffix = market_from_symbol(sym)  # raises UnsupportedSymbol for other exchanges
    if mkt in ("NSE", "BSE") and from_suffix and from_suffix != mkt:
        raise ValueError(f"Ticker {sym} does not belong to the {mkt} market.")
    return sym, from_suffix or mkt


def make_metadata(provider: MarketDataProvider, symbol: str, retrieved_at: datetime, **extra) -> dict:
    return {
        "source": provider.name,
        "source_url": provider.quote_url(symbol),
        "retrieved_at": retrieved_at.isoformat(),
        "note": "retrieved_at is when this data was downloaded. "
                "Each price row's 'date' is the trading day it belongs to.",
        **extra,
    }


def _persist(fn, *args, **kwargs) -> None:
    """Saving is best-effort: a database problem must never hide good data from the user."""
    try:
        fn(*args, **kwargs)
    except Exception:  # noqa: BLE001
        log.exception("Could not save to the database")


# ------------------------------------------------------------------ history
def history_block(provider: MarketDataProvider, db: Session, symbol: str, period: str) -> dict:
    period = parse_period(period)
    end = date.today()
    start = end - timedelta(days=PERIOD_DAYS[period])
    retrieved_at = now_utc()

    raw = provider.get_history(symbol, start, end)  # may raise NoDataError / ProviderError
    clean, report = validate_ohlcv(raw, today=end)
    rows = df_to_rows(clean)

    stored = 0
    if report["status"] != "unusable":
        try:
            stored = storage.save_prices(db, symbol, clean, provider.name, retrieved_at)
        except Exception:  # noqa: BLE001
            db.rollback()
            log.exception("Could not save prices")
    _persist(storage.log_fetch, db, symbol, "prices", provider.name, retrieved_at,
             report["rows_received"], stored, report["status"],
             {"issues": [{k: i[k] for k in ("type", "count", "action")} for i in report["issues"]]})

    return {
        "symbol": symbol,
        "period": period,
        "interval": "1d",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "row_count": len(rows),
        "first_trading_date": rows[0]["date"] if rows else None,
        "last_trading_date": rows[-1]["date"] if rows else None,
        "columns": ["date", "open", "high", "low", "close", "adj_close", "volume"],
        "price_basis": "open/high/low/close are raw (unadjusted); adj_close is split/dividend adjusted",
        "rows": rows,
        "validation": report,
        "metadata": make_metadata(provider, symbol, retrieved_at),
    }


# ------------------------------------------------------------------ profile
def profile_block(provider: MarketDataProvider, db: Session, symbol: str,
                  market_hint: Optional[str]) -> dict:
    retrieved_at = now_utc()
    try:
        data = provider.get_profile(symbol)
        error = None
    except ProviderError as exc:
        data, error = {}, str(exc)

    if "." in symbol:  # .NS / .BO already tell us the market
        market = market_hint
    elif data:  # plain US ticker: trust the exchange Yahoo reports (NYSE vs Nasdaq)
        market = market_from_yahoo_exchange(data.get("exchange"))
    else:
        market = market_hint
    if data:
        data["market"] = market
        data["currency"] = currency_for(market, data.get("currency"))
        _persist(storage.upsert_company, db, symbol,
                 {**data, "exchange": data.get("exchange_name") or data.get("exchange"),
                  "profile_json": data}, provider.name, retrieved_at)
    _persist(storage.log_fetch, db, symbol, "profile", provider.name, retrieved_at,
             quality_status="available" if data else "unavailable", message=error)
    return {
        "available": bool(data),
        "data": data or None,
        "message": None if data else (error or "Company profile is not available from the data source."),
        "metadata": make_metadata(provider, symbol, retrieved_at),
    }


# --------------------------------------------------------------- financials
def financials_block(provider: MarketDataProvider, db: Session, symbol: str) -> dict:
    retrieved_at = now_utc()
    try:
        frames = provider.get_financials(symbol)
        error = None
    except ProviderError as exc:
        frames, error = {}, str(exc)

    statements, available_count = {}, 0
    for key, label in STATEMENT_LABELS.items():
        d = statement_to_dict(frames.get(key))
        if d:
            available_count += 1
            _persist(storage.save_statement, db, symbol, key, d, provider.name, retrieved_at)
        statements[key] = {
            "label": label,
            "available": d is not None,
            "periods": d["periods"] if d else [],
            "items": d["items"] if d else {},
            "message": None if d else f"{label} is not available for this company.",
        }
    _persist(storage.log_fetch, db, symbol, "financials", provider.name, retrieved_at,
             rows_received=available_count, quality_status=f"{available_count}/3 statements",
             message=error)
    return {
        "available": available_count > 0,
        "statements_available": available_count,
        "statements": statements,
        "message": error,
        "metadata": make_metadata(provider, symbol, retrieved_at,
                                  frequency="annual (as provided by the source)"),
    }


# ----------------------------------------------------------------- overview
def overview(provider: MarketDataProvider, db: Session, symbol_in: str,
             market_in: Optional[str], period: str) -> dict:
    symbol, market = resolve_symbol(symbol_in, market_in)
    warnings: list[str] = []

    history = history_block(provider, db, symbol, period)  # NoDataError -> 404 (unknown ticker)
    profile = profile_block(provider, db, symbol, market)
    market = (profile["data"] or {}).get("market") or market

    if "." not in symbol and market is None and profile["data"] is not None:
        raise UnsupportedSymbol(
            f"'{symbol}' does not trade on NYSE or Nasdaq (exchange: "
            f"{profile['data'].get('exchange_name') or profile['data'].get('exchange') or 'unknown'}). "
            "Supported markets: NSE, BSE, NYSE, Nasdaq.")

    financials = financials_block(provider, db, symbol)

    if history["validation"]["status"] == "unusable":
        warnings.append("All price rows failed validation, so no usable price data is available.")
    elif history["validation"]["rows_removed"]:
        warnings.append(f"{history['validation']['rows_removed']} price row(s) were removed during validation.")
    if not profile["available"]:
        warnings.append("Company profile is not available.")
    if financials["statements_available"] < 3:
        warnings.append("Some financial statements are not available for this company.")
    if market is None:
        warnings.append("Could not confirm the exchange; supported markets are NSE, BSE, NYSE and Nasdaq.")

    pdata = profile["data"] or {}
    return {
        "company": {
            "symbol": symbol,
            "name": pdata.get("name"),
            "market": market,
            "exchange": pdata.get("exchange_name") or pdata.get("exchange")
                        or (SUPPORTED_MARKETS[market]["name"] if market in SUPPORTED_MARKETS else None),
            "currency": currency_for(market, pdata.get("currency")),
            "sector": pdata.get("sector"),
            "industry": pdata.get("industry"),
        },
        "profile": profile,
        "history": history,
        "financials": financials,
        "warnings": warnings,
        "generated_at": now_utc().isoformat(),
    }
