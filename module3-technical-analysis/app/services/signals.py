
import pandas as pd


def generate_signals(df: pd.DataFrame) -> dict:
    """
    Generate technical signals using the latest indicator values.
    """

    if df.empty:
        raise ValueError("No data available for signal generation.")

    required_columns = [
        "close", "SMA_20", "EMA_20", "RSI_14",
        "macd", "signal", "histogram", "Volatility"
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Missing indicator columns: {missing}")

    latest = df.iloc[-1]

    if latest[required_columns].isnull().any():
        raise ValueError("Latest indicator values contain missing data.")

    signals = {}

    # 1. Price compared with SMA
    signals["sma"] = (
        "bullish" if latest["close"] > latest["SMA_20"]
        else "bearish" if latest["close"] < latest["SMA_20"]
        else "neutral"
    )

    # 2. Price compared with EMA
    signals["ema"] = (
        "bullish" if latest["close"] > latest["EMA_20"]
        else "bearish" if latest["close"] < latest["EMA_20"]
        else "neutral"
    )

    # 3. RSI momentum
    if latest["RSI_14"] > 50:
        signals["rsi"] = "bullish"
    elif latest["RSI_14"] < 50:
        signals["rsi"] = "bearish"
    else:
        signals["rsi"] = "neutral"

    # RSI overbought / oversold conditions
    if latest["RSI_14"] > 70:
        rsi_condition = "overbought"
    elif latest["RSI_14"] < 30:
        rsi_condition = "oversold"
    else:
        rsi_condition = "normal"

    # 4. MACD compared with signal line
    signals["macd"] = (
        "bullish" if latest["macd"] > latest["signal"]
        else "bearish" if latest["macd"] < latest["signal"]
        else "neutral"
    )

    # 5. Overall assessment
    bullish_count = list(signals.values()).count("bullish")
    bearish_count = list(signals.values()).count("bearish")

    if bullish_count > bearish_count:
        overall = "bullish"
    elif bearish_count > bullish_count:
        overall = "bearish"
    else:
        overall = "neutral"

    return {
        "latest_price": round(float(latest["close"]), 2),
        "individual_signals": signals,
        "rsi_condition": rsi_condition,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "overall_signal": overall,
        "historical_volatility": round(
            float(latest["Volatility"]), 4
        )
    }
