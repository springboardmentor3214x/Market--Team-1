"""Settings read from environment variables (.env supported)."""
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./market_data.db")
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if o.strip()
]
ENABLE_YAHOO_SEARCH: bool = os.getenv("ENABLE_YAHOO_SEARCH", "true").lower() == "true"

DATA_SOURCE_NAME = "Yahoo Finance (via the yfinance Python library)"
