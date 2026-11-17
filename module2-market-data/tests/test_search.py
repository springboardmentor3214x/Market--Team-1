import pytest

from app.markets import (UnsupportedSymbol, market_from_symbol, normalize_market,
                         normalize_symbol)
from app.providers.base import NoDataError
from app.services.search import search_companies


def syms(res):
    return [r["symbol"] for r in res["results"]]


def test_search_by_exact_ticker(provider):
    res = search_companies(provider, "INFY")
    assert syms(res)[0] == "INFY.NS"
    assert "INFY.BO" in syms(res)


def test_search_by_company_name(provider):
    assert syms(search_companies(provider, "Infosys"))[0].startswith("INFY")
    assert syms(search_companies(provider, "Tata Consultancy Services"))[0].startswith("TCS")
    assert syms(search_companies(provider, "reliance industries"))[0].startswith("RELIANCE")


def test_search_us_companies(provider):
    assert syms(search_companies(provider, "Apple"))[0] == "AAPL"
    assert syms(search_companies(provider, "MSFT"))[0] == "MSFT"
    assert syms(search_companies(provider, "microsoft"))[0] == "MSFT"


def test_search_is_case_and_space_insensitive(provider):
    assert syms(search_companies(provider, "  iNfY  "))[0] == "INFY.NS"


def test_typo_tolerance(provider):
    assert syms(search_companies(provider, "infosis"))[0].startswith("INFY")
    assert syms(search_companies(provider, "relience"))[0].startswith("RELIANCE")


def test_search_with_full_symbol(provider):
    assert syms(search_companies(provider, "reliance.bo"))[0] == "RELIANCE.BO"


def test_market_filter(provider):
    res = search_companies(provider, "INFY", market="BSE")
    assert syms(res) == ["INFY.BO"]
    res = search_companies(provider, "Apple", market="NSE")
    assert res["count"] == 0


def test_results_carry_market_and_currency(provider):
    r = search_companies(provider, "INFY")["results"][0]
    assert r["market"] == "NSE" and r["currency"] == "INR"
    a = search_companies(provider, "AAPL")["results"][0]
    assert a["market"] == "NASDAQ" and a["currency"] == "USD"


def test_yahoo_results_added_and_filtered(provider):
    provider.search_results = [
        {"symbol": "TATAPOWER.NS", "name": "Tata Power Company Limited", "exchange": "NSI", "quote_type": "EQUITY"},
        {"symbol": "TATAPOWER.L", "name": "Some London listing", "exchange": "LSE", "quote_type": "EQUITY"},
        {"symbol": "TATAETF.NS", "name": "An ETF", "exchange": "NSI", "quote_type": "ETF"},
    ]
    res = search_companies(provider, "tata power")
    assert "TATAPOWER.NS" in syms(res)
    assert "TATAPOWER.L" not in syms(res) and "TATAETF.NS" not in syms(res)


def test_duplicates_removed(provider):
    provider.search_results = [
        {"symbol": "INFY.NS", "name": "Infosys", "exchange": "NSI", "quote_type": "EQUITY"}]
    assert syms(search_companies(provider, "INFY")).count("INFY.NS") == 1


def test_provider_failure_falls_back_with_warning(provider):
    provider.fail_search = True
    res = search_companies(provider, "Infosys")
    assert syms(res)[0].startswith("INFY")
    assert res["warnings"]


@pytest.mark.parametrize("bad", ["", "   ", "!!!", "x" * 100])
def test_invalid_queries_rejected(provider, bad):
    with pytest.raises(ValueError):
        search_companies(provider, bad)


def test_unknown_company_returns_nothing(provider):
    assert search_companies(provider, "zzqqxxnothing")["count"] == 0


def test_symbol_helpers():
    assert normalize_symbol("infy", "NSE") == "INFY.NS"
    assert normalize_symbol("infy", "BSE") == "INFY.BO"
    assert normalize_symbol("aapl", "NASDAQ") == "AAPL"
    assert normalize_symbol("reliance.bo", "NSE") == "RELIANCE.BO"
    assert market_from_symbol("INFY.NS") == "NSE" and market_from_symbol("AAPL") is None
    with pytest.raises(UnsupportedSymbol):
        market_from_symbol("VOD.L")
    assert normalize_market("nasdaq") == "NASDAQ" and normalize_market("") is None
    with pytest.raises(ValueError):
        normalize_market("LSE")


# ---- API level
def test_api_search_ok(client):
    r = client.get("/api/search", params={"q": "Infosys"})
    assert r.status_code == 200 and r.json()["results"][0]["symbol"] == "INFY.NS"


def test_api_search_not_found_message(client):
    r = client.get("/api/search", params={"q": "zzqqxxnothing"})
    assert r.status_code == 404 and "No company found" in r.json()["detail"]


def test_api_search_bad_input(client):
    assert client.get("/api/search", params={"q": "   "}).status_code == 400
    assert client.get("/api/search", params={"q": "inf", "market": "LSE"}).status_code == 400
    assert client.get("/api/search").status_code == 422


def test_api_markets(client):
    body = client.get("/api/markets").json()
    assert {m["code"] for m in body["markets"]} == {"NSE", "BSE", "NYSE", "NASDAQ"}
    assert body["periods"] == ["1M", "3M", "6M", "1Y", "3Y", "5Y"]
