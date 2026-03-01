#!/usr/bin/env python3
"""
Seed Database with Sample Data

Populates the database with sample tickers (stocks and ETFs).
Metadata is hardcoded here; for a larger import with live metadata
use scripts/bulk_import_tickers.py instead.

Usage:
    python scripts/seed_data.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal
from app.models import Ticker


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


def seed_tickers(db):
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


def main():
    """Main entry point."""
    print("Market Intelligence Database Seeding")
    print("=" * 50)

    # Create database session
    db = SessionLocal()

    try:
        seed_tickers(db)

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
