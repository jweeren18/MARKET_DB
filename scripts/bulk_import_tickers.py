"""
Bulk Ticker Import Script

Import hundreds of tickers from CSV file or list with automatic metadata fetching.

Usage:
    # From CSV file
    python scripts/bulk_import_tickers.py --csv tickers.csv

    # From comma-separated list
    python scripts/bulk_import_tickers.py --tickers AAPL,MSFT,GOOGL,TSLA

    # With automatic data backfill
    python scripts/bulk_import_tickers.py --csv tickers.csv --backfill --days 730

CSV Format:
    ticker,name,asset_type,sector,industry
    AAPL,Apple Inc,STOCK,Technology,Consumer Electronics
    MSFT,Microsoft Corporation,STOCK,Technology,Software

Or simple format (script will fetch metadata):
    ticker
    AAPL
    MSFT
    GOOGL
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import argparse
import logging
import csv
from typing import List, Dict, Optional
from datetime import datetime

import yfinance as yf
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Ticker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_ticker_metadata(ticker_symbol: str) -> Optional[Dict]:
    """
    Fetch ticker metadata from yfinance.

    Returns dict with name, sector, industry, asset_type, etc.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # Extract relevant fields
        metadata = {
            "ticker": ticker_symbol.upper(),
            "name": info.get("longName") or info.get("shortName") or ticker_symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap_category": categorize_market_cap(info.get("marketCap")),
            "exchange": info.get("exchange"),
            "asset_type": determine_asset_type(info)
        }

        return metadata

    except Exception as e:
        logger.warning(f"Could not fetch metadata for {ticker_symbol}: {e}")
        return None


def determine_asset_type(info: Dict) -> str:
    """Determine asset type from yfinance info."""
    quote_type = info.get("quoteType", "").upper()

    if quote_type == "EQUITY":
        return "STOCK"
    elif quote_type == "ETF":
        return "ETF"
    elif quote_type == "CRYPTOCURRENCY":
        return "CRYPTO"
    elif quote_type == "INDEX":
        return "INDEX"
    elif quote_type == "MUTUALFUND":
        return "MUTUAL_FUND"
    else:
        return "STOCK"  # Default to stock


def categorize_market_cap(market_cap: Optional[int]) -> Optional[str]:
    """Categorize market cap into LARGE, MID, SMALL, MICRO."""
    if market_cap is None:
        return None

    # Market cap in billions
    cap_billions = market_cap / 1_000_000_000

    if cap_billions >= 200:
        return "MEGA"
    elif cap_billions >= 10:
        return "LARGE"
    elif cap_billions >= 2:
        return "MID"
    elif cap_billions >= 0.3:
        return "SMALL"
    else:
        return "MICRO"


def read_tickers_from_csv(csv_path: str) -> List[Dict]:
    """
    Read tickers from CSV file.

    Supports two formats:
    1. Full format: ticker,name,asset_type,sector,industry
    2. Simple format: ticker (script will fetch metadata)
    """
    tickers = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Check if it's simple format (only ticker column)
            if reader.fieldnames == ['ticker']:
                logger.info("Simple CSV format detected. Will fetch metadata for each ticker.")
                for row in reader:
                    ticker_symbol = row['ticker'].strip().upper()
                    if ticker_symbol:
                        tickers.append({"ticker": ticker_symbol})
            else:
                # Full format with metadata
                for row in reader:
                    ticker_data = {
                        "ticker": row.get('ticker', '').strip().upper(),
                        "name": row.get('name'),
                        "asset_type": row.get('asset_type', 'STOCK').upper(),
                        "sector": row.get('sector'),
                        "industry": row.get('industry'),
                        "market_cap_category": row.get('market_cap_category'),
                        "exchange": row.get('exchange')
                    }

                    if ticker_data['ticker']:
                        tickers.append(ticker_data)

        logger.info(f"Read {len(tickers)} tickers from {csv_path}")
        return tickers

    except Exception as e:
        logger.error(f"Failed to read CSV file: {e}")
        return []


def parse_ticker_list(ticker_string: str) -> List[Dict]:
    """Parse comma-separated ticker list."""
    tickers = []

    for ticker in ticker_string.split(','):
        ticker = ticker.strip().upper()
        if ticker:
            tickers.append({"ticker": ticker})

    logger.info(f"Parsed {len(tickers)} tickers from list")
    return tickers


