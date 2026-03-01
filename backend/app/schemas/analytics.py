"""
Pydantic schemas for portfolio analytics API responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime


# P&L Schemas

class PLBreakdown(BaseModel):
    """Profit/Loss breakdown for a single holding."""
    ticker: str
    quantity: Decimal
    cost_basis: Decimal
    current_price: Decimal
    current_value: Decimal
    unrealized_gain_loss: Decimal
    unrealized_gain_loss_pct: Decimal
    realized_gain_loss: Decimal = Field(default=Decimal("0"))
    total_gain_loss: Decimal


class PortfolioPL(BaseModel):
    """Overall portfolio P&L summary."""
    total_cost_basis: Decimal
    total_current_value: Decimal
    total_unrealized_gain_loss: Decimal
    total_unrealized_gain_loss_pct: Decimal
    total_realized_gain_loss: Decimal
    total_gain_loss: Decimal
    total_gain_loss_pct: Decimal
    daily_change: Decimal
    daily_change_pct: Decimal
    holdings_breakdown: List[PLBreakdown]


# Returns Schemas

class ReturnsMetrics(BaseModel):
    """Time-weighted and money-weighted returns."""
    time_weighted_return: Decimal = Field(
        description="Time-weighted return (TWR) - accounts for timing of cash flows"
    )
    money_weighted_return: Decimal = Field(
        description="Money-weighted return / Internal Rate of Return (IRR)"
    )
    period_days: int
    start_date: datetime
    end_date: datetime
    annualized_twr: Optional[Decimal] = None
    annualized_mwr: Optional[Decimal] = None


# Allocation Schemas

class AllocationItem(BaseModel):
    """Single allocation item (sector, market cap, etc.)."""
    category: str
    value: Decimal
    percentage: Decimal
    count: int = Field(description="Number of holdings in this category")


class AllocationBreakdown(BaseModel):
    """Portfolio allocation breakdowns."""
    by_sector: List[AllocationItem]
    by_market_cap: List[AllocationItem]
    by_asset_type: List[AllocationItem]
    top_holdings: List[Dict[str, Any]] = Field(
        description="Top holdings by percentage"
    )


# Risk Metrics Schemas

class RiskMetrics(BaseModel):
    """Portfolio risk metrics."""
    volatility: Decimal = Field(
        description="Annualized volatility (standard deviation of returns)"
    )
    beta: Decimal = Field(
        description="Beta vs market benchmark (e.g., S&P 500)"
    )
    sharpe_ratio: Decimal = Field(
        description="Sharpe ratio - risk-adjusted return"
    )
    max_drawdown: Decimal = Field(
        description="Maximum peak-to-trough decline"
    )
    max_drawdown_pct: Decimal
    value_at_risk_95: Decimal = Field(
        description="Value at Risk at 95% confidence level"
    )
    calculation_period_days: int
    benchmark_ticker: str = Field(default="SPY")


# Combined Analytics Response

class PortfolioAnalytics(BaseModel):
    """Complete portfolio analytics response."""
    portfolio_id: str
    as_of_date: datetime
    profit_loss: PortfolioPL
    returns: ReturnsMetrics
    allocations: AllocationBreakdown
    risk_metrics: RiskMetrics


# Performance History Schema

class PerformancePoint(BaseModel):
    """Single point in portfolio performance history."""
    date: datetime
    portfolio_value: Decimal
    daily_return: Decimal
    cumulative_return: Decimal


class PerformanceHistory(BaseModel):
    """Portfolio performance over time."""
    portfolio_id: str
    start_date: datetime
    end_date: datetime
    data_points: List[PerformancePoint]
    total_return: Decimal
    annualized_return: Decimal
