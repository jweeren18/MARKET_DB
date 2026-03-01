"""
Signal Engine Service - Calculate and store technical indicators.

Responsibilities:
- Calculate technical indicators for all tickers
- Store indicators in technical_indicators table
- Detect anomalies and signals
- Provide indicator history and analysis
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import decimal
import pandas as pd
import logging

from app.models import PriceData, TechnicalIndicator, Ticker
from app.utils.indicators import (
    calculate_all_indicators,
    get_latest_indicator_values,
)

logger = logging.getLogger(__name__)


class SignalEngine:
    """Service class for technical indicator calculations and signal detection."""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Indicator Calculation ====================

    def calculate_indicators_for_ticker(
        self,
        ticker: str,
        lookback_days: int = 252,
        force_recalculate: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate all technical indicators for a ticker.

        Args:
            ticker: Stock ticker symbol
            lookback_days: Number of days of historical data to use
            force_recalculate: Recalculate even if recent indicators exist

        Returns:
            Dictionary with indicator values and metadata
        """
        logger.info(f"Calculating indicators for {ticker} (lookback: {lookback_days} days)")

        # Check if we need to recalculate
        if not force_recalculate:
            latest_indicator = self._get_latest_indicator_date(ticker)
            if latest_indicator:
                # If we have indicators from today, skip
                if latest_indicator.date() == datetime.now().date():
                    logger.info(f"Indicators for {ticker} already calculated today")
                    return {"status": "skipped", "reason": "already_calculated_today"}

        # Get price data
        price_data = self._get_price_data(ticker, lookback_days)

        if len(price_data) < 50:  # Need minimum data for indicators
            logger.warning(f"Insufficient price data for {ticker}: {len(price_data)} days")
            return {"status": "error", "reason": "insufficient_data", "days_available": len(price_data)}

        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        df = df.sort_values('timestamp')

        # Calculate all indicators
        try:
            indicators = calculate_all_indicators(df, include_volume=True)
        except Exception as e:
            logger.error(f"Error calculating indicators for {ticker}: {e}", exc_info=True)
            return {"status": "error", "reason": str(e)}

        # Store indicators in database
        stored_count = self._store_indicators(ticker, df, indicators)

        logger.info(f"Calculated and stored {stored_count} indicator records for {ticker}")

        return {
            "status": "success",
            "ticker": ticker,
            "indicators_calculated": list(indicators.keys()),
            "data_points": len(df),
            "stored_records": stored_count
        }

    def calculate_indicators_for_all_tickers(
        self,
        lookback_days: int = 252,
        force_recalculate: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate indicators for all active tickers.

        Args:
            lookback_days: Number of days of historical data to use
            force_recalculate: Recalculate even if recent indicators exist

        Returns:
            Summary of calculation results
        """
        logger.info("Calculating indicators for all active tickers")

        # Get all active tickers
        tickers = self.db.query(Ticker).filter(Ticker.is_active == True).all()

        results = {
            "total_tickers": len(tickers),
            "successful": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }

        for ticker_obj in tickers:
            try:
                result = self.calculate_indicators_for_ticker(
                    ticker_obj.ticker,
                    lookback_days=lookback_days,
                    force_recalculate=force_recalculate
                )

                if result["status"] == "success":
                    results["successful"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "ticker": ticker_obj.ticker,
                        "error": result.get("reason", "unknown")
                    })

            except Exception as e:
                logger.error(f"Error processing {ticker_obj.ticker}: {e}", exc_info=True)
                results["failed"] += 1
                results["errors"].append({
                    "ticker": ticker_obj.ticker,
                    "error": str(e)
                })

        logger.info(f"Indicator calculation complete: {results['successful']} successful, "
                    f"{results['skipped']} skipped, {results['failed']} failed")

        return results

    # ==================== Indicator Retrieval ====================

    def get_latest_indicators(self, ticker: str) -> Dict[str, float]:
        """
        Get the most recent indicator values for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary of indicator_name -> value
        """
        # Get the latest date with indicators
        latest_date = self._get_latest_indicator_date(ticker)

        if not latest_date:
            return {}

        # Get all indicators for that date
        indicators = self.db.query(TechnicalIndicator).filter(
            TechnicalIndicator.ticker == ticker,
            TechnicalIndicator.timestamp == latest_date
        ).all()

        return {ind.indicator_name: float(ind.value) for ind in indicators if ind.value is not None}

    def get_indicator_history(
        self,
        ticker: str,
        indicator_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical values for a specific indicator.

        Args:
            ticker: Stock ticker symbol
            indicator_name: Name of the indicator (e.g., 'rsi_14')
            start_date: Start date (optional)
            end_date: End date (optional, default: today)
            limit: Maximum number of records to return

        Returns:
            List of {timestamp, value} dictionaries
        """
        query = self.db.query(TechnicalIndicator).filter(
            TechnicalIndicator.ticker == ticker,
            TechnicalIndicator.indicator_name == indicator_name
        )

        if start_date:
            query = query.filter(TechnicalIndicator.timestamp >= start_date)
        if end_date:
            query = query.filter(TechnicalIndicator.timestamp <= end_date)

        indicators = query.order_by(TechnicalIndicator.timestamp.desc()).limit(limit).all()

        return [
            {
                "timestamp": ind.timestamp,
                "value": float(ind.value) if ind.value else None,
                "meta": ind.meta
            }
            for ind in indicators
        ]

    def get_indicators_for_date(
        self,
        ticker: str,
        date: datetime
    ) -> Dict[str, float]:
        """
        Get all indicator values for a specific date.

        Args:
            ticker: Stock ticker symbol
            date: Target date

        Returns:
            Dictionary of indicator_name -> value
        """
        indicators = self.db.query(TechnicalIndicator).filter(
            TechnicalIndicator.ticker == ticker,
            func.date(TechnicalIndicator.timestamp) == date.date()
        ).all()

        return {ind.indicator_name: float(ind.value) for ind in indicators if ind.value is not None}

    # ==================== Signal Detection ====================

    def detect_signals(self, ticker: str) -> Dict[str, Any]:
        """
        Detect trading signals based on technical indicators.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with detected signals and their strength
        """
        indicators = self.get_latest_indicators(ticker)

        if not indicators:
            return {"signals": [], "message": "No indicators available"}

        signals = []

        # RSI Signals
        if 'rsi_14' in indicators:
            rsi = indicators['rsi_14']
            if rsi < 30:
                signals.append({
                    "type": "oversold",
                    "indicator": "RSI",
                    "value": rsi,
                    "strength": "strong" if rsi < 25 else "moderate",
                    "description": f"RSI at {rsi:.2f} indicates oversold conditions"
                })
            elif rsi > 70:
                signals.append({
                    "type": "overbought",
                    "indicator": "RSI",
                    "value": rsi,
                    "strength": "strong" if rsi > 75 else "moderate",
                    "description": f"RSI at {rsi:.2f} indicates overbought conditions"
                })

        # MACD Signals
        if 'macd' in indicators and 'macd_signal' in indicators:
            macd = indicators['macd']
            signal = indicators['macd_signal']
            if macd > signal and abs(macd - signal) > 0.5:
                signals.append({
                    "type": "bullish",
                    "indicator": "MACD",
                    "value": macd - signal,
                    "strength": "strong" if abs(macd - signal) > 2 else "moderate",
                    "description": f"MACD above signal line (difference: {macd - signal:.2f})"
                })
            elif macd < signal and abs(macd - signal) > 0.5:
                signals.append({
                    "type": "bearish",
                    "indicator": "MACD",
                    "value": macd - signal,
                    "strength": "strong" if abs(macd - signal) > 2 else "moderate",
                    "description": f"MACD below signal line (difference: {macd - signal:.2f})"
                })

        # Bollinger Bands Signals
        if all(k in indicators for k in ['bb_upper', 'bb_lower', 'bb_middle']):
            # Need current price
            price_data = self._get_price_data(ticker, days=1)
            if price_data:
                current_price = float(price_data[-1]['close'])
                bb_upper = indicators['bb_upper']
                bb_lower = indicators['bb_lower']

                if current_price <= bb_lower:
                    signals.append({
                        "type": "oversold",
                        "indicator": "Bollinger Bands",
                        "value": (current_price - bb_lower) / bb_lower * 100,
                        "strength": "moderate",
                        "description": f"Price at lower Bollinger Band ({current_price:.2f} vs {bb_lower:.2f})"
                    })
                elif current_price >= bb_upper:
                    signals.append({
                        "type": "overbought",
                        "indicator": "Bollinger Bands",
                        "value": (current_price - bb_upper) / bb_upper * 100,
                        "strength": "moderate",
                        "description": f"Price at upper Bollinger Band ({current_price:.2f} vs {bb_upper:.2f})"
                    })

        # Stochastic Signals
        if 'stochastic_k' in indicators:
            stoch_k = indicators['stochastic_k']
            if stoch_k < 20:
                signals.append({
                    "type": "oversold",
                    "indicator": "Stochastic",
                    "value": stoch_k,
                    "strength": "moderate",
                    "description": f"Stochastic %K at {stoch_k:.2f} indicates oversold"
                })
            elif stoch_k > 80:
                signals.append({
                    "type": "overbought",
                    "indicator": "Stochastic",
                    "value": stoch_k,
                    "strength": "moderate",
                    "description": f"Stochastic %K at {stoch_k:.2f} indicates overbought"
                })

        # ADX Trend Strength
        if 'adx_14' in indicators:
            adx = indicators['adx_14']
            if adx > 25:
                strength = "strong" if adx > 40 else "moderate"
                signals.append({
                    "type": "trending",
                    "indicator": "ADX",
                    "value": adx,
                    "strength": strength,
                    "description": f"ADX at {adx:.2f} indicates {strength} trend"
                })

        return {
            "ticker": ticker,
            "as_of": datetime.now(),
            "signals": signals,
            "signal_count": len(signals),
            "indicators_analyzed": len(indicators)
        }

    # ==================== Helper Methods ====================

    def _get_price_data(self, ticker: str, days: int) -> List[Dict[str, Any]]:
        """Get price data for a ticker."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        price_records = self.db.query(PriceData).filter(
            PriceData.ticker == ticker,
            PriceData.timestamp >= start_date,
            PriceData.timestamp <= end_date
        ).order_by(PriceData.timestamp).all()

        return [
            {
                "timestamp": p.timestamp,
                "open": float(p.open),
                "high": float(p.high),
                "low": float(p.low),
                "close": float(p.close),
                "volume": int(p.volume) if p.volume else 0
            }
            for p in price_records
        ]

    def _get_latest_indicator_date(self, ticker: str) -> Optional[datetime]:
        """Get the date of the most recent indicator calculation."""
        result = self.db.query(func.max(TechnicalIndicator.timestamp)).filter(
            TechnicalIndicator.ticker == ticker
        ).scalar()

        return result

    def _safe_decimal_convert(self, value: Any) -> Optional[Decimal]:
        """
        Safely convert a value to Decimal, handling NaN, inf, and other special values.

        Args:
            value: Value to convert

        Returns:
            Decimal value or None if conversion fails or value is invalid
        """
        # Check if None
        if value is None:
            return None

        # Check for NaN
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        # Convert to string and check for special values
        value_str = str(value).lower()
        if value_str in ('nan', 'inf', '-inf', 'infinity', '-infinity', ''):
            return None

        # Try to convert to Decimal
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, decimal.InvalidOperation):
            return None

    def _store_indicators(
        self,
        ticker: str,
        df: pd.DataFrame,
        indicators: Dict[str, pd.Series]
    ) -> int:
        """
        Store calculated indicators in the database.

        Uses upsert logic to update existing records or insert new ones.
        """
        stored_count = 0

        for indicator_name, series in indicators.items():
            if not isinstance(series, pd.Series):
                continue  # Skip non-series values

            # Iterate through each date in the series
            for idx, value in series.items():
                # Convert value to Decimal safely
                decimal_value = self._safe_decimal_convert(value)
                if decimal_value is None:
                    continue  # Skip invalid values

                timestamp = df.loc[idx, 'timestamp']

                # Check if indicator already exists
                existing = self.db.query(TechnicalIndicator).filter(
                    TechnicalIndicator.ticker == ticker,
                    TechnicalIndicator.timestamp == timestamp,
                    TechnicalIndicator.indicator_name == indicator_name
                ).first()

                if existing:
                    # Update existing record
                    existing.value = decimal_value
                else:
                    # Insert new record
                    new_indicator = TechnicalIndicator(
                        ticker=ticker,
                        timestamp=timestamp,
                        indicator_name=indicator_name,
                        value=decimal_value,
                        meta=None
                    )
                    self.db.add(new_indicator)

                stored_count += 1

        self.db.commit()
        return stored_count

    def get_indicator_summary(self, ticker: str) -> Dict[str, Any]:
        """
        Get a summary of available indicators for a ticker.

        Returns:
            Dictionary with indicator metadata
        """
        # Get all unique indicator names for this ticker
        indicators = self.db.query(
            TechnicalIndicator.indicator_name,
            func.count(TechnicalIndicator.timestamp).label('count'),
            func.min(TechnicalIndicator.timestamp).label('first_date'),
            func.max(TechnicalIndicator.timestamp).label('last_date')
        ).filter(
            TechnicalIndicator.ticker == ticker
        ).group_by(
            TechnicalIndicator.indicator_name
        ).all()

        return {
            "ticker": ticker,
            "indicators": [
                {
                    "name": ind.indicator_name,
                    "data_points": ind.count,
                    "first_date": ind.first_date,
                    "last_date": ind.last_date,
                    "is_current": ind.last_date.date() == datetime.now().date()
                }
                for ind in indicators
            ],
            "total_indicators": len(indicators)
        }
