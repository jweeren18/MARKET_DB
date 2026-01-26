#!/usr/bin/env python3
"""
Calculate Technical Indicators Job

Calculates technical indicators for all tickers with recent price data.
Runs as a Kubernetes pod triggered by Airflow.

Usage:
    python jobs/calculate_indicators.py [--tickers AAPL,MSFT,NVDA]
"""

import argparse
import logging
from datetime import datetime, timedelta
from typing import List
import pandas as pd

from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import SessionLocal
from app.models import Ticker, PriceData, TechnicalIndicator
from app.utils.indicators import calculate_moving_averages, calculate_rsi, calculate_macd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndicatorCalculationJob:
    """Job for calculating technical indicators."""

    def __init__(self, db: Session):
        self.db = db

    def get_active_tickers(self) -> List[str]:
        """Get list of active tickers."""
        tickers = self.db.query(Ticker).filter(Ticker.is_active == True).all()
        return [t.ticker for t in tickers]

    def get_price_data(self, symbol: str, days: int = 200) -> pd.DataFrame:
        """Get price data for a symbol as a DataFrame."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        prices = self.db.query(PriceData).filter(
            and_(
                PriceData.ticker == symbol,
                PriceData.timestamp >= start_date,
                PriceData.timestamp <= end_date
            )
        ).order_by(PriceData.timestamp.asc()).all()

        if not prices:
            return pd.DataFrame()

        data = {
            'timestamp': [p.timestamp for p in prices],
            'open': [float(p.open) for p in prices],
            'high': [float(p.high) for p in prices],
            'low': [float(p.low) for p in prices],
            'close': [float(p.close) for p in prices],
            'volume': [int(p.volume) for p in prices],
        }

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    def save_indicators(self, symbol: str, indicators: dict):
        """Save calculated indicators to database."""
        if not indicators:
            return

        saved_count = 0
        for timestamp, values in indicators.items():
            for indicator_name, value in values.items():
                try:
                    # Check if indicator already exists
                    existing = self.db.query(TechnicalIndicator).filter(
                        and_(
                            TechnicalIndicator.ticker == symbol,
                            TechnicalIndicator.timestamp == timestamp,
                            TechnicalIndicator.indicator_name == indicator_name
                        )
                    ).first()

                    if existing:
                        existing.value = value
                    else:
                        indicator = TechnicalIndicator(
                            ticker=symbol,
                            timestamp=timestamp,
                            indicator_name=indicator_name,
                            value=value
                        )
                        self.db.add(indicator)

                    saved_count += 1
                except Exception as e:
                    logger.error(f"Failed to save indicator {indicator_name} for {symbol}: {e}")
                    continue

        self.db.commit()
        logger.info(f"Saved {saved_count} indicators for {symbol}")

    def calculate_indicators_for_ticker(self, symbol: str):
        """Calculate all indicators for a ticker."""
        logger.info(f"Calculating indicators for {symbol}")

        # Get price data
        df = self.get_price_data(symbol, days=200)

        if df.empty:
            logger.warning(f"No price data available for {symbol}")
            return

        # Calculate indicators
        indicators = {}

        # Moving averages
        ma_50 = calculate_moving_averages(df['close'], window=50)
        ma_200 = calculate_moving_averages(df['close'], window=200)

        # RSI
        rsi = calculate_rsi(df['close'], period=14)

        # MACD
        macd_line, signal_line, histogram = calculate_macd(df['close'])

        # Organize by timestamp
        for timestamp in df.index:
            indicators[timestamp] = {
                'ma_50': ma_50.loc[timestamp] if timestamp in ma_50.index else None,
                'ma_200': ma_200.loc[timestamp] if timestamp in ma_200.index else None,
                'rsi': rsi.loc[timestamp] if timestamp in rsi.index else None,
                'macd': macd_line.loc[timestamp] if timestamp in macd_line.index else None,
                'macd_signal': signal_line.loc[timestamp] if timestamp in signal_line.index else None,
                'macd_histogram': histogram.loc[timestamp] if timestamp in histogram.index else None,
            }

        # Filter out None values
        for timestamp in list(indicators.keys()):
            indicators[timestamp] = {
                k: v for k, v in indicators[timestamp].items()
                if v is not None and pd.notna(v)
            }

        # Save to database
        self.save_indicators(symbol, indicators)

    def run(self, tickers: List[str]):
        """Run the indicator calculation job."""
        logger.info(f"Starting indicator calculation for {len(tickers)} tickers")

        for symbol in tickers:
            try:
                self.calculate_indicators_for_ticker(symbol)
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue

        logger.info("Indicator calculation completed")


def main():
    """Main entry point for the job."""
    parser = argparse.ArgumentParser(description='Calculate technical indicators')
    parser.add_argument('--tickers', type=str, help='Comma-separated list of tickers')
    parser.add_argument('--all', action='store_true', help='Calculate for all active tickers')

    args = parser.parse_args()

    # Create database session
    db = SessionLocal()

    try:
        job = IndicatorCalculationJob(db)

        # Determine which tickers to process
        if args.all:
            tickers = job.get_active_tickers()
            logger.info(f"Calculating indicators for all {len(tickers)} active tickers")
        elif args.tickers:
            tickers = [t.strip() for t in args.tickers.split(',')]
        else:
            logger.error("Must specify either --tickers or --all")
            return

        # Run the job
        job.run(tickers)

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
