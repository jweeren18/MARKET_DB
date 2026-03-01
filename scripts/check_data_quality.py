#!/usr/bin/env python3
"""
Data Quality Monitoring Script

Checks data completeness, identifies gaps, and validates data quality.

Usage:
    # Full quality report
    python scripts/check_data_quality.py

    # Check specific ticker
    python scripts/check_data_quality.py --ticker AAPL

    # Find gaps for all tickers
    python scripts/check_data_quality.py --gaps-only

    # Check data for specific date range
    python scripts/check_data_quality.py --start-date 2023-01-01 --end-date 2023-12-31
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import func, text
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Ticker, PriceData


class DataQualityChecker:
    """Data quality monitoring and validation."""

    def __init__(self, db: Session):
        self.db = db

    def get_data_summary(self, ticker: str = None) -> List[Dict[str, Any]]:
        """Get summary statistics for each ticker."""
        query = self.db.query(
            PriceData.ticker,
            func.count(PriceData.timestamp).label('record_count'),
            func.min(PriceData.timestamp).label('earliest_date'),
            func.max(PriceData.timestamp).label('latest_date')
        ).group_by(PriceData.ticker)

        if ticker:
            query = query.filter(PriceData.ticker == ticker)

        results = query.all()

        summaries = []
        for row in results:
            days_span = (row.latest_date - row.earliest_date).days if row.earliest_date and row.latest_date else 0
            # Rough estimate: ~252 trading days per year
            expected_records = int(days_span * 252 / 365) if days_span > 0 else 0
            completeness = (row.record_count / expected_records * 100) if expected_records > 0 else 0

            summaries.append({
                'ticker': row.ticker,
                'record_count': row.record_count,
                'earliest_date': row.earliest_date,
                'latest_date': row.latest_date,
                'days_span': days_span,
                'expected_records': expected_records,
                'completeness_pct': min(100, completeness)  # Cap at 100%
            })

        return summaries

    def find_gaps(
        self,
        ticker: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        min_gap_days: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find date gaps in the data (missing trading days).

        Args:
            ticker: Specific ticker to check (None = all)
            start_date: Start of date range to check
            end_date: End of date range to check
            min_gap_days: Minimum gap size to report (default: 2 days)

        Returns:
            List of gaps with ticker, gap size, and date range
        """
        # Build query to find consecutive timestamps and calculate gaps
        query = """
        WITH ordered_data AS (
            SELECT
                ticker,
                timestamp,
                LAG(timestamp) OVER (PARTITION BY ticker ORDER BY timestamp) AS prev_timestamp
            FROM price_data
            WHERE 1=1
                {ticker_filter}
                {date_filter}
        ),
        gaps AS (
            SELECT
                ticker,
                prev_timestamp AS gap_start,
                timestamp AS gap_end,
                EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) / 86400 AS gap_days
            FROM ordered_data
            WHERE prev_timestamp IS NOT NULL
                AND EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) / 86400 > :min_gap_days
        )
        SELECT
            ticker,
            gap_start,
            gap_end,
            gap_days
        FROM gaps
        ORDER BY ticker, gap_start
        """

        # Build filter conditions
        ticker_filter = "AND ticker = :ticker" if ticker else ""
        date_filter = ""
        if start_date:
            date_filter += "AND timestamp >= :start_date"
        if end_date:
            date_filter += "AND timestamp <= :end_date"

        query = query.format(
            ticker_filter=ticker_filter,
            date_filter=date_filter
        )

        # Execute query
        params = {'min_gap_days': min_gap_days}
        if ticker:
            params['ticker'] = ticker
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        result = self.db.execute(text(query), params)
        gaps = []
        for row in result:
            gaps.append({
                'ticker': row.ticker,
                'gap_start': row.gap_start,
                'gap_end': row.gap_end,
                'gap_days': int(row.gap_days)
            })

        return gaps

    def check_duplicates(self, ticker: str = None) -> List[Dict[str, Any]]:
        """
        Check for duplicate records (should be prevented by primary key).

        Returns:
            List of any duplicate ticker+timestamp combinations
        """
        query = self.db.query(
            PriceData.ticker,
            PriceData.timestamp,
            func.count().label('count')
        ).group_by(
            PriceData.ticker,
            PriceData.timestamp
        ).having(func.count() > 1)

        if ticker:
            query = query.filter(PriceData.ticker == ticker)

        duplicates = []
        for row in query.all():
            duplicates.append({
                'ticker': row.ticker,
                'timestamp': row.timestamp,
                'count': row.count
            })

        return duplicates

    def check_missing_values(self, ticker: str = None) -> List[Dict[str, Any]]:
        """
        Check for NULL/missing values in critical fields.
        """
        missing = []

        # Check for NULL values in required fields
        query = self.db.query(PriceData).filter(
            (PriceData.open.is_(None)) |
            (PriceData.high.is_(None)) |
            (PriceData.low.is_(None)) |
            (PriceData.close.is_(None)) |
            (PriceData.volume.is_(None))
        )

        if ticker:
            query = query.filter(PriceData.ticker == ticker)

        for record in query.limit(100).all():
            null_fields = []
            if record.open is None:
                null_fields.append('open')
            if record.high is None:
                null_fields.append('high')
            if record.low is None:
                null_fields.append('low')
            if record.close is None:
                null_fields.append('close')
            if record.volume is None:
                null_fields.append('volume')

            missing.append({
                'ticker': record.ticker,
                'timestamp': record.timestamp,
                'type': 'missing_values',
                'details': f'NULL fields: {", ".join(null_fields)}'
            })

        return missing

    def check_data_anomalies(self, ticker: str = None) -> List[Dict[str, Any]]:
        """
        Check for data anomalies like:
        - Zero or negative prices
        - Zero volume
        - OHLC relationship violations
        - Negative volume
        """
        anomalies = []

        # Check for invalid prices
        invalid_prices = self.db.query(PriceData).filter(
            (PriceData.open <= 0) |
            (PriceData.high <= 0) |
            (PriceData.low <= 0) |
            (PriceData.close <= 0)
        )
        if ticker:
            invalid_prices = invalid_prices.filter(PriceData.ticker == ticker)

        for record in invalid_prices.limit(100).all():
            anomalies.append({
                'ticker': record.ticker,
                'timestamp': record.timestamp,
                'type': 'invalid_price',
                'details': f'O:{record.open} H:{record.high} L:{record.low} C:{record.close}'
            })

        # Check for OHLC relationship violations
        # High should be >= Open, Close, Low
        # Low should be <= Open, Close, High
        ohlc_violations = self.db.query(PriceData).filter(
            (PriceData.high < PriceData.low) |
            (PriceData.high < PriceData.open) |
            (PriceData.high < PriceData.close) |
            (PriceData.low > PriceData.open) |
            (PriceData.low > PriceData.close)
        )
        if ticker:
            ohlc_violations = ohlc_violations.filter(PriceData.ticker == ticker)

        for record in ohlc_violations.limit(100).all():
            violations = []
            if record.high < record.low:
                violations.append('high<low')
            if record.high < record.open:
                violations.append('high<open')
            if record.high < record.close:
                violations.append('high<close')
            if record.low > record.open:
                violations.append('low>open')
            if record.low > record.close:
                violations.append('low>close')

            anomalies.append({
                'ticker': record.ticker,
                'timestamp': record.timestamp,
                'type': 'ohlc_violation',
                'details': f'{", ".join(violations)} | O:{record.open} H:{record.high} L:{record.low} C:{record.close}'
            })

        # Check for zero volume
        zero_volume = self.db.query(PriceData).filter(PriceData.volume == 0)
        if ticker:
            zero_volume = zero_volume.filter(PriceData.ticker == ticker)

        for record in zero_volume.limit(100).all():
            anomalies.append({
                'ticker': record.ticker,
                'timestamp': record.timestamp,
                'type': 'zero_volume',
                'details': f'Price: {record.close}'
            })

        # Check for negative volume
        negative_volume = self.db.query(PriceData).filter(PriceData.volume < 0)
        if ticker:
            negative_volume = negative_volume.filter(PriceData.ticker == ticker)

        for record in negative_volume.limit(100).all():
            anomalies.append({
                'ticker': record.ticker,
                'timestamp': record.timestamp,
                'type': 'negative_volume',
                'details': f'Volume: {record.volume}'
            })

        return anomalies

    def get_recent_activity(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get data ingestion activity for the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)

        query = self.db.query(
            func.date_trunc('day', PriceData.timestamp).label('date'),
            func.count(PriceData.ticker).label('records'),
            func.count(func.distinct(PriceData.ticker)).label('unique_tickers')
        ).filter(
            PriceData.timestamp >= cutoff_date
        ).group_by(
            func.date_trunc('day', PriceData.timestamp)
        ).order_by(
            func.date_trunc('day', PriceData.timestamp).desc()
        )

        activity = []
        for row in query.all():
            activity.append({
                'date': row.date,
                'records': row.records,
                'unique_tickers': row.unique_tickers
            })

        return activity