def import_ticker(db: Session, ticker_data: Dict, fetch_metadata: bool = True) -> bool:
    """
    Import a single ticker into the database.

    Args:
        db: Database session
        ticker_data: Dict with ticker info
        fetch_metadata: Whether to fetch missing metadata from yfinance

    Returns:
        True if successful, False otherwise
    """
    ticker_symbol = ticker_data['ticker']

    try:
        # Check if ticker already exists
        existing = db.query(Ticker).filter(Ticker.ticker == ticker_symbol).first()

        if existing:
            logger.info(f"[SKIP] {ticker_symbol} already exists")
            return False

        # Fetch metadata if not provided
        if fetch_metadata and (not ticker_data.get('name') or ticker_data.get('name') == ticker_symbol):
            logger.info(f"Fetching metadata for {ticker_symbol}...")
            metadata = fetch_ticker_metadata(ticker_symbol)

            if metadata:
                # Merge with provided data (provided data takes precedence)
                for key, value in metadata.items():
                    if key not in ticker_data or not ticker_data[key]:
                        ticker_data[key] = value

        # Create ticker record
        new_ticker = Ticker(
            ticker=ticker_symbol,
            name=ticker_data.get('name') or ticker_symbol,
            asset_type=ticker_data.get('asset_type') or 'STOCK',
            sector=ticker_data.get('sector'),
            industry=ticker_data.get('industry'),
            market_cap_category=ticker_data.get('market_cap_category'),
            exchange=ticker_data.get('exchange'),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(new_ticker)
        db.commit()

        logger.info(f"[OK] Added {ticker_symbol} - {new_ticker.name}")
        return True

    except Exception as e:
        logger.error(f"[ERROR] Failed to import {ticker_symbol}: {e}")
        db.rollback()
        return False


def bulk_import_tickers(
    tickers: List[Dict],
    fetch_metadata: bool = True,
    backfill: bool = False,
    backfill_days: int = 730
) -> Dict:
    """
    Import multiple tickers in bulk.

    Returns:
        Dict with statistics (added, skipped, failed)
    """
    db = SessionLocal()

    stats = {
        "total": len(tickers),
        "added": 0,
        "skipped": 0,
        "failed": 0,
        "new_tickers": []
    }

    try:
        logger.info("=" * 80)
        logger.info(f"BULK TICKER IMPORT - {stats['total']} tickers")
        logger.info("=" * 80)

        for ticker_data in tickers:
            ticker_symbol = ticker_data['ticker']

            result = import_ticker(db, ticker_data, fetch_metadata)

            if result:
                stats['added'] += 1
                stats['new_tickers'].append(ticker_symbol)
            else:
                stats['skipped'] += 1

        logger.info("")
        logger.info("=" * 80)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total tickers: {stats['total']}")
        logger.info(f"Added: {stats['added']}")
        logger.info(f"Skipped: {stats['skipped']}")
        logger.info(f"Failed: {stats['failed']}")

        if stats['new_tickers']:
            logger.info("")
            logger.info(f"New tickers added: {', '.join(stats['new_tickers'])}")

        # Optionally trigger backfill
        if backfill and stats['new_tickers']:
            logger.info("")
            logger.info("=" * 80)
            logger.info("TRIGGERING DATA BACKFILL")
            logger.info("=" * 80)
            logger.info(f"Backfilling {backfill_days} days of data for {len(stats['new_tickers'])} tickers")

            # Import and run backfill script
            try:
                from scripts.backfill_historical_data import backfill_ticker_data

                for ticker in stats['new_tickers']:
                    logger.info(f"Backfilling {ticker}...")
                    backfill_ticker_data(ticker, days=backfill_days)

                logger.info("")
                logger.info("[OK] Backfill completed!")
                logger.info("")
                logger.info("Next steps:")
                logger.info("  1. Calculate indicators:")
                logger.info(f"     python backend/jobs/calculate_indicators.py --all")
                logger.info("  2. Score opportunities:")
                logger.info(f"     python backend/jobs/score_opportunities.py --all")

            except Exception as e:
                logger.error(f"Backfill failed: {e}")
                logger.info("You can run backfill manually:")
                logger.info(f"  python scripts/backfill_historical_data.py")

        logger.info("=" * 80)

        return stats

    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bulk import tickers into the database"
    )

    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--csv",
        type=str,
        help="Path to CSV file with tickers"
    )
    input_group.add_argument(
        "--tickers",
        type=str,
        help="Comma-separated list of tickers (e.g., AAPL,MSFT,GOOGL)"
    )

    # Options
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Don't fetch metadata from yfinance (use only CSV data)"
    )
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Automatically backfill historical data after import"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=730,
        help="Number of days to backfill (default: 730 = 2 years)"
    )

    args = parser.parse_args()

    # Read tickers from source
    if args.csv:
        tickers = read_tickers_from_csv(args.csv)
    else:
        tickers = parse_ticker_list(args.tickers)

    if not tickers:
        logger.error("No tickers to import!")
        return

    # Import tickers
    stats = bulk_import_tickers(
        tickers=tickers,
        fetch_metadata=not args.no_metadata,
        backfill=args.backfill,
        backfill_days=args.days
    )

    # Exit with appropriate code
    if stats['added'] > 0:
        logger.info(f"✅ Successfully added {stats['added']} new tickers!")
        sys.exit(0)
    else:
        logger.warning("⚠️ No new tickers were added")
        sys.exit(0)


if __name__ == "__main__":
    main()
