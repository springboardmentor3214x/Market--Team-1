
from app.services.market_data_client import fetch_stock_history

from app.services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_historical_volatility,
)

from app.services.signals import generate_signals
from app.services.conditions import detect_technical_conditions


def run_technical_analysis(
    symbol: str,
    market: str = "NSE",
    period: str = "1Y"
) -> dict:
    """
    Run the complete technical analysis workflow.

    1. Fetch real historical data from Module 2.
    2. Preserve data validation and source metadata.
    3. Calculate technical indicators.
    4. Generate technical signals.
    5. Detect technical conditions.
    6. Return a structured analysis result.
    """

    # Step 1: Fetch real historical data
    df = fetch_stock_history(symbol, market, period)

    # Step 2: Validate minimum records
    if len(df) < 30:
        raise ValueError(
            "Insufficient historical data for technical analysis."
        )

    close = df["close"]

    # Step 3: Calculate technical indicators
    df["SMA_20"] = calculate_sma(close, 20)

    df["EMA_12"] = calculate_ema(close, 12)
    df["EMA_20"] = calculate_ema(close, 20)
    df["EMA_26"] = calculate_ema(close, 26)

    df["RSI_14"] = calculate_rsi(close, 14)

    macd = calculate_macd(close)

    # Preserve metadata before joining MACD
    saved_attrs = df.attrs.copy()

    df = df.join(macd)

    # Restore metadata after joining
    df.attrs.update(saved_attrs)

    df["Volatility"] = calculate_historical_volatility(
        close, 20
    )

    # Step 4: Generate technical signals
    signals = generate_signals(df)

    # Step 5: Detect technical conditions
    conditions = detect_technical_conditions(df)

    # Step 6: Prepare latest indicator values
    latest = df.iloc[-1]

    indicators = {
        "close": round(float(latest["close"]), 2),
        "sma_20": round(float(latest["SMA_20"]), 2),
        "ema_12": round(float(latest["EMA_12"]), 2),
        "ema_20": round(float(latest["EMA_20"]), 2),
        "ema_26": round(float(latest["EMA_26"]), 2),
        "rsi_14": round(float(latest["RSI_14"]), 2),
        "macd": round(float(latest["macd"]), 4),
        "macd_signal": round(float(latest["signal"]), 4),
        "macd_histogram": round(float(latest["histogram"]), 4),
        "historical_volatility": round(
            float(latest["Volatility"]), 4
        )
    }

    # Step 7: Extract Module 2 validation information
    validation = df.attrs.get("validation", {})
    metadata = df.attrs.get("metadata", {})

    data_quality = {
        "validation_status": validation.get("status", "unknown"),
        "rows_received": validation.get("rows_received", len(df)),
        "rows_valid": validation.get("rows_valid", len(df)),
        "rows_removed": validation.get("rows_removed", 0),
        "issue_count": validation.get("issue_count", 0),
        "issues": validation.get("issues", []),
        "data_source": metadata.get("source", "unknown"),
        "source_url": metadata.get("source_url"),
        "retrieved_at": metadata.get("retrieved_at"),
    }

    # Step 8: Return complete analysis
    return {
        "symbol": str(df.attrs.get("symbol", symbol)),
        "market": df.attrs.get("market", market),
        "period": df.attrs.get("period", period),
        "latest_date": str(latest["date"].date()),
        "records_analyzed": len(df),
        "indicators": indicators,
        "signals": signals,
        "technical_conditions": conditions,
        "data_quality": data_quality,
        "analysis_status": "completed"
    }