def print_summary_report(summaries: List[Dict[str, Any]]):
    """Print data summary report."""
    print("\n" + "="*80)
    print("DATA SUMMARY REPORT")
    print("="*80)
    print(f"\n{'Ticker':<8} {'Records':<10} {'Earliest':<12} {'Latest':<12} {'Days':<8} {'Complete':<10}")
    print("-"*80)

    for s in summaries:
        earliest = s['earliest_date'].strftime('%Y-%m-%d') if s['earliest_date'] else 'N/A'
        latest = s['latest_date'].strftime('%Y-%m-%d') if s['latest_date'] else 'N/A'
        completeness = f"{s['completeness_pct']:.1f}%" if s['completeness_pct'] > 0 else 'N/A'

        print(f"{s['ticker']:<8} {s['record_count']:<10} {earliest:<12} {latest:<12} {s['days_span']:<8} {completeness:<10}")

    total_records = sum(s['record_count'] for s in summaries)
    print("-"*80)
    print(f"Total: {len(summaries)} tickers, {total_records:,} records")


def print_gaps_report(gaps: List[Dict[str, Any]]):
    """Print data gaps report."""
    if not gaps:
        print("\n[OK] No significant data gaps found!")
        return

    print("\n" + "="*80)
    print("DATA GAPS REPORT")
    print("="*80)
    print(f"\n{'Ticker':<8} {'Gap Start':<20} {'Gap End':<20} {'Days':<8}")
    print("-"*80)

    for gap in gaps:
        gap_start = gap['gap_start'].strftime('%Y-%m-%d %H:%M')
        gap_end = gap['gap_end'].strftime('%Y-%m-%d %H:%M')
        print(f"{gap['ticker']:<8} {gap_start:<20} {gap_end:<20} {gap['gap_days']:<8}")

    print("-"*80)
    print(f"Total gaps: {len(gaps)}")


