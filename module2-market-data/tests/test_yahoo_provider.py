"""Tests the Yahoo adapter with a fake `yfinance` module, so no internet is needed."""
import sys
import types
from datetime import date

import pandas as pd
import pytest

from app.providers.base import NoDataError, ProviderError
from app.providers.yahoo import YahooProvider


def install_fake_yf(monkeypatch, history=None, info=None, quotes=None, raise_on=None):
    class FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, **kw):
            if raise_on == "history":
                raise RuntimeError("boom")
            self.kw = kw
            FakeTicker.last_kwargs = kw
            return history if history is not None else pd.DataFrame()

        @property
        def info(self):
            if raise_on == "info":
                raise RuntimeError("boom")
            return info or {}

        @property
        def income_stmt(self):
            return pd.DataFrame({pd.Timestamp("2025-03-31"): [1.0]}, index=["Total Revenue"])

        @property
        def balance_sheet(self):
            raise RuntimeError("not available")

        cashflow = pd.DataFrame()

    class FakeSearch:
        def __init__(self, query, **kw):
            if raise_on == "search":
                raise RuntimeError("down")
            self.quotes = quotes or []

    mod = types.SimpleNamespace(Ticker=FakeTicker, Search=FakeSearch)
    monkeypatch.setitem(sys.modules, "yfinance", mod)
    return FakeTicker


def test_history_strips_timezone_and_asks_for_raw_prices(monkeypatch):
    idx = pd.DatetimeIndex(["2025-01-02", "2025-01-03"], tz="Asia/Kolkata")
    df = pd.DataFrame({"Open": [1, 2], "High": [2, 3], "Low": [1, 1], "Close": [2, 2],
                       "Adj Close": [2, 2], "Volume": [10, 20]}, index=idx)
    T = install_fake_yf(monkeypatch, history=df)
    out = YahooProvider().get_history("INFY.NS", date(2025, 1, 1), date(2025, 1, 31))
    assert list(out["Date"].dt.date) == [date(2025, 1, 2), date(2025, 1, 3)]
    assert out["Date"].dt.tz is None
    assert T.last_kwargs["auto_adjust"] is False       # raw OHLC, consistent price basis
    assert T.last_kwargs["end"] == "2025-02-01"         # yfinance 'end' is exclusive


def test_empty_history_is_no_data(monkeypatch):
    install_fake_yf(monkeypatch, history=pd.DataFrame())
    with pytest.raises(NoDataError):
        YahooProvider().get_history("XXXX", date(2025, 1, 1), date(2025, 1, 31))


def test_history_error_becomes_provider_error(monkeypatch):
    install_fake_yf(monkeypatch, raise_on="history")
    with pytest.raises(ProviderError):
        YahooProvider().get_history("INFY.NS", date(2025, 1, 1), date(2025, 1, 31))


def test_profile_mapping(monkeypatch):
    install_fake_yf(monkeypatch, info={
        "longName": "Infosys Limited", "sector": "Technology", "industry": "IT Services",
        "exchange": "NSI", "fullExchangeName": "NSE", "currency": "INR",
        "longBusinessSummary": "Consulting", "irrelevant": 1})
    p = YahooProvider().get_profile("INFY.NS")
    assert p["name"] == "Infosys Limited" and p["exchange"] == "NSI" and p["exchange_name"] == "NSE"
    assert "irrelevant" not in p


def test_profile_error(monkeypatch):
    install_fake_yf(monkeypatch, raise_on="info")
    with pytest.raises(ProviderError):
        YahooProvider().get_profile("INFY.NS")


def test_financials_one_failure_does_not_hide_others(monkeypatch):
    install_fake_yf(monkeypatch)
    out = YahooProvider().get_financials("INFY.NS")
    assert not out["income_statement"].empty
    assert out["balance_sheet"].empty and out["cash_flow"].empty


def test_search_mapping_and_failure(monkeypatch):
    install_fake_yf(monkeypatch, quotes=[
        {"symbol": "INFY.NS", "longname": "Infosys Limited", "exchange": "NSI", "quoteType": "EQUITY"},
        {"shortname": "no symbol"}])
    res = YahooProvider().search("infosys")
    assert res == [{"symbol": "INFY.NS", "name": "Infosys Limited", "exchange": "NSI", "quote_type": "EQUITY"}]
    install_fake_yf(monkeypatch, raise_on="search")
    with pytest.raises(ProviderError):
        YahooProvider().search("x")
