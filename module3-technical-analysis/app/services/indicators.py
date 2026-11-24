
import pandas as pd
import pytest



def calculate_sma(close_prices, window: int):
    """
    Calculate Simple Moving Average (SMA).
    """

    if window <= 0:
        raise ValueError("Window must be greater than zero.")

    if close_prices.empty:
        raise ValueError("Closing price data cannot be empty.")

    if close_prices.isna().any():
        raise ValueError("Closing price data contains missing values.")

    return close_prices.rolling(window=window).mean()



def calculate_ema(close_prices, window: int):
    """
    Calculate Exponential Moving Average (EMA).
    """

    if window <= 0:
        raise ValueError("Window must be greater than zero.")

    if close_prices.empty:
        raise ValueError("Closing price data cannot be empty.")

    if close_prices.isna().any():
        raise ValueError("Closing price data contains missing values.")

    return close_prices.ewm(
        span=window,
        adjust=False,
        min_periods=window
    ).mean()


def calculate_rsi(close_prices: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    """

    if window <= 0:
        raise ValueError("Window must be greater than zero.")

    if close_prices.empty:
        raise ValueError("Closing price data cannot be empty.")

    if close_prices.isna().any():
        raise ValueError("Closing prices cannot contain missing values.")

    if (close_prices < 0).any():
        raise ValueError("Closing prices cannot be negative.")

    delta = close_prices.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / window,
        min_periods=window,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / window,
        min_periods=window,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    rsi = rsi.mask(avg_loss == 0, 100)
    rsi = rsi.mask((avg_gain == 0) & (avg_loss == 0), 50)

    return rsi

def calculate_macd(
    close_prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> pd.DataFrame:
    """
    Calculate MACD, Signal Line and Histogram.
    """

    if fast <= 0 or slow <= 0 or signal <= 0:
        raise ValueError("All periods must be greater than zero.")

    if fast >= slow:
        raise ValueError("Fast period must be smaller than slow period.")

    if close_prices.empty:
        raise ValueError("Closing price data cannot be empty.")

    if close_prices.isna().any():
        raise ValueError("Closing prices cannot contain missing values.")

    fast_ema = close_prices.ewm(
        span=fast, adjust=False, min_periods=fast
    ).mean()

    slow_ema = close_prices.ewm(
        span=slow, adjust=False, min_periods=slow
    ).mean()

    macd_line = fast_ema - slow_ema

    signal_line = macd_line.ewm(
        span=signal, adjust=False, min_periods=signal
    ).mean()

    histogram = macd_line - signal_line

    return pd.DataFrame({
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    })

import numpy as np


def calculate_historical_volatility(
    close_prices: pd.Series,
    window: int = 20,
    trading_days: int = 252
) -> pd.Series:
    """
    Calculate annualized historical volatility.
    """

    if window <= 1:
        raise ValueError("Window must be greater than 1.")

    if trading_days <= 0:
        raise ValueError("Trading days must be greater than zero.")

    if close_prices.empty:
        raise ValueError("Closing prices cannot be empty.")

    if close_prices.isna().any():
        raise ValueError("Closing prices cannot contain missing values.")

    if (close_prices <= 0).any():
        raise ValueError("Closing prices must be positive.")

    log_returns = np.log(close_prices / close_prices.shift(1))

    volatility = (
        log_returns
        .rolling(window=window)
        .std()
        * np.sqrt(trading_days)
    )

    return volatility

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
