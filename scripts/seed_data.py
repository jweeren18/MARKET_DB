#!/usr/bin/env python3
"""
Seed Database with Sample Data

This script populates the database with:
- Sample tickers (stocks and ETFs)
- Basic ticker information
- Optional: Historical price data using yfinance

Run this to test the platform without Schwab API credentials.

Usage:
    python scripts/seed_data.py [--fetch-prices]
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal
from app.models import Ticker
from app.services.market_data_service import market_data_service


# Sample tickers across different sectors
SAMPLE_TICKERS = [
    # Technology
    {"ticker": "AAPL", "name": "Apple Inc.", "asset_type": "STOCK", "sector": "Technology", "industry": "Consumer Electronics", "market_cap_category": "LARGE", "exchange": "NASDAQ"},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "asset_type": "STOCK", "sector": "Technology", "industry": "Software", "market_cap_category": "LARGE", "exchange": "NASDAQ"},
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "asset_type": "STOCK", "sector": "Technology", "industry": "Semiconductors", "market_cap_category": "LARGE", "exchange": "NASDAQ"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "asset_type": "STOCK", "sector": "Technology", "industry": "Internet Services", "market_cap_category": "LARGE", "exchange": "NASDAQ"},
    {"ticker": "META", "name": "Meta Platforms Inc.", "asset_type": "STOCK", "sector": "Technology", "industry": "Social Media", "market_cap_category": "LARGE", "exchange": "NASDAQ"},

    # Finance
    {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "asset_type": "STOCK", "sector": "Finance", "industry": "Banking", "market_cap_category": "LARGE", "exchange": "NYSE"},
    {"ticker": "V", "name": "Visa Inc.", "asset_type": "STOCK", "sector": "Finance", "industry": "Payment Processing", "market_cap_category": "LARGE", "exchange": "NYSE"},
    {"ticker": "BAC", "name": "Bank of America Corp", "asset_type": "STOCK", "sector": "Finance", "industry": "Banking", "market_cap_category": "LARGE", "exchange": "NYSE"},

    # Healthcare
    {"ticker": "UNH", "name": "UnitedHealth Group Inc.", "asset_type": "STOCK", "sector": "Healthcare", "industry": "Health Insurance", "market_cap_category": "LARGE", "exchange": "NYSE"},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "asset_type": "STOCK", "sector": "Healthcare", "industry": "Pharmaceuticals", "market_cap_category": "LARGE", "exchange": "NYSE"},
    {"ticker": "LLY", "name": "Eli Lilly and Company", "asset_type": "STOCK", "sector": "Healthcare", "industry": "Pharmaceuticals", "market_cap_category": "LARGE", "exchange": "NYSE"},

    # Consumer
    {"ticker": "AMZN", "name": "Amazon.com Inc.", "asset_type": "STOCK", "sector": "Consumer Cyclical", "industry": "E-commerce", "market_cap_category": "LARGE", "exchange": "NASDAQ"},
    {"ticker": "TSLA", "name": "Tesla Inc.", "asset_type": "STOCK", "sector": "Consumer Cyclical", "industry": "Automotive", "market_cap_category": "LARGE", "exchange": "NASDAQ"},
    {"ticker": "WMT", "name": "Walmart Inc.", "asset_type": "STOCK", "sector": "Consumer Defensive", "industry": "Retail", "market_cap_category": "LARGE", "exchange": "NYSE"},
    {"ticker": "HD", "name": "Home Depot Inc.", "asset_type": "STOCK", "sector": "Consumer Cyclical", "industry": "Retail", "market_cap_category": "LARGE", "exchange": "NYSE"},

    # Energy
    {"ticker": "XOM", "name": "Exxon Mobil Corporation", "asset_type": "STOCK", "sector": "Energy", "industry": "Oil & Gas", "market_cap_category": "LARGE", "exchange": "NYSE"},
    {"ticker": "CVX", "name": "Chevron Corporation", "asset_type": "STOCK", "sector": "Energy", "industry": "Oil & Gas", "market_cap_category": "LARGE", "exchange": "NYSE"},

    # ETFs
    {"ticker": "SPY", "name": "SPDR S&P 500 ETF Trust", "asset_type": "ETF", "sector": "Broad Market", "industry": "Index Fund", "market_cap_category": "LARGE", "exchange": "NYSE"},
    {"ticker": "QQQ", "name": "Invesco QQQ Trust", "asset_type": "ETF", "sector": "Technology", "industry": "Index Fund", "market_cap_category": "LARGE", "exchange": "NASDAQ"},
    {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF", "asset_type": "ETF", "sector": "Broad Market", "industry": "Index Fund", "market_cap_category": "LARGE", "exchange": "NYSE"},
    {"ticker": "IWM", "name": "iShares Russell 2000 ETF", "asset_type": "ETF", "sector": "Small Cap", "industry": "Index Fund", "market_cap_category": "SMALL", "exchange": "NYSE"},
]


async def fetch_and_update_ticker_info(db, ticker_symbol: str):
    """Fetch real ticker info from yfinance and update database."""
    try:
        fundamentals = await market_data_service.get_fundamentals(ticker_symbol)

        ticker = db.query(Ticker).filter(Ticker.ticker == ticker_symbol).first()
        if ticker:
            # Update with real data from yfinance
            ticker.name = fundamentals.get('name', ticker.name)
            ticker.sector = fundamentals.get('sector', ticker.sector)
            ticker.industry = fundamentals.get('industry', ticker.industry)

            # Determine market cap category
            market_cap = fundamentals.get('marketCap', 0)
            if market_cap > 200_000_000_000:
                ticker.market_cap_category = 'LARGE'
            elif market_cap > 10_000_000_000:
                ticker.market_cap_category = 'MID'
            elif market_cap > 2_000_000_000:
                ticker.market_cap_category = 'SMALL'
            else:
                ticker.market_cap_category = 'MICRO'

            db.commit()
            print(f"[OK] Updated {ticker_symbol} with real data")
        else:
            print(f"[SKIP] Ticker {ticker_symbol} not found in database")

    except Exception as e:
        print(f"[ERROR] Failed to fetch data for {ticker_symbol}: {e}")


def seed_tickers(db, fetch_real_data: bool = False):
    """Seed the database with sample tickers."""
    print(f"\n[SEED] Seeding {len(SAMPLE_TICKERS)} tickers...")

    added = 0
    updated = 0

    for ticker_data in SAMPLE_TICKERS:
        existing = db.query(Ticker).filter(Ticker.ticker == ticker_data['ticker']).first()

        if existing:
            # Update existing ticker
            for key, value in ticker_data.items():
                setattr(existing, key, value)
            updated += 1
        else:
            # Create new ticker
            ticker = Ticker(**ticker_data)
            db.add(ticker)
            added += 1

    db.commit()

    print(f"[SUCCESS] Added {added} new tickers, updated {updated} existing tickers")

    # Optionally fetch real data from yfinance
    if fetch_real_data:
        print("\n[FETCH] Fetching real data from yfinance...")
        for ticker_data in SAMPLE_TICKERS:
            asyncio.run(fetch_and_update_ticker_info(db, ticker_data['ticker']))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Seed database with sample data')
    parser.add_argument(
        '--fetch-prices',
        action='store_true',
        help='Fetch real data from yfinance (slower but more accurate)'
    )

    args = parser.parse_args()

    print("Market Intelligence Database Seeding")
    print("=" * 50)

    # Create database session
    db = SessionLocal()

    try:
        # Seed tickers
        seed_tickers(db, fetch_real_data=args.fetch_prices)

        print("\n[COMPLETE] Database seeding complete!")
        print(f"\nYou can now:")
        print(f"  1. View tickers in the database")
        print(f"  2. Create portfolios and add holdings")
        print(f"  3. Run Airflow DAGs to fetch price data")
        print(f"  4. Test the scoring algorithm")

    except Exception as e:
        print(f"\n[FAILED] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
