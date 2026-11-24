
from app.services.market_data_client import fetch_stock_history
from app.services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_historical_volatility,
)
from app.services.signals import generate_signals


# Fetch real INFY historical data
df = fetch_stock_history("INFY", "NSE", "1Y")

# Calculate indicators
close = df["close"]

df["SMA_20"] = calculate_sma(close, 20)
df["EMA_20"] = calculate_ema(close, 20)
df["RSI_14"] = calculate_rsi(close, 14)

macd = calculate_macd(close)
df = df.join(macd)

df["Volatility"] = calculate_historical_volatility(close, 20)

# Generate technical signals
result = generate_signals(df)

# Display the result
print("\nINFY TECHNICAL SIGNAL ANALYSIS")
print("==============================")

for key, value in result.items():
    print(f"{key}: {value}")

print("\nSignal generation completed successfully!")
