
from pydantic import BaseModel, Field
from typing import Literal


class TechnicalAnalysisRequest(BaseModel):
    symbol: str = Field(..., min_length=1)
    market: str = "NSE"
    period: str = "1Y"


class TechnicalIndicators(BaseModel):
    close: float
    sma_20: float
    ema_12: float
    ema_20: float
    ema_26: float
    rsi_14: float
    macd: float
    macd_signal: float
    macd_histogram: float
    historical_volatility: float



class TechnicalSignals(BaseModel):
    latest_price: float
    individual_signals: dict[
        str, Literal["bullish", "bearish", "neutral"]
    ]
    rsi_condition: Literal["overbought", "oversold", "normal"]
    bullish_count: int
    bearish_count: int
    overall_signal: Literal["bullish", "bearish", "neutral"]
    trend: Literal["upward", "downward", "mixed"]
    historical_volatility: float




class TechnicalConditions(BaseModel):
    latest_date: str | None
    conditions_detected: list[str]
    explanations: list[str]
    condition_count: int



class DataQuality(BaseModel):
    validation_status: str
    rows_received: int
    rows_valid: int
    rows_removed: int
    issue_count: int
    issues: list
    data_source: str
    source_url: str | None
    retrieved_at: str | None


class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    market: str
    period: str
    latest_date: str
    records_analyzed: int
    indicators: TechnicalIndicators
    signals: TechnicalSignals
    technical_conditions: TechnicalConditions
    data_quality: DataQuality
    analysis_status: str
