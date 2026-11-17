"""Yahoo Finance provider using the `yfinance` library (free, no API key).

Limitations to mention in the report: Yahoo data is unofficial, can be delayed,
and may be rate-limited. The provider interface lets us swap in another source.
"""
from datetime import date, timedelta

import pandas as pd

from app.config import DATA_SOURCE_NAME
from app.providers.base import MarketDataProvider, NoDataError, ProviderError

PROFILE_FIELDS = {
    "name": ("longName", "shortName"),
    "description": ("longBusinessSummary",),
    "sector": ("sector",),
    "industry": ("industry",),
    "website": ("website",),
    "country": ("country",),
    "city": ("city",),
    "employees": ("fullTimeEmployees",),
    "exchange": ("exchange",),
    "exchange_name": ("fullExchangeName",),
    "currency": ("currency", "financialCurrency"),
    "market_cap": ("marketCap",),
    "quote_type": ("quoteType",),
}


class YahooProvider(MarketDataProvider):
    name = DATA_SOURCE_NAME
    homepage = "https://finance.yahoo.com"

    def quote_url(self, symbol: str) -> str:
        return f"https://finance.yahoo.com/quote/{symbol}"

    @staticmethod
    def _yf():
        try:
            import yfinance as yf  # imported lazily so tests don't need network
        except ImportError as exc:  # pragma: no cover
            raise ProviderError("yfinance is not installed. Run: pip install yfinance") from exc
        return yf

    # ---------------------------------------------------------------- search
    def search(self, query: str, max_results: int = 10) -> list[dict]:
        yf = self._yf()
        try:
            res = yf.Search(query, max_results=max_results, news_count=0, lists_count=0)
            quotes = res.quotes or []
        except Exception as exc:
            raise ProviderError(f"Yahoo search failed: {exc}") from exc
        out = []
        for q in quotes:
            if not q.get("symbol"):
                continue
            out.append(
                {
                    "symbol": q["symbol"],
                    "name": q.get("longname") or q.get("shortname") or q["symbol"],
                    "exchange": q.get("exchange"),
                    "quote_type": q.get("quoteType"),
                }
            )
        return out

    # --------------------------------------------------------------- history
    def get_history(self, symbol: str, start: date, end: date, interval: str = "1d") -> pd.DataFrame:
        yf = self._yf()
        try:
            # auto_adjust=False keeps Open/High/Low/Close on one raw price basis;
            # the split/dividend-adjusted price comes separately as 'Adj Close'.
            df = yf.Ticker(symbol).history(
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),  # 'end' is exclusive in yfinance
                interval=interval,
                auto_adjust=False,
                actions=False,
            )
        except Exception as exc:
            raise ProviderError(f"Could not download prices for {symbol}: {exc}") from exc
        if df is None or df.empty:
            raise NoDataError(
                f"No price data found for '{symbol}'. Check the ticker symbol or choose the right market."
            )
        idx = pd.to_datetime(df.index)
        if getattr(idx, "tz", None) is not None:
            idx = idx.tz_localize(None)  # keep the exchange-local calendar date
        df = df.copy()
        df.index = idx
        df.index.name = "Date"
        return df.reset_index()

    # --------------------------------------------------------------- profile
    def get_profile(self, symbol: str) -> dict:
        yf = self._yf()
        try:
            info = yf.Ticker(symbol).info or {}
        except Exception as exc:
            raise ProviderError(f"Could not download company profile for {symbol}: {exc}") from exc
        profile = {}
        for key, candidates in PROFILE_FIELDS.items():
            for c in candidates:
                if info.get(c) not in (None, ""):
                    profile[key] = info[c]
                    break
        return profile

    # ------------------------------------------------------------ financials
    def get_financials(self, symbol: str) -> dict[str, pd.DataFrame]:
        yf = self._yf()
        t = yf.Ticker(symbol)
        out: dict[str, pd.DataFrame] = {}
        for key, attr in (
            ("income_statement", "income_stmt"),
            ("balance_sheet", "balance_sheet"),
            ("cash_flow", "cashflow"),
        ):
            try:
                out[key] = getattr(t, attr)
            except Exception:  # one statement failing must not hide the others
                out[key] = pd.DataFrame()
        return out
