
from app.services.market_data_client import fetch_stock_history
from app.services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_historical_volatility,
)
from app.services.conditions import detect_technical_conditions


# Fetch actual INFY data from Module 2
df = fetch_stock_history("INFY", "NSE", "1Y")

# Calculate indicators
close = df["close"]

df["SMA_20"] = calculate_sma(close, 20)
df["EMA_20"] = calculate_ema(close, 20)
df["RSI_14"] = calculate_rsi(close, 14)

macd = calculate_macd(close)
df = df.join(macd)

df["Volatility"] = calculate_historical_volatility(close, 20)

# Detect technical conditions
result = detect_technical_conditions(df)

# Display results
print("\nINFY TECHNICAL CONDITIONS")
print("=========================")

print("Latest date:", result["latest_date"])
print("Conditions detected:", result["condition_count"])

for condition in result["conditions_detected"]:
    print("-", condition)

print("\nTechnical condition detection completed!")
