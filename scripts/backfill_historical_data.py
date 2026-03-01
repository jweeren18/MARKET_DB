#!/usr/bin/env python3
"""
Historical Data Backfill Script

Easily backfill historical market data for your portfolio tickers.

Usage:
    # Backfill 1 year for all active tickers
    python scripts/backfill_historical_data.py --days 365

    # Backfill 2 years for specific tickers
    python scripts/backfill_historical_data.py --tickers AAPL,MSFT,NVDA --days 730

    # Backfill 5 years for all tickers
    python scripts/backfill_historical_data.py --days 1825 --all

    # Backfill with custom date range
    python scripts/backfill_historical_data.py --start-date 2020-01-01 --end-date 2023-12-31
"""

import sys
import os
import asyncio
import argparse
import logging
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Ticker, PriceData
from app.services.market_data_service import market_data_service
from sqlalchemy import func

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HistoricalBackfillJob:
    """Historical data backfill job."""

    def __init__(self, db: Session):
        self.db = db

    def get_active_tickers(self) -> list[str]:
        """Get list of active tickers."""
        tickers = self.db.query(Ticker).filter(Ticker.is_active == True).all()
        return [t.ticker for t in tickers]

    def get_existing_data_range(self, symbol: str) -> tuple[datetime | None, datetime | None]:
        """Get the date range of existing data for a symbol."""
        result = self.db.query(
            func.min(PriceData.timestamp),
            func.max(PriceData.timestamp)
        ).filter(PriceData.ticker == symbol).first()

        return result if result else (None, None)

    async def backfill_ticker(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """
        Backfill historical data for a single ticker.

        Returns:
            Number of records inserted/updated
        """
        logger.info(f"Backfilling {symbol} from {start_date.date()} to {end_date.date()}")

        # Check existing data
        min_date, max_date = self.get_existing_data_range(symbol)
        if min_date and max_date:
            logger.info(f"  Existing data: {min_date.date()} to {max_date.date()}")
        else:
            logger.info(f"  No existing data found")

        try:
            # Fetch historical data
            data = await market_data_service.get_price_history(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval="1d"
            )

            if not data:
                logger.warning(f"  No data returned for {symbol}")
                return 0

            # Save to database
            saved_count = 0
            updated_count = 0

            for candle in data:
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
                        updated_count += 1
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
                    logger.error(f"  Failed to save candle for {symbol}: {e}")
                    continue

            self.db.commit()
            logger.info(f"  ✓ {symbol}: {saved_count} new, {updated_count} updated")
            return saved_count + updated_count

        except Exception as e:
            logger.error(f"  ✗ Failed to backfill {symbol}: {e}")
            self.db.rollback()
            return 0

    async def run(
        self,
        tickers: list[str],
        start_date: datetime,
        end_date: datetime
    ):
        """Run the backfill job for multiple tickers."""
        logger.info(f"Starting historical backfill for {len(tickers)} tickers")
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")

        total_records = 0
        failed_tickers = []

        for symbol in tickers:
            try:
                count = await self.backfill_ticker(symbol, start_date, end_date)
                total_records += count
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                failed_tickers.append(symbol)
                continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Backfill completed!")
        logger.info(f"Total records processed: {total_records}")
        if failed_tickers:
            logger.warning(f"Failed tickers ({len(failed_tickers)}): {', '.join(failed_tickers)}")
        logger.info(f"{'='*60}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Backfill historical market data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Ticker selection
    ticker_group = parser.add_mutually_exclusive_group()
    ticker_group.add_argument(
        '--tickers',
        type=str,
        help='Comma-separated list of tickers to backfill'
    )
    ticker_group.add_argument(
        '--all',
        action='store_true',
        help='Backfill all active tickers'
    )

    # Date range options
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        '--days',
        type=int,
        help='Number of days to backfill (from today backwards)'
    )
    date_group.add_argument(
        '--start-date',
        type=str,
        help='Start date (YYYY-MM-DD) - requires --end-date'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD) - defaults to today'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.start_date and not args.end_date:
        parser.error("--start-date requires --end-date")

    if not args.tickers and not args.all:
        parser.error("Must specify either --tickers or --all")

    # Parse dates
    if args.days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
    else:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else datetime.now()

    # Create database session
    db = SessionLocal()

    try:
        job = HistoricalBackfillJob(db)

        # Determine which tickers to process
        if args.all:
            tickers = job.get_active_tickers()
            logger.info(f"Backfilling all {len(tickers)} active tickers")
        else:
            tickers = [t.strip() for t in args.tickers.split(',')]

        if not tickers:
            logger.error("No tickers found to backfill")
            return

        # Run the backfill
        await job.run(tickers, start_date, end_date)

    except Exception as e:
        logger.error(f"Backfill job failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
