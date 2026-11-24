
from app.services.market_data_client import fetch_stock_history

from app.services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_historical_volatility,
)

from app.services.charts import generate_technical_charts


# Foreign companies and their exchanges
companies = [
    ("AAPL", "NASDAQ"),
    ("MSFT", "NASDAQ"),
    ("GOOGL", "NASDAQ"),
    ("AMZN", "NASDAQ"),
    ("META", "NASDAQ"),
    ("NVDA", "NASDAQ"),
    ("TSLA", "NASDAQ"),
    ("NFLX", "NASDAQ"),
    ("INTC", "NASDAQ"),
    ("JPM", "NYSE"),
    ("WMT", "NYSE"),
    ("KO", "NYSE"),
    ("DIS", "NYSE"),
    ("BA", "NYSE"),
    ("V", "NYSE"),
    ("XOM", "NYSE"),
    ("JNJ", "NYSE"),
    ("PG", "NYSE"),
    ("BAC", "NYSE"),
]

successful = []
failed = []

for symbol, market in companies:

    print(f"\nGenerating charts for {symbol} ({market})")
    print("=" * 50)

    try:
        # Fetch actual historical data
        df = fetch_stock_history(symbol, market, "1Y")

        if len(df) < 30:
            raise ValueError("Insufficient historical records.")

        # Calculate technical indicators
        close = df["close"]

        df["SMA_20"] = calculate_sma(close, 20)
        df["EMA_20"] = calculate_ema(close, 20)
        df["RSI_14"] = calculate_rsi(close, 14)

        macd = calculate_macd(close)
        df = df.join(macd)

        df["Volatility"] = calculate_historical_volatility(
            close, 20
        )

        # Generate four charts
        charts = generate_technical_charts(df, symbol)

        print("Charts generated successfully!")

        for chart_name, chart_path in charts.items():
            print(f"{chart_name}: {chart_path}")

        successful.append(symbol)

    except Exception as error:
        print("Chart generation failed:", error)
        failed.append(symbol)


print("\n========== FOREIGN CHART REPORT ==========")

print("Total companies:", len(companies))
print("Successful:", len(successful))
print("Failed:", len(failed))
print("Total charts generated:", len(successful) * 4)

print("\nSuccessful companies:", successful)
print("Failed companies:", failed)
