
import numpy as np
import pandas as pd

from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator

from app.services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
)


# Create controlled sample closing prices
close = pd.Series(
    np.linspace(100, 200, 100)
    + np.sin(np.arange(100)) * 5
)

# Our implementation
our_sma = calculate_sma(close, 20)
our_ema = calculate_ema(close, 20)
our_rsi = calculate_rsi(close, 14)
our_macd = calculate_macd(close)

# Independent library calculations
ta_sma = SMAIndicator(
    close=close, window=20
).sma_indicator()

ta_ema = EMAIndicator(
    close=close, window=20
).ema_indicator()

ta_rsi = RSIIndicator(
    close=close, window=14
).rsi()

ta_macd = MACD(
    close=close,
    window_fast=12,
    window_slow=26,
    window_sign=9
)

# Compare latest values
print("\nINDEPENDENT INDICATOR VALIDATION")
print("================================")

comparisons = {
    "SMA": (our_sma.iloc[-1], ta_sma.iloc[-1]),
    "EMA": (our_ema.iloc[-1], ta_ema.iloc[-1]),
    "RSI": (our_rsi.iloc[-1], ta_rsi.iloc[-1]),
    "MACD": (
        our_macd["macd"].iloc[-1],
        ta_macd.macd().iloc[-1]
    ),
    "MACD Signal": (
        our_macd["signal"].iloc[-1],
        ta_macd.macd_signal().iloc[-1]
    ),
}

for name, (ours, reference) in comparisons.items():
    difference = abs(ours - reference)

    print(f"\n{name}")
    print(f"Our result: {ours:.6f}")
    print(f"TA result:  {reference:.6f}")
    print(f"Difference: {difference:.6f}")

print("\nValidation comparison completed!")
