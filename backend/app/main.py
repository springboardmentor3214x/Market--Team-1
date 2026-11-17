from fastapi import FastAPI

from app.auth.routes import router as auth_router
from app.database.connection import Base, engine
from app.database import models

# Create database tables for initial development
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stock Research Analyst API",
    description="User registration and login services",
    version="1.0.0"
)

app.include_router(auth_router)


@app.get("/")
def home():
    return {"message": "Stock Research Analyst API is running"}