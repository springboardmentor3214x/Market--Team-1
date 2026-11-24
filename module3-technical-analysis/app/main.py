
from fastapi import FastAPI, HTTPException

from app.models.technical_analysis import (
    TechnicalAnalysisRequest,
    TechnicalAnalysisResponse,
)

from app.services.technical_analysis import run_technical_analysis


app = FastAPI(
    title="MarketAI - Technical Analysis Agent",
    description="API for technical stock market analysis using real historical data.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "MarketAI Technical Analysis Agent is running!",
        "status": "active",
    }


@app.post(
    "/api/technical-analysis",
    response_model=TechnicalAnalysisResponse,
)
def technical_analysis(request: TechnicalAnalysisRequest):

    try:
        result = run_technical_analysis(
            symbol=request.symbol,
            market=request.market,
            period=request.period,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )
