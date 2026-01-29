"""
Calculate Technical Indicators Job

Batch job to calculate and store technical indicators for all active tickers.
Can be run manually or scheduled via Airflow.

Usage:
    python backend/jobs/calculate_indicators.py --all
    python backend/jobs/calculate_indicators.py --ticker AAPL
    python backend/jobs/calculate_indicators.py --all --lookback 365
    python backend/jobs/calculate_indicators.py --all --force
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import argparse
import logging
from datetime import datetime

from app.database import SessionLocal
from app.services.signal_engine import SignalEngine


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def calculate_indicators_for_ticker(
    ticker: str,
    lookback_days: int = 252,
    force: bool = False
):
    """Calculate indicators for a single ticker."""
    db = SessionLocal()

    try:
        signal_engine = SignalEngine(db)

        logger.info(f"Starting indicator calculation for {ticker}")
        result = signal_engine.calculate_indicators_for_ticker(
            ticker=ticker,
            lookback_days=lookback_days,
            force_recalculate=force
        )

        if result["status"] == "success":
            logger.info(f"[OK] Successfully calculated indicators for {ticker}")
            logger.info(f"  Indicators: {len(result['indicators_calculated'])}")
            logger.info(f"  Data points: {result['data_points']}")
            logger.info(f"  Stored records: {result['stored_records']}")
        elif result["status"] == "skipped":
            logger.info(f"[-] Skipped {ticker}: {result['reason']}")
        else:
            logger.error(f"[FAILED] Failed to calculate indicators for {ticker}: {result.get('reason', 'unknown')}")

        return result

    except Exception as e:
        logger.error(f"Error calculating indicators for {ticker}: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}

    finally:
        db.close()


def calculate_indicators_for_all_tickers(
    lookback_days: int = 252,
    force: bool = False
):
    """Calculate indicators for all active tickers."""
    db = SessionLocal()

    try:
        signal_engine = SignalEngine(db)

        logger.info("=" * 80)
        logger.info("CALCULATE TECHNICAL INDICATORS - ALL TICKERS")
        logger.info("=" * 80)
        logger.info(f"Lookback period: {lookback_days} days")
        logger.info(f"Force recalculate: {force}")
        logger.info("")

        start_time = datetime.now()

        results = signal_engine.calculate_indicators_for_all_tickers(
            lookback_days=lookback_days,
            force_recalculate=force
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Print summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("CALCULATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total tickers: {results['total_tickers']}")
        logger.info(f"Successful: {results['successful']}")
        logger.info(f"Skipped: {results['skipped']}")
        logger.info(f"Failed: {results['failed']}")
        logger.info(f"Duration: {duration:.2f} seconds")

        if results['errors']:
            logger.info("")
            logger.info("ERRORS:")
            for error in results['errors']:
                logger.error(f"  {error['ticker']}: {error['error']}")

        logger.info("=" * 80)

        return results

    except Exception as e:
        logger.error(f"Error in batch indicator calculation: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}

    finally:
        db.close()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Calculate technical indicators for tickers"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        help="Calculate indicators for a specific ticker (e.g., AAPL)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Calculate indicators for all active tickers"
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=252,
        help="Number of days of historical data to use (default: 252)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recalculation even if indicators exist for today"
    )

    args = parser.parse_args()

    if args.ticker:
        # Calculate for single ticker
        calculate_indicators_for_ticker(
            ticker=args.ticker,
            lookback_days=args.lookback,
            force=args.force
        )
    elif args.all:
        # Calculate for all tickers
        calculate_indicators_for_all_tickers(
            lookback_days=args.lookback,
            force=args.force
        )
    else:
        logger.error("Must specify either --ticker or --all")
        parser.print_help()


if __name__ == "__main__":
    main()
