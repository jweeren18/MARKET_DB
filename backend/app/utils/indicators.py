"""
Technical indicator calculation utilities.
Uses pandas and numpy for indicator calculations.

Implements:
- Moving Averages (SMA, EMA)
- Momentum Indicators (RSI, MACD, Stochastic)
- Volatility Indicators (Bollinger Bands, ATR)
- Volume Indicators
- Trend Detection
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from decimal import Decimal


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


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA).

    Args:
        prices: Series of closing prices
        period: EMA period

    Returns:
        Series of EMA values
    """
    return prices.ewm(span=period, adjust=False).mean()


def calculate_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator.

    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of closing prices
        k_period: %K period (default 14)
        d_period: %D period (default 3)

    Returns:
        Tuple of (%K, %D)
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_period).mean()

    return k_percent, d_percent


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV).

    Args:
        close: Series of closing prices
        volume: Series of volume data

    Returns:
        Series of OBV values
    """
    obv = pd.Series(index=close.index, dtype=float)
    obv.iloc[0] = volume.iloc[0]

    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]

    return obv


def calculate_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    Calculate Average Directional Index (ADX) - trend strength.

    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of closing prices
        period: ADX period (default 14)

    Returns:
        Series of ADX values
    """
    # Calculate +DM and -DM
    high_diff = high.diff()
    low_diff = -low.diff()

    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

    # Calculate ATR
    atr = calculate_atr(high, low, close, period)

    # Calculate +DI and -DI
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

    # Calculate DX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

    # Calculate ADX
    adx = dx.rolling(window=period).mean()

    return adx


def calculate_williams_r(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    Calculate Williams %R.

    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of closing prices
        period: Period (default 14)

    Returns:
        Series of Williams %R values (-100 to 0)
    """
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()

    williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))

    return williams_r


def calculate_rate_of_change(prices: pd.Series, period: int = 12) -> pd.Series:
    """
    Calculate Rate of Change (ROC) - momentum indicator.

    Args:
        prices: Series of closing prices
        period: Period (default 12)

    Returns:
        Series of ROC values (percentage)
    """
    roc = 100 * ((prices - prices.shift(period)) / prices.shift(period))
    return roc


def detect_golden_cross(
    prices: pd.Series,
    short_period: int = 50,
    long_period: int = 200
) -> pd.Series:
    """
    Detect golden cross (short MA crosses above long MA).

    Args:
        prices: Series of closing prices
        short_period: Short MA period (default 50)
        long_period: Long MA period (default 200)

    Returns:
        Boolean series indicating golden cross
    """
    short_ma = calculate_moving_averages(prices, short_period)
    long_ma = calculate_moving_averages(prices, long_period)

    # Golden cross: short MA crosses above long MA
    cross_above = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))

    return cross_above


def detect_death_cross(
    prices: pd.Series,
    short_period: int = 50,
    long_period: int = 200
) -> pd.Series:
    """
    Detect death cross (short MA crosses below long MA).

    Args:
        prices: Series of closing prices
        short_period: Short MA period (default 50)
        long_period: Long MA period (default 200)

    Returns:
        Boolean series indicating death cross
    """
    short_ma = calculate_moving_averages(prices, short_period)
    long_ma = calculate_moving_averages(prices, long_period)

    # Death cross: short MA crosses below long MA
    cross_below = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))

    return cross_below


def calculate_all_indicators(
    df: pd.DataFrame,
    include_volume: bool = True
) -> Dict[str, Any]:
    """
    Calculate all technical indicators for a given price DataFrame.

    Args:
        df: DataFrame with columns: open, high, low, close, volume
        include_volume: Whether to calculate volume indicators (default True)

    Returns:
        Dictionary of indicator name -> value (latest value) or series
    """
    indicators = {}

    # Price data
    close = df['close']
    high = df['high']
    low = df['low']

    # Moving Averages
    indicators['sma_20'] = calculate_moving_averages(close, 20)
    indicators['sma_50'] = calculate_moving_averages(close, 50)
    indicators['sma_200'] = calculate_moving_averages(close, 200)
    indicators['ema_12'] = calculate_ema(close, 12)
    indicators['ema_26'] = calculate_ema(close, 26)

    # Momentum Indicators
    indicators['rsi_14'] = calculate_rsi(close, 14)
    macd, signal, histogram = calculate_macd(close)
    indicators['macd'] = macd
    indicators['macd_signal'] = signal
    indicators['macd_histogram'] = histogram

    # Stochastic
    k, d = calculate_stochastic(high, low, close)
    indicators['stochastic_k'] = k
    indicators['stochastic_d'] = d

    # Volatility Indicators
    upper, middle, lower = calculate_bollinger_bands(close)
    indicators['bb_upper'] = upper
    indicators['bb_middle'] = middle
    indicators['bb_lower'] = lower
    indicators['atr_14'] = calculate_atr(high, low, close, 14)

    # Trend Indicators
    indicators['adx_14'] = calculate_adx(high, low, close, 14)
    indicators['williams_r'] = calculate_williams_r(high, low, close, 14)
    indicators['roc_12'] = calculate_rate_of_change(close, 12)

    # Volume Indicators (if volume data available)
    if include_volume and 'volume' in df.columns:
        volume = df['volume']
        indicators['volume_sma_20'] = calculate_volume_sma(volume, 20)
        indicators['volume_spike'] = detect_volume_spike(volume)
        indicators['obv'] = calculate_obv(close, volume)

    # Crossover Signals
    indicators['golden_cross'] = detect_golden_cross(close)
    indicators['death_cross'] = detect_death_cross(close)

    return indicators


def get_latest_indicator_values(
    df: pd.DataFrame,
    include_volume: bool = True
) -> Dict[str, float]:
    """
    Get latest (most recent) values for all indicators.

    Args:
        df: DataFrame with OHLCV data
        include_volume: Whether to include volume indicators

    Returns:
        Dictionary of indicator_name -> latest_value
    """
    indicators = calculate_all_indicators(df, include_volume)

    latest_values = {}
    for name, series in indicators.items():
        if isinstance(series, pd.Series):
            # Get last non-NaN value
            last_valid = series.dropna()
            if len(last_valid) > 0:
                latest_values[name] = float(last_valid.iloc[-1])
        else:
            latest_values[name] = float(series)

    return latest_values
