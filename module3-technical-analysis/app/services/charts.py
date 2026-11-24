
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


# Folder where generated charts will be stored
CHARTS_DIR = Path("outputs/charts")
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_technical_charts(df, symbol: str) -> dict:
    """
    Generate technical analysis charts using calculated indicators.
    """

    required_columns = [
        "date", "close", "SMA_20", "EMA_20",
        "RSI_14", "macd", "signal",
        "histogram", "Volatility"
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns for charts: {missing}")

    if df.empty:
        raise ValueError("No data available for chart generation.")

    data = df.copy()
    data["date"] = __import__("pandas").to_datetime(data["date"])

    chart_paths = {}

    # 1. Stock price with SMA and EMA
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(data["date"], data["close"], label="Closing Price")
    ax.plot(data["date"], data["SMA_20"], label="SMA 20")
    ax.plot(data["date"], data["EMA_20"], label="EMA 20")

    ax.set_title(f"{symbol} - Price, SMA and EMA")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()
    fig.tight_layout()

    path = CHARTS_DIR / f"{symbol}_price.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    chart_paths["price_chart"] = str(path)

    # 2. RSI chart
    fig, ax = plt.subplots(figsize=(12, 4))

    ax.plot(data["date"], data["RSI_14"], label="RSI 14")
    ax.axhline(70, linestyle="--", label="Overbought (70)")
    ax.axhline(30, linestyle="--", label="Oversold (30)")

    ax.set_title(f"{symbol} - Relative Strength Index")
    ax.set_xlabel("Date")
    ax.set_ylabel("RSI")
    ax.set_ylim(0, 100)
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()
    fig.tight_layout()

    path = CHARTS_DIR / f"{symbol}_rsi.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    chart_paths["rsi_chart"] = str(path)

    # 3. MACD chart
    fig, ax = plt.subplots(figsize=(12, 4))

    ax.plot(data["date"], data["macd"], label="MACD")
    ax.plot(data["date"], data["signal"], label="Signal")
    ax.bar(data["date"], data["histogram"], label="Histogram")

    ax.set_title(f"{symbol} - MACD")
    ax.set_xlabel("Date")
    ax.set_ylabel("MACD Value")
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()
    fig.tight_layout()

    path = CHARTS_DIR / f"{symbol}_macd.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    chart_paths["macd_chart"] = str(path)

    # 4. Historical volatility chart
    fig, ax = plt.subplots(figsize=(12, 4))

    ax.plot(
        data["date"],
        data["Volatility"] * 100,
        label="Historical Volatility"
    )

    ax.set_title(f"{symbol} - Historical Volatility")
    ax.set_xlabel("Date")
    ax.set_ylabel("Annualized Volatility (%)")
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()
    fig.tight_layout()

    path = CHARTS_DIR / f"{symbol}_volatility.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    chart_paths["volatility_chart"] = str(path)

    return chart_paths
