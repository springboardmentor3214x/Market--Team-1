"""Shared dependencies. Tests replace get_provider with a fake provider."""
from app.providers.base import MarketDataProvider
from app.providers.yahoo import YahooProvider

_provider: MarketDataProvider | None = None


def get_provider() -> MarketDataProvider:
    global _provider
    if _provider is None:
        _provider = YahooProvider()
    return _provider
