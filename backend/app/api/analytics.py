"""
Analytics API endpoints for portfolio analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID

from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    PortfolioAnalytics,
    PortfolioPL,
    ReturnsMetrics,
    AllocationBreakdown,
    RiskMetrics,
    PerformanceHistory,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/portfolios/{portfolio_id}/complete", response_model=PortfolioAnalytics)
def get_complete_analytics(
    portfolio_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get complete analytics for a portfolio.

    Includes:
    - P&L (profit/loss)
    - Returns (TWR and MWR)
    - Allocations (sector, market cap, asset type)
    - Risk metrics (volatility, beta, Sharpe ratio, max drawdown)
    """
    analytics_service = AnalyticsService(db)

    try:
        return analytics_service.get_complete_analytics(portfolio_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate analytics: {str(e)}")


@router.get("/portfolios/{portfolio_id}/pl", response_model=PortfolioPL)
def get_portfolio_pl(
    portfolio_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get profit/loss breakdown for a portfolio.

    Returns:
    - Total P&L (realized + unrealized)
    - Per-holding breakdown
    - Daily change
    """
    analytics_service = AnalyticsService(db)

    try:
        return analytics_service.calculate_portfolio_pl(portfolio_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate P&L: {str(e)}")


@router.get("/portfolios/{portfolio_id}/returns", response_model=ReturnsMetrics)
def get_portfolio_returns(
    portfolio_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date for calculation"),
    end_date: Optional[datetime] = Query(None, description="End date for calculation (default: today)"),
    db: Session = Depends(get_db)
):
    """
    Get return metrics for a portfolio.

    Returns:
    - Time-weighted return (TWR)
    - Money-weighted return (MWR/IRR)
    - Annualized returns (if period > 1 year)
    """
    analytics_service = AnalyticsService(db)

    try:
        return analytics_service.calculate_returns(portfolio_id, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate returns: {str(e)}")


@router.get("/portfolios/{portfolio_id}/allocations", response_model=AllocationBreakdown)
def get_portfolio_allocations(
    portfolio_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get portfolio allocation breakdowns.

    Returns:
    - Allocation by sector
    - Allocation by market cap category
    - Allocation by asset type
    - Top holdings
    """
    analytics_service = AnalyticsService(db)

    try:
        return analytics_service.calculate_allocations(portfolio_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate allocations: {str(e)}")


@router.get("/portfolios/{portfolio_id}/risk", response_model=RiskMetrics)
def get_portfolio_risk_metrics(
    portfolio_id: UUID,
    lookback_days: int = Query(252, description="Number of days for calculation (default: 252 trading days)"),
    benchmark_ticker: str = Query("SPY", description="Benchmark ticker for beta calculation"),
    risk_free_rate: float = Query(0.04, description="Annual risk-free rate (default: 4%)"),
    db: Session = Depends(get_db)
):
    """
    Get risk metrics for a portfolio.

    Returns:
    - Volatility (annualized standard deviation)
    - Beta (vs benchmark)
    - Sharpe ratio (risk-adjusted return)
    - Maximum drawdown
    - Value at Risk (95% confidence)
    """
    analytics_service = AnalyticsService(db)

    try:
        return analytics_service.calculate_risk_metrics(
            portfolio_id,
            lookback_days=lookback_days,
            benchmark_ticker=benchmark_ticker,
            risk_free_rate=risk_free_rate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate risk metrics: {str(e)}")


@router.get("/portfolios/{portfolio_id}/performance", response_model=PerformanceHistory)
def get_portfolio_performance_history(
    portfolio_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date (default: today)"),
    db: Session = Depends(get_db)
):
    """
    Get portfolio performance history over time.

    Returns daily data points with:
    - Portfolio value
    - Daily return
    - Cumulative return
    """
    if end_date is None:
        end_date = datetime.now()

    if start_date is None:
        start_date = end_date - timedelta(days=365)  # Default to 1 year

    analytics_service = AnalyticsService(db)

    try:
        return analytics_service.get_performance_history(portfolio_id, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance history: {str(e)}")
