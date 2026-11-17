"""Provider interface. Every data source (Yahoo, Alpha Vantage, ...) implements this,
so the rest of the app never depends on one specific library."""
from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class ProviderError(Exception):
    """The data source failed (network error, rate limit, bad response)."""


class NoDataError(Exception):
    """The data source worked but has nothing for this symbol / period."""


class MarketDataProvider(ABC):
    name: str = "unknown"
    homepage: str = ""

    def quote_url(self, symbol: str) -> str:
        return self.homepage

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Return raw quote dicts: symbol, name, exchange (provider code), quote_type."""

    @abstractmethod
    def get_history(self, symbol: str, start: date, end: date, interval: str = "1d") -> pd.DataFrame:
        """Raw daily prices: columns Date, Open, High, Low, Close, Adj Close, Volume.
        Prices must be on the SAME (unadjusted) basis for Open/High/Low/Close."""

    @abstractmethod
    def get_profile(self, symbol: str) -> dict:
        """Company profile fields (may be empty)."""

    @abstractmethod
    def get_financials(self, symbol: str) -> dict[str, pd.DataFrame]:
        """Keys: income_statement, balance_sheet, cash_flow. Missing ones may be absent/empty."""
