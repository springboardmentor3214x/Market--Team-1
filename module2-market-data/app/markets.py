"""Supported stock markets, their currency and Yahoo Finance ticker suffix.

NSE  -> RELIANCE.NS      BSE -> RELIANCE.BO      NYSE / Nasdaq -> AAPL (no suffix)
"""
from typing import Optional

SUPPORTED_MARKETS: dict[str, dict] = {
    "NSE": {"name": "National Stock Exchange of India", "currency": "INR",
            "country": "India", "suffix": ".NS"},
    "BSE": {"name": "Bombay Stock Exchange", "currency": "INR",
            "country": "India", "suffix": ".BO"},
    "NYSE": {"name": "New York Stock Exchange", "currency": "USD",
             "country": "United States", "suffix": ""},
    "NASDAQ": {"name": "Nasdaq", "currency": "USD",
               "country": "United States", "suffix": ""},
}

# Yahoo's internal exchange codes -> our market names
YAHOO_EXCHANGE_TO_MARKET: dict[str, str] = {
    "NSI": "NSE",
    "BSE": "BSE", "BOM": "BSE",
    "NYQ": "NYSE",
    "NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ",
}

# Analysis periods (same values as the Module 1 user preferences) -> days back
PERIOD_DAYS: dict[str, int] = {
    "1M": 30, "3M": 91, "6M": 182, "1Y": 365, "3Y": 1095, "5Y": 1826,
}


class UnsupportedSymbol(ValueError):
    """Ticker belongs to an exchange we don't support (e.g. London, Tokyo)."""


def normalize_market(market: Optional[str]) -> Optional[str]:
    if market is None or not market.strip():
        return None
    m = market.strip().upper()
    if m not in SUPPORTED_MARKETS:
        raise ValueError(
            f"Unsupported market '{market}'. Choose one of: {', '.join(SUPPORTED_MARKETS)}"
        )
    return m


def normalize_symbol(symbol: str, market: Optional[str] = None) -> str:
    """Upper-case the ticker and add .NS/.BO when an Indian market is selected.

    'infy' + NSE -> 'INFY.NS'   |   'RELIANCE.BO' stays as is   |   'aapl' -> 'AAPL'
    """
    s = symbol.strip().upper()
    if not s:
        raise ValueError("Ticker symbol cannot be empty")
    if "." not in s and market in ("NSE", "BSE"):
        s += SUPPORTED_MARKETS[market]["suffix"]
    return s


def market_from_symbol(symbol: str) -> Optional[str]:
    """'X.NS' -> NSE, 'X.BO' -> BSE, plain US ticker -> None (decided by exchange later).
    Raises UnsupportedSymbol for any other exchange suffix such as '.L' or '.T'."""
    s = symbol.upper()
    if s.endswith(".NS"):
        return "NSE"
    if s.endswith(".BO"):
        return "BSE"
    if "." in s:
        raise UnsupportedSymbol(
            f"'{symbol}' is not on a supported exchange. Supported: NSE (.NS), BSE (.BO), NYSE, Nasdaq."
        )
    return None


def market_from_yahoo_exchange(code: Optional[str]) -> Optional[str]:
    return YAHOO_EXCHANGE_TO_MARKET.get((code or "").upper())


def currency_for(market: Optional[str], provider_currency: Optional[str] = None) -> Optional[str]:
    if provider_currency:
        return provider_currency
    return SUPPORTED_MARKETS[market]["currency"] if market in SUPPORTED_MARKETS else None
