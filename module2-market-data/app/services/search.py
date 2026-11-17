"""Company search by NAME or TICKER.

1. Score the built-in list (exact ticker > exact name > prefix > contains > fuzzy typo match).
2. Ask Yahoo Finance search for anything else.
3. Keep only equities on NSE / BSE / NYSE / Nasdaq, remove duplicates, rank, return.
"""
import re
from difflib import SequenceMatcher
from typing import Optional

from app.markets import SUPPORTED_MARKETS, currency_for, market_from_yahoo_exchange
from app.providers.base import MarketDataProvider, ProviderError
from app.services.universe import UNIVERSE

MAX_QUERY_LEN = 60


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9&. ]+", " ", text.lower()).strip()


def _score(q: str, entry: dict) -> int:
    ticker = entry["ticker"].lower()
    symbol = entry["symbol"].lower()
    names = [_norm(entry["name"])] + [_norm(a) for a in entry["aliases"]]
    short_name = _norm(re.sub(r"\b(limited|ltd|inc|corporation|corp|company|co)\b\.?", "", entry["name"].lower()))
    names.append(short_name.strip())

    if q in (ticker, symbol):
        return 100
    if q in names:
        return 95
    if len(q) >= 2 and ticker.startswith(q):
        return 85
    if any(n.startswith(q) for n in names):
        return 80
    if len(q) >= 3 and any(q in n for n in names):
        return 65
    best = 0.0
    if len(q) >= 4:  # typo tolerance: "infosis" -> Infosys, "relience" -> Reliance
        for n in names:
            for token in [n] + n.split():
                best = max(best, SequenceMatcher(None, q, token).ratio())
        if best >= 0.78:
            return int(best * 60)
    return 0


def _local_results(q: str, market: Optional[str]) -> list[dict]:
    scored = []
    for e in UNIVERSE:
        if market and e["market"] != market:
            continue
        s = _score(q, e)
        if s:
            scored.append((s, e))
    scored.sort(key=lambda x: (-x[0], x[1]["market"] != "NSE", x[1]["symbol"]))
    return [
        {"symbol": e["symbol"], "name": e["name"], "market": e["market"],
         "exchange": SUPPORTED_MARKETS[e["market"]]["name"], "currency": e["currency"],
         "type": "EQUITY", "source": "built-in list", "score": s}
        for s, e in scored
    ]


def search_companies(
    provider: MarketDataProvider,
    query: str,
    market: Optional[str] = None,
    limit: int = 10,
    use_provider: bool = True,
) -> dict:
    raw = (query or "").strip()
    if not raw:
        raise ValueError("Search text cannot be empty. Enter a company name or ticker symbol.")
    if len(raw) > MAX_QUERY_LEN:
        raise ValueError(f"Search text is too long (maximum {MAX_QUERY_LEN} characters).")
    if not re.search(r"[A-Za-z0-9]", raw):
        raise ValueError("Search text must contain letters or numbers.")

    q = _norm(raw)
    results = _local_results(q, market)
    warnings: list[str] = []

    if use_provider:
        try:
            for item in provider.search(raw, max_results=15):
                if (item.get("quote_type") or "").upper() != "EQUITY":
                    continue
                m = market_from_yahoo_exchange(item.get("exchange"))
                if m is None or (market and m != market):
                    continue
                results.append({
                    "symbol": item["symbol"], "name": item["name"], "market": m,
                    "exchange": SUPPORTED_MARKETS[m]["name"], "currency": currency_for(m),
                    "type": "EQUITY", "source": "Yahoo Finance search", "score": 50,
                })
        except ProviderError as exc:
            warnings.append(
                f"Online search is unavailable right now ({exc}). Showing matches from the built-in list only."
            )

    seen, unique = set(), []
    for r in results:  # local results come first, so they win duplicates
        if r["symbol"] not in seen:
            seen.add(r["symbol"])
            unique.append(r)
    unique.sort(key=lambda r: -r["score"])
    unique = unique[:limit]
    for r in unique:
        r.pop("score", None)

    return {"query": raw, "market_filter": market, "count": len(unique),
            "results": unique, "warnings": warnings}
