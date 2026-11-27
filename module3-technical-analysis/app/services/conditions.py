
import pandas as pd


def detect_technical_conditions(df: pd.DataFrame) -> dict:
    """
    Detect technical events and generate plain-language explanations.
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
    explanations = []

    # 1. RSI conditions
    if latest["RSI_14"] > 70:
        conditions.append("RSI is overbought")
        explanations.append(
            "RSI is above 70, indicating strong recent buying momentum. "
            "The stock may be approaching an overbought zone."
        )

    elif latest["RSI_14"] < 30:
        conditions.append("RSI is oversold")
        explanations.append(
            "RSI is below 30, indicating strong recent selling pressure. "
            "The stock may be approaching an oversold zone."
        )

    # 2. MACD crossover detection
    if (
        previous["macd"] <= previous["signal"]
        and latest["macd"] > latest["signal"]
    ):
        conditions.append("Bullish MACD crossover")
        explanations.append(
            "MACD moved above its signal line, indicating a possible "
            "improvement in upward momentum."
        )

    elif (
        previous["macd"] >= previous["signal"]
        and latest["macd"] < latest["signal"]
    ):
        conditions.append("Bearish MACD crossover")
        explanations.append(
            "MACD moved below its signal line, indicating a possible "
            "increase in downward momentum."
        )

    # 3. Price crossing SMA
    if (
        previous["close"] <= previous["SMA_20"]
        and latest["close"] > latest["SMA_20"]
    ):
        conditions.append("Price crossed above SMA 20")
        explanations.append(
            "The closing price moved above its 20-day simple moving "
            "average, suggesting improving short-term price strength."
        )

    elif (
        previous["close"] >= previous["SMA_20"]
        and latest["close"] < latest["SMA_20"]
    ):
        conditions.append("Price crossed below SMA 20")
        explanations.append(
            "The closing price moved below its 20-day simple moving "
            "average, suggesting weakening short-term price strength."
        )

    # 4. Price crossing EMA
    if (
        previous["close"] <= previous["EMA_20"]
        and latest["close"] > latest["EMA_20"]
    ):
        conditions.append("Price crossed above EMA 20")
        explanations.append(
            "The closing price moved above its 20-day exponential "
            "moving average, suggesting improving recent price momentum."
        )

    elif (
        previous["close"] >= previous["EMA_20"]
        and latest["close"] < latest["EMA_20"]
    ):
        conditions.append("Price crossed below EMA 20")
        explanations.append(
            "The closing price moved below its 20-day exponential "
            "moving average, suggesting weakening recent price momentum."
        )

    # 5. SMA and EMA crossover
    if (
        previous["SMA_20"] <= previous["EMA_20"]
        and latest["SMA_20"] > latest["EMA_20"]
    ):
        conditions.append("SMA crossed above EMA")
        explanations.append(
            "The 20-day simple moving average moved above the "
            "20-day exponential moving average, indicating a change "
            "in their relative price trends."
        )

    elif (
        previous["SMA_20"] >= previous["EMA_20"]
        and latest["SMA_20"] < latest["EMA_20"]
    ):
        conditions.append("SMA crossed below EMA")
        explanations.append(
            "The 20-day simple moving average moved below the "
            "20-day exponential moving average, indicating a change "
            "in their relative price trends."
        )

    if not conditions:
        conditions.append("No major technical event detected")
        explanations.append(
            "No major RSI threshold, MACD crossover, or moving-average "
            "crossover was detected in the latest trading record."
        )

    return {
        "latest_date": str(latest["date"].date())
        if "date" in df.columns and pd.notna(latest["date"])
        else None,
        "conditions_detected": conditions,
        "explanations": explanations,
        "condition_count": len(conditions)
        if conditions != ["No major technical event detected"]
        else 0
    }
