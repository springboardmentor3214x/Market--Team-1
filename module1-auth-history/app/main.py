"""FastAPI entry point.  Run with:  uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.config import CORS_ORIGINS
from app.database import Base, engine
from app.routers import auth, history, preferences


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Market Research Platform - Auth & Research Workspace",
    description="Module 1: JWT authentication, research history and user preferences.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(history.router)
app.include_router(preferences.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
