#!/usr/bin/env python3
"""
Data Ingestion Job

Fetches market data from Schwab API and stores in the database.
Runs as a Kubernetes pod triggered by Airflow.

Usage:
    python jobs/data_ingestion.py [--tickers AAPL,MSFT,NVDA] [--days 1]
"""

import sys
import os
import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from typing import List

# Add backend to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Ticker, PriceData
from app.services.market_data_service import market_data_service
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataIngestionJob:
    """Data ingestion job for fetching market data."""

    def __init__(self, db: Session):
        self.db = db

    def get_active_tickers(self) -> List[str]:
        """Get list of active tickers to fetch data for."""
        tickers = self.db.query(Ticker).filter(Ticker.is_active == True).all()
        return [t.ticker for t in tickers]

    async def fetch_price_history(self, symbol: str, days: int = 1) -> List[dict]:
        """Fetch price history for a symbol."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching {days} days of price data for {symbol}")

        try:
            data = await market_data_service.get_price_history(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval="1d"
            )
            return data
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return []

    def save_price_data(self, symbol: str, candles: List[dict]):
        """Save price data to database."""
        if not candles:
            logger.warning(f"No price data to save for {symbol}")
            return

        saved_count = 0
        for candle in candles:
            try:
                # Check if data already exists
                existing = self.db.query(PriceData).filter(
                    PriceData.ticker == symbol,
                    PriceData.timestamp == candle['datetime']
                ).first()

                if existing:
                    # Update existing record
                    existing.open = candle['open']
                    existing.high = candle['high']
                    existing.low = candle['low']
                    existing.close = candle['close']
                    existing.volume = candle['volume']
                    existing.adjusted_close = candle.get('adjusted_close', candle['close'])
                else:
                    # Insert new record
                    price_data = PriceData(
                        ticker=symbol,
                        timestamp=candle['datetime'],
                        open=candle['open'],
                        high=candle['high'],
                        low=candle['low'],
                        close=candle['close'],
                        volume=candle['volume'],
                        adjusted_close=candle.get('adjusted_close', candle['close'])
                    )
                    self.db.add(price_data)

                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save candle for {symbol}: {e}")
                continue

        self.db.commit()
        logger.info(f"Saved {saved_count} price records for {symbol}")

    async def run(self, tickers: List[str], days: int = 1):
        """Run the data ingestion job."""
        logger.info(f"Starting data ingestion for {len(tickers)} tickers")

        for symbol in tickers:
            try:
                candles = await self.fetch_price_history(symbol, days)
                self.save_price_data(symbol, candles)
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue

        logger.info("Data ingestion completed")


async def main():
    """Main entry point for the job."""
    parser = argparse.ArgumentParser(description='Ingest market data')
    parser.add_argument('--tickers', type=str, help='Comma-separated list of tickers')
    parser.add_argument('--days', type=int, default=1, help='Number of days to fetch')
    parser.add_argument('--all', action='store_true', help='Fetch for all active tickers')

    args = parser.parse_args()

    # Create database session
    db = SessionLocal()

    try:
        job = DataIngestionJob(db)

        # Determine which tickers to process
        if args.all:
            tickers = job.get_active_tickers()
            logger.info(f"Fetching data for all {len(tickers)} active tickers")
        elif args.tickers:
            tickers = [t.strip() for t in args.tickers.split(',')]
        else:
            logger.error("Must specify either --tickers or --all")
            return

        # Run the job
        await job.run(tickers, args.days)

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
