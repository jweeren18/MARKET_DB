"""
Test script for Portfolio Analytics Service.

Tests all analytics calculations with real portfolio data.
Run: python scripts/test_analytics.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Portfolio, Holding, Transaction, Ticker, PriceData
from app.services.analytics_service import AnalyticsService


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def test_pl_calculation(db: Session, portfolio_id):
    """Test P&L calculation."""
    print_section("Testing P&L Calculation")

    analytics_service = AnalyticsService(db)

    try:
        pl = analytics_service.calculate_portfolio_pl(portfolio_id)

        print(f"Total Cost Basis: ${pl.total_cost_basis:,.2f}")
        print(f"Current Value: ${pl.total_current_value:,.2f}")
        print(f"Total Gain/Loss: ${pl.total_gain_loss:,.2f} ({pl.total_gain_loss_pct:.2f}%)")
        print(f"  - Unrealized: ${pl.total_unrealized_gain_loss:,.2f} ({pl.total_unrealized_gain_loss_pct:.2f}%)")
        print(f"  - Realized: ${pl.total_realized_gain_loss:,.2f}")
        print(f"Daily Change: ${pl.daily_change:,.2f} ({pl.daily_change_pct:.2f}%)")

        print(f"\nHoldings Breakdown ({len(pl.holdings_breakdown)} positions):")
        for holding in pl.holdings_breakdown:
            print(f"  {holding.ticker}: ${holding.current_value:,.2f} "
                  f"(Gain: ${holding.unrealized_gain_loss:,.2f}, {holding.unrealized_gain_loss_pct:.2f}%)")

        print("\n[OK] P&L calculation completed successfully")
        return True

    except Exception as e:
        print(f"\n[ERROR] P&L calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_returns_calculation(db: Session, portfolio_id):
    """Test returns calculation."""
    print_section("Testing Returns Calculation")

    analytics_service = AnalyticsService(db)

    try:
        # Test default period (all time)
        returns = analytics_service.calculate_returns(portfolio_id)

        print(f"Period: {returns.start_date.date()} to {returns.end_date.date()} ({returns.period_days} days)")
        print(f"Time-Weighted Return (TWR): {returns.time_weighted_return:.2f}%")
        print(f"Money-Weighted Return (MWR/IRR): {returns.money_weighted_return:.2f}%")

        if returns.annualized_twr:
            print(f"Annualized TWR: {returns.annualized_twr:.2f}%")
            print(f"Annualized MWR: {returns.annualized_mwr:.2f}%")

        # Test specific period (last 90 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        returns_90d = analytics_service.calculate_returns(portfolio_id, start_date, end_date)

        print(f"\nLast 90 Days:")
        print(f"TWR: {returns_90d.time_weighted_return:.2f}%")
        print(f"MWR: {returns_90d.money_weighted_return:.2f}%")

        print("\n[OK] Returns calculation completed successfully")
        return True

    except Exception as e:
        print(f"\n[ERROR] Returns calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_allocations_calculation(db: Session, portfolio_id):
    """Test allocations calculation."""
    print_section("Testing Allocations Calculation")

    analytics_service = AnalyticsService(db)

    try:
        allocations = analytics_service.calculate_allocations(portfolio_id)

        print("By Sector:")
        for item in allocations.by_sector:
            print(f"  {item.category}: ${item.value:,.2f} ({item.percentage:.2f}%) - {item.count} holdings")

        print("\nBy Market Cap:")
        for item in allocations.by_market_cap:
            print(f"  {item.category}: ${item.value:,.2f} ({item.percentage:.2f}%) - {item.count} holdings")

        print("\nBy Asset Type:")
        for item in allocations.by_asset_type:
            print(f"  {item.category}: ${item.value:,.2f} ({item.percentage:.2f}%) - {item.count} holdings")

        print("\nTop Holdings:")
        for holding in allocations.top_holdings[:5]:
            print(f"  {holding['ticker']}: ${holding['value']:,.2f} ({holding['percentage']:.2f}%)")

        print("\n[OK] Allocations calculation completed successfully")
        return True

    except Exception as e:
        print(f"\n[ERROR] Allocations calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_metrics_calculation(db: Session, portfolio_id):
    """Test risk metrics calculation."""
    print_section("Testing Risk Metrics Calculation")

    analytics_service = AnalyticsService(db)

    try:
        risk_metrics = analytics_service.calculate_risk_metrics(
            portfolio_id,
            lookback_days=252,
            benchmark_ticker="SPY",
            risk_free_rate=0.04
        )

        print(f"Calculation Period: {risk_metrics.calculation_period_days} days")
        print(f"Benchmark: {risk_metrics.benchmark_ticker}")
        print(f"\nRisk Metrics:")
        print(f"  Volatility (annualized): {risk_metrics.volatility:.2f}%")
        print(f"  Beta (vs {risk_metrics.benchmark_ticker}): {risk_metrics.beta:.2f}")
        print(f"  Sharpe Ratio: {risk_metrics.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: ${risk_metrics.max_drawdown:,.2f} ({risk_metrics.max_drawdown_pct:.2f}%)")
        print(f"  Value at Risk (95%): ${risk_metrics.value_at_risk_95:,.2f}")

        # Interpret metrics
        print("\nInterpretation:")
        if float(risk_metrics.beta) > 1.2:
            print("  - High beta: Portfolio is more volatile than the market")
        elif float(risk_metrics.beta) < 0.8:
            print("  - Low beta: Portfolio is less volatile than the market")
        else:
            print("  - Moderate beta: Portfolio moves roughly with the market")

        if float(risk_metrics.sharpe_ratio) > 1.0:
            print("  - Good Sharpe ratio: Strong risk-adjusted returns")
        elif float(risk_metrics.sharpe_ratio) > 0.5:
            print("  - Acceptable Sharpe ratio: Moderate risk-adjusted returns")
        else:
            print("  - Low Sharpe ratio: Poor risk-adjusted returns")

        print("\n[OK] Risk metrics calculation completed successfully")
        return True

    except Exception as e:
        print(f"\n[ERROR] Risk metrics calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_history(db: Session, portfolio_id):
    """Test performance history retrieval."""
    print_section("Testing Performance History")

    analytics_service = AnalyticsService(db)

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        history = analytics_service.get_performance_history(portfolio_id, start_date, end_date)

        print(f"Period: {history.start_date.date()} to {history.end_date.date()}")
        print(f"Data Points: {len(history.data_points)}")
        print(f"Total Return: {history.total_return:.2f}%")
        print(f"Annualized Return: {history.annualized_return:.2f}%")

        if history.data_points:
            print("\nFirst 5 data points:")
            for point in history.data_points[:5]:
                print(f"  {point.date.date()}: ${point.portfolio_value:,.2f} "
                      f"(Daily: {point.daily_return:.2f}%, Cumulative: {point.cumulative_return:.2f}%)")

            if len(history.data_points) > 5:
                print("  ...")
                last_point = history.data_points[-1]
                print(f"  {last_point.date.date()}: ${last_point.portfolio_value:,.2f} "
                      f"(Daily: {last_point.daily_return:.2f}%, Cumulative: {last_point.cumulative_return:.2f}%)")

        print("\n[OK] Performance history retrieval completed successfully")
        return True

    except Exception as e:
        print(f"\n[ERROR] Performance history retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complete_analytics(db: Session, portfolio_id):
    """Test complete analytics retrieval."""
    print_section("Testing Complete Analytics")

    analytics_service = AnalyticsService(db)

    try:
        analytics = analytics_service.get_complete_analytics(portfolio_id)

        print(f"Portfolio ID: {analytics.portfolio_id}")
        print(f"As of Date: {analytics.as_of_date}")

        print("\n--- Summary ---")
        print(f"Total Value: ${analytics.profit_loss.total_current_value:,.2f}")
        print(f"Total Gain/Loss: ${analytics.profit_loss.total_gain_loss:,.2f} ({analytics.profit_loss.total_gain_loss_pct:.2f}%)")
        print(f"Time-Weighted Return: {analytics.returns.time_weighted_return:.2f}%")
        print(f"Sharpe Ratio: {analytics.risk_metrics.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {analytics.risk_metrics.max_drawdown_pct:.2f}%")

        print("\n[OK] Complete analytics retrieval completed successfully")
        return True

    except Exception as e:
        print(f"\n[ERROR] Complete analytics retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_test_portfolio(db: Session):
    """Get a portfolio for testing (use first available)."""
    portfolio = db.query(Portfolio).first()

    if not portfolio:
        print("\n[WARNING] No portfolios found in database.")
        print("Please create a portfolio and add holdings first.")
        print("\nExample:")
        print("  1. Start backend: cd backend && uvicorn app.main:app --reload")
        print("  2. Create portfolio: POST /api/portfolios")
        print("  3. Add holdings: POST /api/portfolios/{id}/holdings")
        return None

    # Check if portfolio has holdings
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
    if not holdings:
        print(f"\n[WARNING] Portfolio '{portfolio.name}' has no holdings.")
        print("Please add holdings to test analytics.")
        return None

    # Check if price data exists
    tickers = [h.ticker for h in holdings]
    price_data_count = db.query(PriceData).filter(PriceData.ticker.in_(tickers)).count()
    if price_data_count == 0:
        print(f"\n[WARNING] No price data found for portfolio holdings.")
        print("Please run backfill: python scripts/backfill_historical_data.py")
        return None

    return portfolio


def main():
    """Run all analytics tests."""
    print_section("Portfolio Analytics Service - Test Suite")

    db = SessionLocal()

    try:
        # Get test portfolio
        portfolio = get_test_portfolio(db)
        if not portfolio:
            return

        print(f"Testing with portfolio: {portfolio.name} (ID: {portfolio.id})")

        # Run all tests
        results = {
            "P&L Calculation": test_pl_calculation(db, portfolio.id),
            "Returns Calculation": test_returns_calculation(db, portfolio.id),
            "Allocations Calculation": test_allocations_calculation(db, portfolio.id),
            "Risk Metrics Calculation": test_risk_metrics_calculation(db, portfolio.id),
            "Performance History": test_performance_history(db, portfolio.id),
            "Complete Analytics": test_complete_analytics(db, portfolio.id),
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
            print("\n[OK] All tests passed! Analytics service is working correctly.")
        else:
            print(f"\n[WARNING] {total - passed} test(s) failed. Check errors above.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
