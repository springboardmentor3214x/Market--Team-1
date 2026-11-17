"""Module 2 API: stock search, prices (OHLCV), profile, financial statements."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import storage
from app.config import ENABLE_YAHOO_SEARCH
from app.database import get_db
from app.deps import get_provider
from app.markets import PERIOD_DAYS, SUPPORTED_MARKETS, normalize_market
from app.providers.base import MarketDataProvider, NoDataError, ProviderError
from app.services import market_data as svc
from app.services.search import search_companies

router = APIRouter(prefix="/api", tags=["Market Data"])


def _call(fn, *args, **kwargs):
    """Translate service errors into clean HTTP errors."""
    try:
        return fn(*args, **kwargs)
    except NoDataError as exc:
        raise HTTPException(404, str(exc))
    except ProviderError as exc:
        raise HTTPException(502, f"The market data source failed: {exc}")
    except ValueError as exc:  # bad market/period/symbol/unsupported exchange
        raise HTTPException(400, str(exc))


@router.get("/markets")
def list_markets():
    """Supported markets with their currency."""
    return {
        "markets": [{"code": k, **v} for k, v in SUPPORTED_MARKETS.items()],
        "periods": list(PERIOD_DAYS),
    }


@router.get("/search")
def search(
    q: str = Query(..., description="Company name or ticker, e.g. 'Infosys' or 'INFY'"),
    market: Optional[str] = Query(None, description="NSE, BSE, NYSE or NASDAQ"),
    limit: int = Query(10, ge=1, le=25),
    provider: MarketDataProvider = Depends(get_provider),
):
    def run():
        result = search_companies(provider, q, normalize_market(market), limit,
                                  use_provider=ENABLE_YAHOO_SEARCH)
        if result["count"] == 0:
            raise NoDataError(
                f"No company found for '{q}'. Check the spelling or try the ticker symbol "
                f"(supported markets: NSE, BSE, NYSE, Nasdaq)."
            )
        return result

    return _call(run)


@router.get("/stocks/{symbol}/overview")
def stock_overview(
    symbol: str,
    market: Optional[str] = None,
    period: str = "1Y",
    provider: MarketDataProvider = Depends(get_provider),
    db: Session = Depends(get_db),
):
    """Everything the frontend needs for one company: profile + validated OHLCV +
    financial statements, each with its source and retrieval timestamp."""
    return _call(svc.overview, provider, db, symbol, market, period)


@router.get("/stocks/{symbol}/history")
def stock_history(
    symbol: str,
    market: Optional[str] = None,
    period: str = "1Y",
    provider: MarketDataProvider = Depends(get_provider),
    db: Session = Depends(get_db),
):
    def run():
        sym, _ = svc.resolve_symbol(symbol, market)
        return svc.history_block(provider, db, sym, period)

    return _call(run)


@router.get("/stocks/{symbol}/profile")
def stock_profile(
    symbol: str,
    market: Optional[str] = None,
    provider: MarketDataProvider = Depends(get_provider),
    db: Session = Depends(get_db),
):
    def run():
        sym, mkt = svc.resolve_symbol(symbol, market)
        return svc.profile_block(provider, db, sym, mkt)

    return _call(run)


@router.get("/stocks/{symbol}/financials")
def stock_financials(
    symbol: str,
    market: Optional[str] = None,
    provider: MarketDataProvider = Depends(get_provider),
    db: Session = Depends(get_db),
):
    def run():
        sym, _ = svc.resolve_symbol(symbol, market)
        return svc.financials_block(provider, db, sym)

    return _call(run)


@router.get("/stocks/{symbol}/fetch-log")
def fetch_log(symbol: str, market: Optional[str] = None, db: Session = Depends(get_db)):
    """Audit trail of what was downloaded, from where, and when."""
    sym, _ = _call(svc.resolve_symbol, symbol, market)
    return {
        "symbol": sym,
        "entries": [
            {"data_type": l.data_type, "source": l.source,
             "retrieved_at": l.retrieved_at.isoformat(), "rows_received": l.rows_received,
             "rows_stored": l.rows_stored, "quality_status": l.quality_status,
             "message": l.message}
            for l in storage.recent_logs(db, sym)
        ],
    }
