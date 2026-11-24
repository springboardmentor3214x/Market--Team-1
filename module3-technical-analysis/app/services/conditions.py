
import pandas as pd


def detect_technical_conditions(df: pd.DataFrame) -> dict:
    """
    Detect technical events using indicator values
    from the latest and previous trading records.
    """

    if len(df) < 2:
        raise ValueError(
            "At least two records are required to detect conditions."
        )

    required_columns = [
        "close", "SMA_20", "EMA_20", "RSI_14",
        "macd", "signal"
    ]

    missing = [
        col for col in required_columns if col not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    if df[required_columns].tail(2).isnull().any().any():
        raise ValueError(
            "Latest or previous indicator values contain missing data."
        )

    conditions = []

    # 1. RSI conditions
    if latest["RSI_14"] > 70:
        conditions.append("RSI is overbought")
    elif latest["RSI_14"] < 30:
        conditions.append("RSI is oversold")

    # 2. MACD crossover detection
    if (
        previous["macd"] <= previous["signal"]
        and latest["macd"] > latest["signal"]
    ):
        conditions.append("Bullish MACD crossover")

    elif (
        previous["macd"] >= previous["signal"]
        and latest["macd"] < latest["signal"]
    ):
        conditions.append("Bearish MACD crossover")

    # 3. Price crossing SMA
    if (
        previous["close"] <= previous["SMA_20"]
        and latest["close"] > latest["SMA_20"]
    ):
        conditions.append("Price crossed above SMA 20")

    elif (
        previous["close"] >= previous["SMA_20"]
        and latest["close"] < latest["SMA_20"]
    ):
        conditions.append("Price crossed below SMA 20")

    # 4. Price crossing EMA
    if (
        previous["close"] <= previous["EMA_20"]
        and latest["close"] > latest["EMA_20"]
    ):
        conditions.append("Price crossed above EMA 20")

    elif (
        previous["close"] >= previous["EMA_20"]
        and latest["close"] < latest["EMA_20"]
    ):
        conditions.append("Price crossed below EMA 20")

    # 5. SMA and EMA crossover
    if (
        previous["SMA_20"] <= previous["EMA_20"]
        and latest["SMA_20"] > latest["EMA_20"]
    ):
        conditions.append("SMA crossed above EMA")

    elif (
        previous["SMA_20"] >= previous["EMA_20"]
        and latest["SMA_20"] < latest["EMA_20"]
    ):
        conditions.append("SMA crossed below EMA")

    if not conditions:
        conditions.append("No major technical event detected")

    return {
        "latest_date": str(latest["date"].date())
        if "date" in df.columns and pd.notna(latest["date"])
        else None,
        "conditions_detected": conditions,
        "condition_count": len(conditions)
        if conditions != ["No major technical event detected"]
        else 0
    }
