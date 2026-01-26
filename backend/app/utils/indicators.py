"""
Technical indicator calculation utilities.
Uses pandas and ta library for indicator calculations.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def calculate_moving_averages(prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).

    Args:
        prices: Series of closing prices
        window: Window size for moving average

    Returns:
        Series of moving average values
    """
    return prices.rolling(window=window).mean()


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).

    Args:
        prices: Series of closing prices
        period: RSI period (default 14)

    Returns:
        Series of RSI values (0-100)
    """
    delta = prices.diff()

    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        prices: Series of closing prices
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line period (default 9)

    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: pd.Series,
    window: int = 20,
    num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.

    Args:
        prices: Series of closing prices
        window: Window size for moving average (default 20)
        num_std: Number of standard deviations (default 2)

    Returns:
        Tuple of (Upper band, Middle band, Lower band)
    """
    middle_band = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()

    upper_band = middle_band + (std * num_std)
    lower_band = middle_band - (std * num_std)

    return upper_band, middle_band, lower_band


def calculate_volume_sma(volumes: pd.Series, window: int = 20) -> pd.Series:
    """
    Calculate volume moving average.

    Args:
        volumes: Series of volume data
        window: Window size (default 20)

    Returns:
        Series of volume SMA
    """
    return volumes.rolling(window=window).mean()


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    Calculate Average True Range (ATR).

    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of closing prices
        period: ATR period (default 14)

    Returns:
        Series of ATR values
    """
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return atr


def detect_volume_spike(volumes: pd.Series, threshold: float = 2.0, window: int = 20) -> pd.Series:
    """
    Detect volume spikes.

    Args:
        volumes: Series of volume data
        threshold: Multiplier for volume spike detection (default 2.0)
        window: Window for average volume calculation (default 20)

    Returns:
        Boolean series indicating volume spikes
    """
    avg_volume = calculate_volume_sma(volumes, window)
    is_spike = volumes > (avg_volume * threshold)

    return is_spike
