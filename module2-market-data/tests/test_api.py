from sqlalchemy import func, select

from app.models import Company, DataFetchLog, FinancialStatement, PriceHistory
from tests.conftest import sample_history


def test_overview_happy_path(client, provider):
    r = client.get("/api/stocks/INFY.NS/overview", params={"period": "6M"})
    assert r.status_code == 200
    d = r.json()
    assert d["company"]["symbol"] == "INFY.NS"
    assert d["company"]["market"] == "NSE" and d["company"]["currency"] == "INR"
    assert d["company"]["name"] == "Infosys Limited"
    assert d["history"]["row_count"] == 30
    assert d["history"]["validation"]["status"] == "clean"
    assert d["financials"]["statements_available"] == 3
    assert d["warnings"] == []


def test_history_rows_have_ohlcv_fields(client):
    row = client.get("/api/stocks/INFY.NS/history").json()["rows"][0]
    assert set(row) == {"date", "open", "high", "low", "close", "adj_close", "volume"}


def test_retrieval_timestamp_separate_from_trading_date(client):
    h = client.get("/api/stocks/INFY.NS/history").json()
    assert h["metadata"]["source"] == "Fake Test Source"
    assert "retrieved_at" in h["metadata"] and "T" in h["metadata"]["retrieved_at"]
    assert "retrieved_at" not in h["rows"][0]
    assert h["rows"][0]["date"] != h["metadata"]["retrieved_at"][:10] or len(h["rows"]) > 1
    assert h["first_trading_date"] <= h["last_trading_date"]


def test_metadata_on_every_section(client):
    d = client.get("/api/stocks/INFY.NS/overview").json()
    for block in (d["profile"], d["history"], d["financials"]):
        assert block["metadata"]["source"] and block["metadata"]["retrieved_at"]


def test_nse_symbol_added_from_market_param(client):
    d = client.get("/api/stocks/infy/overview", params={"market": "NSE"}).json()
    assert d["company"]["symbol"] == "INFY.NS"


def test_us_symbol_market_from_exchange(client, provider):
    provider.profile = {"name": "Apple Inc.", "exchange": "NMS", "currency": "USD", "sector": "Technology"}
    d = client.get("/api/stocks/aapl/overview").json()
    assert d["company"]["symbol"] == "AAPL"
    assert d["company"]["market"] == "NASDAQ" and d["company"]["currency"] == "USD"
    provider.profile["exchange"] = "NYQ"
    assert client.get("/api/stocks/aapl/overview").json()["company"]["market"] == "NYSE"


def test_us_symbol_on_unsupported_exchange_rejected(client, provider):
    provider.profile = {"name": "Pink sheet co", "exchange": "PNK", "currency": "USD"}
    r = client.get("/api/stocks/ABCD/overview")
    assert r.status_code == 400 and "NYSE or Nasdaq" in r.json()["detail"]


def test_invalid_inputs(client):
    assert client.get("/api/stocks/INFY.NS/overview", params={"period": "9Y"}).status_code == 400
    assert client.get("/api/stocks/INFY.NS/overview", params={"market": "LSE"}).status_code == 400
    assert client.get("/api/stocks/VOD.L/overview").status_code == 400  # unsupported exchange
    assert client.get("/api/stocks/INFY.NS/overview", params={"market": "BSE"}).status_code == 400
    assert client.get("/api/stocks/BAD$SYMBOL/overview").status_code == 400


def test_unknown_symbol_404(client, provider):
    provider.history_df = None
    r = client.get("/api/stocks/NOPE.NS/overview")
    assert r.status_code == 404 and "No price data" in r.json()["detail"]


def test_provider_failure_502(client, provider):
    provider.fail_history = True
    r = client.get("/api/stocks/INFY.NS/overview")
    assert r.status_code == 502


def test_profile_failure_does_not_break_overview(client, provider):
    provider.fail_profile = True
    d = client.get("/api/stocks/INFY.NS/overview").json()
    assert d["profile"]["available"] is False
    assert d["history"]["row_count"] == 30
    assert any("profile" in w.lower() for w in d["warnings"])
    assert d["company"]["market"] == "NSE"  # still known from the .NS suffix


def test_missing_statements_handled(client, provider):
    provider.financials["cash_flow"] = provider.financials["cash_flow"].iloc[0:0]
    del provider.financials["balance_sheet"]
    d = client.get("/api/stocks/INFY.NS/financials").json()
    assert d["statements_available"] == 1
    assert d["statements"]["cash_flow"]["available"] is False
    assert "not available" in d["statements"]["cash_flow"]["message"]
    assert d["statements"]["income_statement"]["periods"] == ["2025-03-31", "2024-03-31"]
    assert d["statements"]["income_statement"]["items"]["Total Revenue"]["2025-03-31"] == 1000.0


def test_dirty_data_is_cleaned_in_response(client, provider):
    df = sample_history(30)
    df.loc[3, "Close"] = float("nan")
    df = __import__("pandas").concat([df, df.iloc[[7]]], ignore_index=True)
    provider.history_df = df
    h = client.get("/api/stocks/INFY.NS/history").json()
    assert h["validation"]["status"] == "cleaned"
    assert h["row_count"] == 29
    assert {"missing_prices", "duplicate_dates"} <= {i["type"] for i in h["validation"]["issues"]}
    dates = [r["date"] for r in h["rows"]]
    assert len(dates) == len(set(dates))


def test_all_rows_invalid_reports_unusable(client, provider):
    df = sample_history(5)
    df["Close"] = float("nan")
    provider.history_df = df
    d = client.get("/api/stocks/INFY.NS/overview").json()
    assert d["history"]["validation"]["status"] == "unusable"
    assert d["history"]["rows"] == []
    assert any("no usable price" in w.lower() for w in d["warnings"])


def test_data_saved_to_database(client, db):
    client.get("/api/stocks/INFY.NS/overview")
    assert db.scalar(select(func.count()).select_from(PriceHistory)) == 30
    assert db.scalar(select(func.count()).select_from(Company)) == 1
    assert db.scalar(select(func.count()).select_from(FinancialStatement)) == 3
    row = db.scalar(select(PriceHistory).order_by(PriceHistory.trade_date))
    assert row.source == "Fake Test Source" and row.retrieved_at is not None
    assert row.symbol == "INFY.NS"


def test_refetch_does_not_duplicate_rows(client, db):
    client.get("/api/stocks/INFY.NS/history")
    client.get("/api/stocks/INFY.NS/history")
    assert db.scalar(select(func.count()).select_from(PriceHistory)) == 30
    assert db.scalar(select(func.count()).select_from(DataFetchLog)
                     .where(DataFetchLog.data_type == "prices")) == 2


def test_fetch_log_endpoint(client):
    client.get("/api/stocks/INFY.NS/overview")
    log = client.get("/api/stocks/INFY.NS/fetch-log").json()
    assert {e["data_type"] for e in log["entries"]} == {"prices", "profile", "financials"}
    assert all(e["source"] and e["retrieved_at"] for e in log["entries"])


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
