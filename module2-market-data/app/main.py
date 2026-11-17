"""Module 2 FastAPI app.  Run with:  uvicorn app.main:app --reload --port 8001"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers tables)
from app.config import CORS_ORIGINS
from app.database import Base, engine
from app.routers import market


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Market Research Platform - Stock Search & Market Data",
    description="Module 2: company search, historical OHLCV prices, company profiles, "
                "financial statements, data validation and source/timestamp tracking.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.include_router(market.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
