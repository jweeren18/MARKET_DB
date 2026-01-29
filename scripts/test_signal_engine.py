"""
Test script for Signal Engine and Technical Indicators.

Tests indicator calculations, signal detection, and API access.
Run: python scripts/test_signal_engine.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Ticker, PriceData
from app.services.signal_engine import SignalEngine


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def test_indicator_calculation(db: Session, ticker: str):
    """Test technical indicator calculation for a ticker."""
    print_section(f"Testing Indicator Calculation for {ticker}")

    signal_engine = SignalEngine(db)

    try:
        result = signal_engine.calculate_indicators_for_ticker(
            ticker=ticker,
            lookback_days=252,
            force_recalculate=True  # Force recalculation for testing
        )

        if result["status"] == "success":
            print(f"[OK] Successfully calculated indicators for {ticker}")
            print(f"  Indicators calculated: {len(result['indicators_calculated'])}")
            print(f"  Sample indicators: {', '.join(result['indicators_calculated'][:10])}")
            if len(result['indicators_calculated']) > 10:
                print(f"    ... and {len(result['indicators_calculated']) - 10} more")
            print(f"  Data points processed: {result['data_points']}")
            print(f"  Stored records: {result['stored_records']}")
            return True
        else:
            print(f"[ERROR] Failed to calculate indicators: {result.get('reason', 'unknown')}")
            return False

    except Exception as e:
        print(f"[ERROR] Exception during calculation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_latest_indicators(db: Session, ticker: str):
    """Test fetching latest indicator values."""
    print_section(f"Testing Latest Indicators for {ticker}")

    signal_engine = SignalEngine(db)

    try:
        indicators = signal_engine.get_latest_indicators(ticker)

        if not indicators:
            print(f"[WARNING] No indicators found for {ticker}")
            return False

        print(f"[OK] Found {len(indicators)} indicators\n")

        # Group indicators by category
        categories = {
            "Moving Averages": ["sma_20", "sma_50", "sma_200", "ema_12", "ema_26"],
            "Momentum": ["rsi_14", "macd", "macd_signal", "macd_histogram", "roc_12"],
            "Volatility": ["bb_upper", "bb_middle", "bb_lower", "atr_14"],
            "Trend": ["adx_14", "williams_r"],
            "Stochastic": ["stochastic_k", "stochastic_d"],
            "Volume": ["volume_sma_20", "obv"]
        }

        for category, indicator_list in categories.items():
            print(f"{category}:")
            found_any = False
            for ind_name in indicator_list:
                if ind_name in indicators:
                    print(f"  {ind_name}: {indicators[ind_name]:.4f}")
                    found_any = True
            if not found_any:
                print(f"  (No indicators in this category)")
            print()

        return True

    except Exception as e:
        print(f"[ERROR] Failed to fetch indicators: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_detection(db: Session, ticker: str):
    """Test trading signal detection."""
    print_section(f"Testing Signal Detection for {ticker}")

    signal_engine = SignalEngine(db)

    try:
        signals = signal_engine.detect_signals(ticker)

        print(f"As of: {signals['as_of']}")
        print(f"Indicators analyzed: {signals['indicators_analyzed']}")
        print(f"Signals detected: {signals['signal_count']}\n")

        if signals['signals']:
            print("Detected Signals:")
            for signal in signals['signals']:
                print(f"\n  {signal['type'].upper()} - {signal['indicator']}")
                print(f"    Strength: {signal['strength']}")
                print(f"    Value: {signal['value']:.2f}")
                print(f"    Description: {signal['description']}")
        else:
            print("No strong signals detected at this time")

        print("\n[OK] Signal detection completed successfully")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to detect signals: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indicator_history(db: Session, ticker: str, indicator_name: str = "rsi_14"):
    """Test fetching indicator history."""
    print_section(f"Testing Indicator History for {ticker}/{indicator_name}")

    signal_engine = SignalEngine(db)

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        history = signal_engine.get_indicator_history(
            ticker=ticker,
            indicator_name=indicator_name,
            start_date=start_date,
            end_date=end_date,
            limit=10
        )

        if not history:
            print(f"[WARNING] No history found for {indicator_name}")
            return False

        print(f"[OK] Found {len(history)} data points (last 30 days, limited to 10)\n")
        print(f"Recent {indicator_name} values:")
        for point in history[:5]:
            print(f"  {point['timestamp'].date()}: {point['value']:.2f}")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to fetch indicator history: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indicator_summary(db: Session, ticker: str):
    """Test fetching indicator summary."""
    print_section(f"Testing Indicator Summary for {ticker}")

    signal_engine = SignalEngine(db)

    try:
        summary = signal_engine.get_indicator_summary(ticker)

        print(f"Ticker: {summary['ticker']}")
        print(f"Total indicator types: {summary['total_indicators']}\n")

        if summary['indicators']:
            print("Available Indicators:")
            for ind in summary['indicators'][:10]:
                status = "[CURRENT]" if ind['is_current'] else "[OUTDATED]"
                print(f"  {status} {ind['name']}: {ind['data_points']} data points")
                print(f"      Range: {ind['first_date'].date()} to {ind['last_date'].date()}")

            if len(summary['indicators']) > 10:
                print(f"\n  ... and {len(summary['indicators']) - 10} more indicators")

        print("\n[OK] Indicator summary retrieved successfully")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to fetch indicator summary: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_test_ticker(db: Session):
    """Get a ticker for testing (use first active ticker with price data)."""
    # Get active tickers with price data
    tickers = db.query(Ticker).filter(Ticker.is_active == True).all()

    for ticker_obj in tickers:
        price_count = db.query(PriceData).filter(
            PriceData.ticker == ticker_obj.ticker
        ).count()

        if price_count >= 100:  # Need sufficient data for indicators
            return ticker_obj.ticker

    return None


def main():
    """Run all signal engine tests."""
    print_section("Signal Engine - Test Suite")

    db = SessionLocal()

    try:
        # Get test ticker
        ticker = get_test_ticker(db)

        if not ticker:
            print("\n[WARNING] No suitable ticker found for testing.")
            print("Please ensure you have:")
            print("  1. Active tickers in the database")
            print("  2. At least 100 days of price data for at least one ticker")
            print("\nRun: python scripts/backfill_historical_data.py")
            return

        print(f"Testing with ticker: {ticker}")

        # Run all tests
        results = {
            "Indicator Calculation": test_indicator_calculation(db, ticker),
            "Latest Indicators": test_latest_indicators(db, ticker),
            "Signal Detection": test_signal_detection(db, ticker),
            "Indicator History": test_indicator_history(db, ticker),
            "Indicator Summary": test_indicator_summary(db, ticker),
        }

        # Summary
        print_section("Test Summary")
        passed = sum(results.values())
        total = len(results)

        for test_name, result in results.items():
            status = "[OK]" if result else "[FAILED]"
            print(f"{status} {test_name}")

        print(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            print("\n[OK] All tests passed! Signal engine is working correctly.")
            print("\nNext steps:")
            print("  1. Calculate indicators for all tickers:")
            print("     python backend/jobs/calculate_indicators.py --all")
            print("\n  2. Test API endpoints:")
            print("     uvicorn app.main:app --reload")
            print("     Visit http://localhost:8000/docs")
        else:
            print(f"\n[WARNING] {total - passed} test(s) failed. Check errors above.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
