

import pandas as pd
import pytest
from app.services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_historical_volatility
)

def test_calculate_sma():
    # Sample closing prices
    prices = pd.Series([100, 110, 120, 130, 140, 150])

    # Calculate 5-day SMA
    sma = calculate_sma(prices, window=5)

    # Verify expected results
    assert sma.iloc[4] == 120
    assert sma.iloc[5] == 130

def test_calculate_ema():
    prices = pd.Series([100, 110, 120, 130, 140, 150])

    ema = calculate_ema(prices, window=5)

    # EMA should begin after 5 observations
    assert pd.isna(ema.iloc[3])
    assert not pd.isna(ema.iloc[4])

    # EMA should react to the latest price
    assert ema.iloc[5] > ema.iloc[4]

def test_calculate_rsi():
    # Continuously increasing prices
    prices = pd.Series(range(100, 130))

    rsi = calculate_rsi(prices, window=14)

    # RSI should be 100 when prices only increase
    assert rsi.iloc[-1] == 100


def test_calculate_rsi_falling_prices():
    # Continuously decreasing prices
    prices = pd.Series(range(130, 100, -1))

    rsi = calculate_rsi(prices, window=14)

    # RSI should be 0 when prices only decrease
    assert rsi.iloc[-1] == 0

def test_calculate_macd():
    # Generate 60 sample closing prices
    prices = pd.Series(range(100, 160))

    macd = calculate_macd(prices)

    # Verify output columns
    assert list(macd.columns) == [
        "macd",
        "signal",
        "histogram"
    ]

    # Verify MACD values are available
    assert not pd.isna(macd["macd"].iloc[-1])
    assert not pd.isna(macd["signal"].iloc[-1])
    assert not pd.isna(macd["histogram"].iloc[-1])

    # Histogram = MACD line - Signal line
    assert abs(
        macd["histogram"].iloc[-1]
        - (macd["macd"].iloc[-1] - macd["signal"].iloc[-1])
    ) < 1e-10



def test_calculate_historical_volatility():
    # Generate sample closing prices
    prices = pd.Series([
        100, 102, 101, 105, 103, 107, 106, 110,
        108, 112, 111, 115, 113, 117, 116, 120,
        118, 122, 121, 125, 123, 127, 126, 130,
        128, 132, 131, 135, 133, 137, 136
    ])

    volatility = calculate_historical_volatility(
        prices,
        window=20
    )

    # Volatility should eventually produce a value
    assert not pd.isna(volatility.iloc[-1])

    # Volatility cannot be negative
    assert volatility.iloc[-1] >= 0

@pytest.mark.parametrize(
    "indicator",
    [
        lambda prices: calculate_sma(prices, 2),
        lambda prices: calculate_ema(prices, 2),
        lambda prices: calculate_rsi(prices, 2),
        lambda prices: calculate_macd(prices),
        lambda prices: calculate_historical_volatility(prices, 2),
    ],
    ids=["SMA", "EMA", "RSI", "MACD", "Volatility"]
)
def test_indicators_reject_missing_values(indicator):
    prices = pd.Series([100, 110, None, 120, 130])

    with pytest.raises(ValueError):
        indicator(prices)

@pytest.mark.parametrize(
    "indicator",
    [
        lambda prices: calculate_sma(prices, 2),
        lambda prices: calculate_ema(prices, 2),
        lambda prices: calculate_rsi(prices, 2),
        lambda prices: calculate_macd(prices),
        lambda prices: calculate_historical_volatility(prices, 2),
    ],
    ids=["SMA", "EMA", "RSI", "MACD", "Volatility"]
)
def test_indicators_reject_empty_data(indicator):
    prices = pd.Series(dtype=float)

    with pytest.raises(ValueError):
        indicator(prices)


@pytest.mark.parametrize(
    "calculation",
    [
        lambda: calculate_sma(pd.Series([100, 110, 120]), 0),
        lambda: calculate_ema(pd.Series([100, 110, 120]), 0),
        lambda: calculate_rsi(pd.Series([100, 110, 120]), 0),
        lambda: calculate_macd(
            pd.Series(range(100, 140)),
            fast=26,
            slow=26
        ),
        lambda: calculate_historical_volatility(
            pd.Series([100, 110, 120]), window=1
        ),
        lambda: calculate_historical_volatility(
            pd.Series([100, 110, 120]), trading_days=0
        ),
        lambda: calculate_rsi(pd.Series([100, -10, 120]), 2),
        lambda: calculate_historical_volatility(
            pd.Series([100, 0, 120]), 2
        ),
    ],
    ids=[
        "SMA-zero-window",
        "EMA-zero-window",
        "RSI-zero-window",
        "MACD-invalid-periods",
        "Volatility-invalid-window",
        "Volatility-zero-trading-days",
        "RSI-negative-prices",
        "Volatility-zero-prices"
    ]
)
def test_indicators_reject_invalid_parameters(calculation):
    with pytest.raises(ValueError):
        calculation()