def print_anomalies_report(anomalies: List[Dict[str, Any]]):
    """Print data anomalies report."""
    if not anomalies:
        print("\n[OK] No data anomalies detected!")
        return

    print("\n" + "="*80)
    print("DATA ANOMALIES REPORT")
    print("="*80)
    print(f"\n{'Ticker':<8} {'Date':<12} {'Type':<20} {'Details':<30}")
    print("-"*80)

    for anomaly in anomalies:
        date_str = anomaly['timestamp'].strftime('%Y-%m-%d')
        print(f"{anomaly['ticker']:<8} {date_str:<12} {anomaly['type']:<20} {anomaly['details']:<30}")

    print("-"*80)
    print(f"Total anomalies: {len(anomalies)}")


def print_activity_report(activity: List[Dict[str, Any]]):
    """Print recent activity report."""
    print("\n" + "="*80)
    print("RECENT DATA INGESTION ACTIVITY")
    print("="*80)
    print(f"\n{'Date':<12} {'Records':<10} {'Unique Tickers':<15}")
    print("-"*80)

    for a in activity:
        date_str = a['date'].strftime('%Y-%m-%d')
        print(f"{date_str:<12} {a['records']:<10} {a['unique_tickers']:<15}")

    if not activity:
        print("No recent activity found")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Check data quality and identify issues'
    )

    parser.add_argument('--ticker', type=str, help='Check specific ticker only')
    parser.add_argument('--gaps-only', action='store_true', help='Only show gaps report')
    parser.add_argument('--start-date', type=str, help='Start date for gap analysis (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date for gap analysis (YYYY-MM-DD)')
    parser.add_argument('--min-gap-days', type=int, default=2, help='Minimum gap size to report (default: 2)')

    args = parser.parse_args()

    # Parse dates
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else None
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else None

    # Create database session
    db = SessionLocal()

    try:
        checker = DataQualityChecker(db)

        if not args.gaps_only:
            # Summary report
            summaries = checker.get_data_summary(args.ticker)
            print_summary_report(summaries)

            # Recent activity
            activity = checker.get_recent_activity(days=7)
            print_activity_report(activity)

            # Check for duplicates
            duplicates = checker.check_duplicates(args.ticker)
            if duplicates:
                print("\n[WARNING] Duplicate records found!")
                for dup in duplicates:
                    print(f"  {dup['ticker']} @ {dup['timestamp']}: {dup['count']} records")
            else:
                print("\n[OK] No duplicate records")

            # Check for missing values
            missing = checker.check_missing_values(args.ticker)
            if missing:
                print("\n[WARNING] Missing/NULL values found!")
                for m in missing[:10]:  # Show first 10
                    date_str = m['timestamp'].strftime('%Y-%m-%d')
                    print(f"  {m['ticker']} @ {date_str}: {m['details']}")
                if len(missing) > 10:
                    print(f"  ... and {len(missing) - 10} more")
            else:
                print("\n[OK] No missing values")

            # Check for anomalies
            anomalies = checker.check_data_anomalies(args.ticker)
            print_anomalies_report(anomalies)

        # Gaps analysis
        gaps = checker.find_gaps(
            ticker=args.ticker,
            start_date=start_date,
            end_date=end_date,
            min_gap_days=args.min_gap_days
        )
        print_gaps_report(gaps)

        print("\n" + "="*80)
        print("Quality check complete!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"Error during quality check: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
