"""
Analytics service - portfolio analytics calculations.

Implements:
- P&L calculations (realized/unrealized gains)
- Returns calculations (TWR and MWR/IRR)
- Asset allocation breakdowns
- Risk metrics (volatility, beta, Sharpe ratio, max drawdown)
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import UUID
import numpy as np
import pandas as pd

from app.models import Portfolio, Holding, Transaction, PriceData, Ticker
from app.schemas.analytics import (
    PortfolioAnalytics,
    PortfolioPL,
    PLBreakdown,
    ReturnsMetrics,
    AllocationBreakdown,
    AllocationItem,
    RiskMetrics,
    PerformanceHistory,
    PerformancePoint,
)
from app.services.market_data_service import MarketDataService


class AnalyticsService:
    """Service class for portfolio analytics calculations."""

    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService(db)

    # ==================== P&L Calculations ====================

    def calculate_portfolio_pl(self, portfolio_id: UUID) -> PortfolioPL:
        """
        Calculate comprehensive P&L for a portfolio.

        Returns:
            PortfolioPL with total and per-holding breakdowns
        """
        holdings = self.db.query(Holding).filter(
            Holding.portfolio_id == portfolio_id
        ).all()

        if not holdings:
            return self._empty_pl()

        holdings_breakdown = []
        total_cost_basis = Decimal("0")
        total_current_value = Decimal("0")
        total_unrealized_gl = Decimal("0")
        total_realized_gl = Decimal("0")

        # Calculate per-holding P&L
        for holding in holdings:
            current_price = self._get_latest_price(holding.ticker)
            if current_price is None:
                continue  # Skip if price unavailable

            current_value = holding.quantity * current_price
            unrealized_gl = current_value - holding.cost_basis
            unrealized_gl_pct = (unrealized_gl / holding.cost_basis * 100) if holding.cost_basis > 0 else Decimal("0")

            # Get realized gains from transactions
            realized_gl = self._calculate_realized_gains(portfolio_id, holding.ticker)

            breakdown = PLBreakdown(
                ticker=holding.ticker,
                quantity=holding.quantity,
                cost_basis=holding.cost_basis,
                current_price=current_price,
                current_value=current_value,
                unrealized_gain_loss=unrealized_gl,
                unrealized_gain_loss_pct=unrealized_gl_pct,
                realized_gain_loss=realized_gl,
                total_gain_loss=unrealized_gl + realized_gl,
            )
            holdings_breakdown.append(breakdown)

            total_cost_basis += holding.cost_basis
            total_current_value += current_value
            total_unrealized_gl += unrealized_gl
            total_realized_gl += realized_gl

        # Calculate daily change
        daily_change, daily_change_pct = self._calculate_daily_change(holdings)

        # Calculate totals
        total_gl = total_unrealized_gl + total_realized_gl
        total_unrealized_gl_pct = (total_unrealized_gl / total_cost_basis * 100) if total_cost_basis > 0 else Decimal("0")
        total_gl_pct = (total_gl / total_cost_basis * 100) if total_cost_basis > 0 else Decimal("0")

        return PortfolioPL(
            total_cost_basis=total_cost_basis,
            total_current_value=total_current_value,
            total_unrealized_gain_loss=total_unrealized_gl,
            total_unrealized_gain_loss_pct=total_unrealized_gl_pct,
            total_realized_gain_loss=total_realized_gl,
            total_gain_loss=total_gl,
            total_gain_loss_pct=total_gl_pct,
            daily_change=daily_change,
            daily_change_pct=daily_change_pct,
            holdings_breakdown=holdings_breakdown,
        )

    def _calculate_realized_gains(self, portfolio_id: UUID, ticker: str) -> Decimal:
        """Calculate realized gains from SELL transactions."""
        sell_transactions = self.db.query(Transaction).filter(
            Transaction.portfolio_id == portfolio_id,
            Transaction.ticker == ticker,
            Transaction.transaction_type == "SELL"
        ).all()

        # Simplified: Would need FIFO/LIFO logic for accurate cost basis
        # For now, return 0 (future enhancement)
        return Decimal("0")

    def _calculate_daily_change(self, holdings: List[Holding]) -> Tuple[Decimal, Decimal]:
        """Calculate portfolio's daily change in value and percentage."""
        if not holdings:
            return Decimal("0"), Decimal("0")

        total_value_today = Decimal("0")
        total_value_yesterday = Decimal("0")

        for holding in holdings:
            price_today = self._get_latest_price(holding.ticker)
            price_yesterday = self._get_price_n_days_ago(holding.ticker, 1)

            if price_today and price_yesterday:
                total_value_today += holding.quantity * price_today
                total_value_yesterday += holding.quantity * price_yesterday

        daily_change = total_value_today - total_value_yesterday
        daily_change_pct = (daily_change / total_value_yesterday * 100) if total_value_yesterday > 0 else Decimal("0")

        return daily_change, daily_change_pct

    # ==================== Returns Calculations ====================

    def calculate_returns(
        self,
        portfolio_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ReturnsMetrics:
        """
        Calculate time-weighted return (TWR) and money-weighted return (MWR/IRR).

        Args:
            portfolio_id: Portfolio UUID
            start_date: Start date for calculation (default: earliest transaction)
            end_date: End date for calculation (default: today)

        Returns:
            ReturnsMetrics with TWR and MWR/IRR
        """
        # Get transactions in date range
        transactions = self._get_transactions_in_range(portfolio_id, start_date, end_date)

        if not transactions:
            return self._empty_returns(start_date or datetime.now(), end_date or datetime.now())

        # Determine actual date range
        actual_start = start_date or min(t.transaction_date for t in transactions)
        actual_end = end_date or datetime.now()
        period_days = (actual_end - actual_start).days

        # Calculate TWR (time-weighted return)
        twr = self._calculate_twr(portfolio_id, actual_start, actual_end, transactions)

        # Calculate MWR/IRR (money-weighted return)
        mwr = self._calculate_mwr(portfolio_id, actual_start, actual_end, transactions)

        # Annualize if period > 365 days
        annualized_twr = None
        annualized_mwr = None
        if period_days >= 365:
            years = period_days / 365.25
            annualized_twr = ((1 + twr / 100) ** (1 / years) - 1) * 100
            annualized_mwr = ((1 + mwr / 100) ** (1 / years) - 1) * 100

        return ReturnsMetrics(
            time_weighted_return=twr,
            money_weighted_return=mwr,
            period_days=period_days,
            start_date=actual_start,
            end_date=actual_end,
            annualized_twr=Decimal(str(annualized_twr)) if annualized_twr else None,
            annualized_mwr=Decimal(str(annualized_mwr)) if annualized_mwr else None,
        )

    def _calculate_twr(
        self,
        portfolio_id: UUID,
        start_date: datetime,
        end_date: datetime,
        transactions: List[Transaction]
    ) -> Decimal:
        """
        Calculate time-weighted return (TWR).

        TWR eliminates the effect of cash flows by calculating returns
        between each cash flow event.
        """
        # Get portfolio values at start and end
        start_value = self._get_portfolio_value_at_date(portfolio_id, start_date)
        end_value = self._get_portfolio_value_at_date(portfolio_id, end_date)

        if start_value == 0:
            return Decimal("0")

        # Simplified TWR: (End Value - Start Value) / Start Value * 100
        # Full implementation would break into sub-periods between cash flows
        twr = (end_value - start_value) / start_value * 100

        return Decimal(str(round(float(twr), 2)))

    def _calculate_mwr(
        self,
        portfolio_id: UUID,
        start_date: datetime,
        end_date: datetime,
        transactions: List[Transaction]
    ) -> Decimal:
        """
        Calculate money-weighted return (MWR) / Internal Rate of Return (IRR).

        MWR accounts for the timing and size of cash flows.
        Uses Newton-Raphson method to solve for IRR.
        """
        # Build cash flow series
        cash_flows = []
        dates = []

        # Initial investment (negative)
        initial_value = self._get_portfolio_value_at_date(portfolio_id, start_date)
        cash_flows.append(-float(initial_value))
        dates.append(start_date)

        # Transaction cash flows
        for txn in transactions:
            if txn.transaction_type == "BUY":
                cash_flows.append(-float(txn.quantity * txn.price + txn.fees))
            else:  # SELL
                cash_flows.append(float(txn.quantity * txn.price - txn.fees))
            dates.append(txn.transaction_date)

        # Final value (positive)
        final_value = self._get_portfolio_value_at_date(portfolio_id, end_date)
        cash_flows.append(float(final_value))
        dates.append(end_date)

        # Calculate IRR using numpy's IRR approximation
        # Convert dates to days from start
        days_from_start = [(d - start_date).days / 365.25 for d in dates]

        # Simple IRR calculation (Newton-Raphson)
        irr = self._irr_newton_raphson(cash_flows, days_from_start)

        return Decimal(str(round(irr * 100, 2)))

    def _irr_newton_raphson(
        self,
        cash_flows: List[float],
        time_periods: List[float],
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> float:
        """
        Calculate IRR using Newton-Raphson method.

        Returns annual rate as a decimal (e.g., 0.15 for 15%)
        """
        # Initial guess
        rate = 0.1

        for _ in range(max_iterations):
            # Calculate NPV and derivative
            npv = sum(cf / ((1 + rate) ** t) for cf, t in zip(cash_flows, time_periods))
            npv_derivative = sum(-t * cf / ((1 + rate) ** (t + 1)) for cf, t in zip(cash_flows, time_periods))

            if abs(npv) < tolerance:
                return rate

            if npv_derivative == 0:
                return 0.0

            # Newton-Raphson update
            rate = rate - npv / npv_derivative

        return rate  # Return best estimate if not converged

    # ==================== Allocation Calculations ====================

    def calculate_allocations(self, portfolio_id: UUID) -> AllocationBreakdown:
        """
        Calculate portfolio allocation breakdowns by sector, market cap, and asset type.
        """
        holdings = self.db.query(Holding).filter(
            Holding.portfolio_id == portfolio_id
        ).all()

        if not holdings:
            return self._empty_allocations()

        # Get current values for each holding
        holding_values = {}
        total_value = Decimal("0")

        for holding in holdings:
            current_price = self._get_latest_price(holding.ticker)
            if current_price:
                value = holding.quantity * current_price
                holding_values[holding.ticker] = value
                total_value += value

        if total_value == 0:
            return self._empty_allocations()

        # Get ticker metadata
        tickers_data = self.db.query(Ticker).filter(
            Ticker.ticker.in_([h.ticker for h in holdings])
        ).all()
        ticker_map = {t.ticker: t for t in tickers_data}

        # Calculate allocations
        by_sector = self._calculate_sector_allocation(holding_values, ticker_map, total_value)
        by_market_cap = self._calculate_market_cap_allocation(holding_values, ticker_map, total_value)
        by_asset_type = self._calculate_asset_type_allocation(holding_values, ticker_map, total_value)
        top_holdings = self._calculate_top_holdings(holding_values, total_value)

        return AllocationBreakdown(
            by_sector=by_sector,
            by_market_cap=by_market_cap,
            by_asset_type=by_asset_type,
            top_holdings=top_holdings,
        )

    def _calculate_sector_allocation(
        self,
        holding_values: Dict[str, Decimal],
        ticker_map: Dict[str, Ticker],
        total_value: Decimal
    ) -> List[AllocationItem]:
        """Calculate allocation by sector."""
        sector_values = {}
        sector_counts = {}

        for ticker, value in holding_values.items():
            ticker_obj = ticker_map.get(ticker)
            sector = ticker_obj.sector if ticker_obj and ticker_obj.sector else "Unknown"

            sector_values[sector] = sector_values.get(sector, Decimal("0")) + value
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        return [
            AllocationItem(
                category=sector,
                value=value,
                percentage=round(value / total_value * 100, 2),
                count=sector_counts[sector]
            )
            for sector, value in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)
        ]

    def _calculate_market_cap_allocation(
        self,
        holding_values: Dict[str, Decimal],
        ticker_map: Dict[str, Ticker],
        total_value: Decimal
    ) -> List[AllocationItem]:
        """Calculate allocation by market cap category."""
        market_cap_values = {}
        market_cap_counts = {}

        for ticker, value in holding_values.items():
            ticker_obj = ticker_map.get(ticker)
            market_cap = ticker_obj.market_cap_category if ticker_obj and ticker_obj.market_cap_category else "Unknown"

            market_cap_values[market_cap] = market_cap_values.get(market_cap, Decimal("0")) + value
            market_cap_counts[market_cap] = market_cap_counts.get(market_cap, 0) + 1

        return [
            AllocationItem(
                category=market_cap,
                value=value,
                percentage=round(value / total_value * 100, 2),
                count=market_cap_counts[market_cap]
            )
            for market_cap, value in sorted(market_cap_values.items(), key=lambda x: x[1], reverse=True)
        ]

    def _calculate_asset_type_allocation(
        self,
        holding_values: Dict[str, Decimal],
        ticker_map: Dict[str, Ticker],
        total_value: Decimal
    ) -> List[AllocationItem]:
        """Calculate allocation by asset type."""
        asset_type_values = {}
        asset_type_counts = {}

        for ticker, value in holding_values.items():
            ticker_obj = ticker_map.get(ticker)
            asset_type = ticker_obj.asset_type if ticker_obj and ticker_obj.asset_type else "Unknown"

            asset_type_values[asset_type] = asset_type_values.get(asset_type, Decimal("0")) + value
            asset_type_counts[asset_type] = asset_type_counts.get(asset_type, 0) + 1

        return [
            AllocationItem(
                category=asset_type,
                value=value,
                percentage=round(value / total_value * 100, 2),
                count=asset_type_counts[asset_type]
            )
            for asset_type, value in sorted(asset_type_values.items(), key=lambda x: x[1], reverse=True)
        ]

    def _calculate_top_holdings(
        self,
        holding_values: Dict[str, Decimal],
        total_value: Decimal,
        top_n: int = 10
    ) -> List[Dict]:
        """Get top N holdings by value."""
        sorted_holdings = sorted(holding_values.items(), key=lambda x: x[1], reverse=True)[:top_n]

        return [
            {
                "ticker": ticker,
                "value": float(value),
                "percentage": float(round(value / total_value * 100, 2))
            }
            for ticker, value in sorted_holdings
        ]

    # ==================== Risk Metrics ====================

    def calculate_risk_metrics(
        self,
        portfolio_id: UUID,
        lookback_days: int = 252,
        benchmark_ticker: str = "SPY",
        risk_free_rate: float = 0.04  # 4% annual
    ) -> RiskMetrics:
        """
        Calculate portfolio risk metrics.

        Args:
            portfolio_id: Portfolio UUID
            lookback_days: Number of days for calculation (default: 252 trading days = 1 year)
            benchmark_ticker: Benchmark for beta calculation (default: SPY)
            risk_free_rate: Annual risk-free rate for Sharpe ratio (default: 4%)

        Returns:
            RiskMetrics with volatility, beta, Sharpe ratio, max drawdown, VaR
        """
        # Get portfolio performance history
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        performance = self._get_portfolio_performance_history(portfolio_id, start_date, end_date)

        if len(performance) < 30:  # Need at least 30 data points
            return self._empty_risk_metrics(lookback_days, benchmark_ticker)

        # Extract daily returns
        returns = np.array([float(p["daily_return"]) for p in performance])
        values = np.array([float(p["value"]) for p in performance])

        # Calculate volatility (annualized)
        volatility = np.std(returns) * np.sqrt(252)  # Annualize daily volatility

        # Calculate beta vs benchmark
        benchmark_returns = self._get_benchmark_returns(benchmark_ticker, start_date, end_date)
        beta = self._calculate_beta(returns, benchmark_returns) if len(benchmark_returns) > 0 else Decimal("1.0")

        # Calculate Sharpe ratio
        avg_return = np.mean(returns)
        daily_risk_free = risk_free_rate / 252
        sharpe_ratio = (avg_return - daily_risk_free) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0

        # Calculate max drawdown
        max_drawdown_value, max_drawdown_pct = self._calculate_max_drawdown(values)

        # Calculate Value at Risk (95% confidence)
        var_95 = np.percentile(returns, 5) * values[-1] if len(values) > 0 else 0

        return RiskMetrics(
            volatility=Decimal(str(round(volatility * 100, 2))),  # Convert to percentage
            beta=beta,
            sharpe_ratio=Decimal(str(round(sharpe_ratio, 2))),
            max_drawdown=Decimal(str(round(max_drawdown_value, 2))),
            max_drawdown_pct=Decimal(str(round(max_drawdown_pct, 2))),
            value_at_risk_95=Decimal(str(round(abs(var_95), 2))),
            calculation_period_days=len(performance),
            benchmark_ticker=benchmark_ticker,
        )

    def _calculate_beta(self, portfolio_returns: np.ndarray, benchmark_returns: np.ndarray) -> Decimal:
        """Calculate portfolio beta vs benchmark."""
        # Align lengths
        min_length = min(len(portfolio_returns), len(benchmark_returns))
        portfolio_returns = portfolio_returns[:min_length]
        benchmark_returns = benchmark_returns[:min_length]

        if len(portfolio_returns) < 2:
            return Decimal("1.0")

        # Beta = Covariance(portfolio, benchmark) / Variance(benchmark)
        covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)

        beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0

        return Decimal(str(round(beta, 2)))

    def _calculate_max_drawdown(self, values: np.ndarray) -> Tuple[float, float]:
        """
        Calculate maximum drawdown (peak-to-trough decline).

        Returns:
            Tuple of (max_drawdown_value, max_drawdown_percentage)
        """
        if len(values) == 0:
            return 0.0, 0.0

        cumulative_max = np.maximum.accumulate(values)
        drawdowns = values - cumulative_max
        max_drawdown_value = np.min(drawdowns)

        # Find the peak before max drawdown
        max_dd_idx = np.argmin(drawdowns)
        peak_value = cumulative_max[max_dd_idx]
        max_drawdown_pct = (max_drawdown_value / peak_value * 100) if peak_value > 0 else 0.0

        return float(max_drawdown_value), float(max_drawdown_pct)

    # ==================== Performance History ====================

    def get_performance_history(
        self,
        portfolio_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> PerformanceHistory:
        """Get portfolio performance history over time."""
        performance_data = self._get_portfolio_performance_history(portfolio_id, start_date, end_date)

        if not performance_data:
            return PerformanceHistory(
                portfolio_id=str(portfolio_id),
                start_date=start_date,
                end_date=end_date,
                data_points=[],
                total_return=Decimal("0"),
                annualized_return=Decimal("0"),
            )

        data_points = [
            PerformancePoint(
                date=p["date"],
                portfolio_value=Decimal(str(p["value"])),
                daily_return=Decimal(str(p["daily_return"])),
                cumulative_return=Decimal(str(p["cumulative_return"])),
            )
            for p in performance_data
        ]

        total_return = data_points[-1].cumulative_return if data_points else Decimal("0")

        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return = ((1 + float(total_return) / 100) ** (1 / years) - 1) * 100 if years > 0 and data_points else 0

        return PerformanceHistory(
            portfolio_id=str(portfolio_id),
            start_date=start_date,
            end_date=end_date,
            data_points=data_points,
            total_return=total_return,
            annualized_return=Decimal(str(round(annualized_return, 2))),
        )

    # ==================== Combined Analytics ====================

    def get_complete_analytics(self, portfolio_id: UUID) -> PortfolioAnalytics:
        """Get complete analytics for a portfolio."""
        return PortfolioAnalytics(
            portfolio_id=str(portfolio_id),
            as_of_date=datetime.now(),
            profit_loss=self.calculate_portfolio_pl(portfolio_id),
            returns=self.calculate_returns(portfolio_id),
            allocations=self.calculate_allocations(portfolio_id),
            risk_metrics=self.calculate_risk_metrics(portfolio_id),
        )

    # ==================== Helper Methods ====================

    def _get_latest_price(self, ticker: str) -> Optional[Decimal]:
        """Get the most recent price for a ticker."""
        latest_price = self.db.query(PriceData).filter(
            PriceData.ticker == ticker
        ).order_by(PriceData.timestamp.desc()).first()

        return latest_price.close if latest_price else None

    def _get_price_n_days_ago(self, ticker: str, days: int) -> Optional[Decimal]:
        """Get price N days ago."""
        target_date = datetime.now() - timedelta(days=days)

        price_data = self.db.query(PriceData).filter(
            PriceData.ticker == ticker,
            PriceData.timestamp <= target_date
        ).order_by(PriceData.timestamp.desc()).first()

        return price_data.close if price_data else None

    def _get_portfolio_value_at_date(self, portfolio_id: UUID, date: datetime) -> Decimal:
        """Calculate total portfolio value at a specific date."""
        holdings = self.db.query(Holding).filter(
            Holding.portfolio_id == portfolio_id,
            Holding.purchase_date <= date.date()
        ).all()

        total_value = Decimal("0")
        for holding in holdings:
            # Get price closest to target date
            price_data = self.db.query(PriceData).filter(
                PriceData.ticker == holding.ticker,
                PriceData.timestamp <= date
            ).order_by(PriceData.timestamp.desc()).first()

            if price_data:
                total_value += holding.quantity * price_data.close

        return total_value

    def _get_transactions_in_range(
        self,
        portfolio_id: UUID,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Transaction]:
        """Get transactions within date range."""
        query = self.db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id)

        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        return query.order_by(Transaction.transaction_date).all()

    def _get_portfolio_performance_history(
        self,
        portfolio_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Get daily portfolio values and returns over a period.

        Returns list of dicts with: date, value, daily_return, cumulative_return
        """
        # Get all holdings that existed during this period
        holdings = self.db.query(Holding).filter(
            Holding.portfolio_id == portfolio_id,
            Holding.purchase_date <= end_date.date()
        ).all()

        if not holdings:
            return []

        # Get all unique dates in range from price_data
        dates_query = self.db.query(func.date(PriceData.timestamp).label('date')).filter(
            PriceData.timestamp >= start_date,
            PriceData.timestamp <= end_date
        ).distinct().order_by(func.date(PriceData.timestamp))

        dates = [row.date for row in dates_query.all()]

        if not dates:
            return []

        # Calculate portfolio value for each date
        performance = []
        initial_value = None

        for date in dates:
            date_datetime = datetime.combine(date, datetime.min.time())
            portfolio_value = float(self._get_portfolio_value_at_date(portfolio_id, date_datetime))

            if initial_value is None:
                initial_value = portfolio_value

            daily_return = 0.0
            if len(performance) > 0:
                prev_value = performance[-1]["value"]
                daily_return = ((portfolio_value - prev_value) / prev_value * 100) if prev_value > 0 else 0.0

            cumulative_return = ((portfolio_value - initial_value) / initial_value * 100) if initial_value > 0 else 0.0

            performance.append({
                "date": date_datetime,
                "value": portfolio_value,
                "daily_return": daily_return,
                "cumulative_return": cumulative_return,
            })

        return performance

    def _get_benchmark_returns(self, benchmark_ticker: str, start_date: datetime, end_date: datetime) -> np.ndarray:
        """Get daily returns for benchmark ticker."""
        prices = self.db.query(PriceData).filter(
            PriceData.ticker == benchmark_ticker,
            PriceData.timestamp >= start_date,
            PriceData.timestamp <= end_date
        ).order_by(PriceData.timestamp).all()

        if len(prices) < 2:
            return np.array([])

        returns = []
        for i in range(1, len(prices)):
            daily_return = (float(prices[i].close) - float(prices[i-1].close)) / float(prices[i-1].close)
            returns.append(daily_return)

        return np.array(returns)

    # ==================== Empty Response Helpers ====================

    def _empty_pl(self) -> PortfolioPL:
        """Return empty P&L response."""
        return PortfolioPL(
            total_cost_basis=Decimal("0"),
            total_current_value=Decimal("0"),
            total_unrealized_gain_loss=Decimal("0"),
            total_unrealized_gain_loss_pct=Decimal("0"),
            total_realized_gain_loss=Decimal("0"),
            total_gain_loss=Decimal("0"),
            total_gain_loss_pct=Decimal("0"),
            daily_change=Decimal("0"),
            daily_change_pct=Decimal("0"),
            holdings_breakdown=[],
        )

    def _empty_returns(self, start_date: datetime, end_date: datetime) -> ReturnsMetrics:
        """Return empty returns response."""
        return ReturnsMetrics(
            time_weighted_return=Decimal("0"),
            money_weighted_return=Decimal("0"),
            period_days=0,
            start_date=start_date,
            end_date=end_date,
        )

    def _empty_allocations(self) -> AllocationBreakdown:
        """Return empty allocations response."""
        return AllocationBreakdown(
            by_sector=[],
            by_market_cap=[],
            by_asset_type=[],
            top_holdings=[],
        )

    def _empty_risk_metrics(self, period_days: int, benchmark_ticker: str) -> RiskMetrics:
        """Return empty risk metrics response."""
        return RiskMetrics(
            volatility=Decimal("0"),
            beta=Decimal("1.0"),
            sharpe_ratio=Decimal("0"),
            max_drawdown=Decimal("0"),
            max_drawdown_pct=Decimal("0"),
            value_at_risk_95=Decimal("0"),
            calculation_period_days=period_days,
            benchmark_ticker=benchmark_ticker,
        )
