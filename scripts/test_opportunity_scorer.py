"""
Test script for Opportunity Scorer.

Tests the 10x opportunity scoring algorithm with real data.
Run: python scripts/test_opportunity_scorer.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Ticker, PriceData
from app.services.opportunity_scorer import OpportunityScorer


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def test_score_single_ticker(db: Session, ticker: str):
    """Test scoring a single ticker."""
    print_section(f"Testing Opportunity Scoring for {ticker}")

    scorer = OpportunityScorer(db)

    try:
        result = scorer.score_ticker(ticker, benchmark_ticker="SPY")

        if "error" in result:
            print(f"[WARNING] Could not score {ticker}: {result.get('message')}")
            return False

        # Print overall score
        print(f"Ticker: {result['ticker']}")
        print(f"Overall Score: {result['overall_score']:.1f}/100")
        print(f"Confidence: {result['confidence']:.1f}%")
        print(f"Timestamp: {result['timestamp']}")

        # Print scenarios
        print(f"\nScenarios:")
        print(f"  Bull Case: {result['scenarios']['bull']:.1f}")
        print(f"  Base Case: {result['scenarios']['base']:.1f}")
        print(f"  Bear Case: {result['scenarios']['bear']:.1f}")

        # Print component breakdown
        print(f"\nComponent Breakdown:")
        for comp_name, comp_data in result['components'].items():
            print(f"\n  {comp_name.replace('_', ' ').title()}:")
            print(f"    Score: {comp_data['score']:.1f}/100")
            print(f"    Weight: {comp_data['weight']*100:.0f}%")
            print(f"    Contribution: {comp_data['contribution']:.1f} points")

            # Print top detail
            if comp_data['details']:
                first_detail = list(comp_data['details'].values())[0]
                # Skip non-dict entries (like "sector": "Technology")
                if isinstance(first_detail, dict):
                    print(f"    Sample: {first_detail['reason']}")

        # Print key drivers
        if result['key_drivers']:
            print(f"\nKey Drivers ({len(result['key_drivers'])}):")
            for driver in result['key_drivers'][:3]:
                print(f"  • {driver}")

        # Print risks
        if result['risks']:
            print(f"\nRisks ({len(result['risks'])}):")
            for risk in result['risks'][:3]:
                print(f"  • {risk}")

        print("\n[OK] Scoring completed successfully")
        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to score {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_score_multiple_tickers(db: Session, tickers: list):
    """Test scoring multiple tickers."""
    print_section("Testing Batch Scoring")

    scorer = OpportunityScorer(db)

    results = []
    for ticker in tickers:
        try:
            result = scorer.score_ticker(ticker, benchmark_ticker="SPY")
            if "error" not in result:
                results.append({
                    "ticker": ticker,
                    "score": result["overall_score"],
                    "confidence": result["confidence"]
                })
                print(f"[OK] {ticker}: Score={result['overall_score']:.1f}, Confidence={result['confidence']:.0f}%")
            else:
                print(f"[SKIP] {ticker}: {result.get('message', 'Insufficient data')}")
        except Exception as e:
            print(f"[ERROR] {ticker}: {e}")

    if results:
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        print(f"\nTop Opportunities:")
        for i, r in enumerate(results[:5], 1):
            print(f"  {i}. {r['ticker']}: {r['score']:.1f} (confidence: {r['confidence']:.0f}%)")

    return len(results) > 0


def test_score_all_tickers(db: Session):
    """Test scoring all active tickers."""
    print_section("Testing Score All Tickers")

    scorer = OpportunityScorer(db)

    try:
        results = scorer.score_all_tickers(
            min_confidence=50.0,
            benchmark_ticker="SPY"
        )

        print(f"Total tickers: {results['total_tickers']}")
        print(f"Successfully scored: {results['scored']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Errors: {len(results.get('errors', []))}")

        if results['scores']:
            print(f"\nTop 10 Opportunities:")
            for i, score in enumerate(results['scores'][:10], 1):
                print(f"  {i}. {score['ticker']}: {score['score']:.1f} "
                     f"(confidence: {score['confidence']:.0f}%)")

        if results.get('errors'):
            print(f"\nErrors:")
            for error in results['errors'][:3]:
                print(f"  • {error['ticker']}: {error['error']}")

        print("\n[OK] Batch scoring completed successfully")
        return True

    except Exception as e:
        print(f"\n[ERROR] Batch scoring failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_component_scores(db: Session, ticker: str):
    """Test detailed component scoring."""
    print_section(f"Testing Component Scores for {ticker}")

    scorer = OpportunityScorer(db)

    try:
        result = scorer.score_ticker(ticker, benchmark_ticker="SPY")

        if "error" in result:
            print(f"[WARNING] Could not score {ticker}")
            return False

        print(f"Detailed Component Analysis:\n")

        for comp_name, comp_data in result['components'].items():
            print(f"{comp_name.replace('_', ' ').upper()}:")
            print(f"  Component Score: {comp_data['score']:.2f}/100")
            print(f"  Contribution to Total: {comp_data['contribution']:.2f} points")
            print(f"  Weight: {comp_data['weight']*100:.0f}%")
            print(f"\n  Details:")

            for detail_name, detail_data in comp_data['details'].items():
                print(f"    {detail_name.replace('_', ' ').title()}:")
                # Skip non-dict entries (like "sector": "Technology")
                if isinstance(detail_data, dict):
                    print(f"      Value: {detail_data.get('value', 0):.2f}")
                    print(f"      {detail_data['reason']}")
                else:
                    print(f"      {detail_data}")

            print()

        print("[OK] Component analysis completed")
        return True

    except Exception as e:
        print(f"\n[ERROR] Component analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_test_tickers(db: Session, count: int = 5):
    """Get tickers for testing (with sufficient data)."""
    tickers = db.query(Ticker).filter(Ticker.is_active == True).all()

    suitable_tickers = []
    for ticker_obj in tickers:
        # Check if has price data and indicators
        price_count = db.query(PriceData).filter(
            PriceData.ticker == ticker_obj.ticker
        ).count()

        if price_count >= 100:  # Need sufficient data
            suitable_tickers.append(ticker_obj.ticker)

        if len(suitable_tickers) >= count:
            break

    return suitable_tickers


def main():
    """Run all opportunity scorer tests."""
    print_section("Opportunity Scorer - Test Suite")

    db = SessionLocal()

    try:
        # Get test tickers
        test_tickers = get_test_tickers(db, count=5)

        if not test_tickers:
            print("\n[WARNING] No suitable tickers found for testing.")
            print("Please ensure you have:")
            print("  1. Active tickers in the database")
            print("  2. At least 100 days of price data per ticker")
            print("  3. Calculated technical indicators")
            print("\nRun:")
            print("  python scripts/backfill_historical_data.py")
            print("  python backend/jobs/calculate_indicators.py --all")
            return

        print(f"Testing with tickers: {', '.join(test_tickers)}")

        # Run tests
        results = {
            "Single Ticker Score": test_score_single_ticker(db, test_tickers[0]),
            "Multiple Tickers": test_score_multiple_tickers(db, test_tickers[:3]),
            "Component Analysis": test_component_scores(db, test_tickers[0]),
            "Score All Tickers": test_score_all_tickers(db),
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
            print("\n[OK] All tests passed! Opportunity scorer is working correctly.")
            print("\nNext steps:")
            print("  1. Score all tickers:")
            print("     python backend/jobs/score_opportunities.py --all")
            print("\n  2. Test API endpoints:")
            print("     uvicorn app.main:app --reload")
            print("     Visit http://localhost:8000/docs")
            print("\n  3. View opportunities:")
            print("     GET /api/opportunities?min_score=60")
        else:
            print(f"\n[WARNING] {total - passed} test(s) failed. Check errors above.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
