
from app.services.market_data_client import fetch_stock_history
from app.services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_historical_volatility,
)


# Fetch actual INFY data from Module 2
df = fetch_stock_history("INFY", "NSE", "1Y")

# Extract closing prices
close = df["close"]

# Calculate technical indicators
df["SMA_20"] = calculate_sma(close, 20)
df["EMA_20"] = calculate_ema(close, 20)
df["RSI_14"] = calculate_rsi(close, 14)

macd = calculate_macd(close)
df = df.join(macd)

df["Volatility"] = calculate_historical_volatility(close, 20)

# Display latest results
print("\nINFY TECHNICAL ANALYSIS")
print("=======================")
print(df[[
    "date", "close", "SMA_20", "EMA_20",
    "RSI_14", "macd", "signal", "histogram",
    "Volatility"
]].tail())

print("\nReal-data technical analysis completed!")
