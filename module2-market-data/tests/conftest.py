import os
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:///./test_market_data.db"
os.environ["ENABLE_YAHOO_SEARCH"] = "true"

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.deps import get_provider  # noqa: E402
from app.main import app  # noqa: E402
from app.providers.base import MarketDataProvider, NoDataError, ProviderError  # noqa: E402


def business_days(n: int, end: date | None = None) -> list[date]:
    end = end or date.today()
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return sorted(out)


def sample_history(n: int = 30) -> pd.DataFrame:
    days = business_days(n)
    close = 100 + np.arange(n, dtype=float)
    return pd.DataFrame({
        "Date": pd.to_datetime(days),
        "Open": close - 0.5, "High": close + 1.0, "Low": close - 1.0, "Close": close,
        "Adj Close": close - 0.2, "Volume": np.full(n, 50_000.0),
    })


def statement(items: dict) -> pd.DataFrame:
    cols = pd.to_datetime(["2025-03-31", "2024-03-31"])
    return pd.DataFrame({c: [v[i] for v in items.values()] for i, c in enumerate(cols)},
                        index=list(items))


class FakeProvider(MarketDataProvider):
    name = "Fake Test Source"
    homepage = "https://example.test"

    def __init__(self):
        self.history_df = sample_history()
        self.profile = {"name": "Infosys Limited", "sector": "Technology",
                        "industry": "IT Services", "exchange": "NSI",
                        "exchange_name": "NSE", "currency": "INR"}
        self.financials = {
            "income_statement": statement({"Total Revenue": [1000.0, 900.0], "Net Income": [200.0, 150.0]}),
            "balance_sheet": statement({"Total Assets": [5000.0, 4500.0]}),
            "cash_flow": statement({"Operating Cash Flow": [300.0, 280.0]}),
        }
        self.search_results = []
        self.fail_search = False
        self.fail_history = False
        self.fail_profile = False
        self.history_calls = 0

    def search(self, query, max_results=10):
        if self.fail_search:
            raise ProviderError("network down")
        return self.search_results

    def get_history(self, symbol, start, end, interval="1d"):
        self.history_calls += 1
        if self.fail_history:
            raise ProviderError("rate limited")
        if self.history_df is None:
            raise NoDataError(f"No price data found for '{symbol}'.")
        return self.history_df.copy()

    def get_profile(self, symbol):
        if self.fail_profile:
            raise ProviderError("profile failed")
        return dict(self.profile)

    def get_financials(self, symbol):
        return {k: v.copy() for k, v in self.financials.items()}


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def provider():
    p = FakeProvider()
    app.dependency_overrides[get_provider] = lambda: p
    yield p
    app.dependency_overrides.clear()


@pytest.fixture
def client(provider):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()
