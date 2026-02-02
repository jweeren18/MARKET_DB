# Portfolio Analytics Service

Complete guide to the portfolio analytics service that provides comprehensive portfolio metrics, returns calculations, allocations, and risk analysis.

## Overview

The Analytics Service implements sophisticated portfolio analytics including:
- **P&L Calculations**: Realized and unrealized gains/losses
- **Returns Metrics**: Time-weighted return (TWR) and money-weighted return (MWR/IRR)
- **Asset Allocations**: Breakdowns by sector, market cap, and asset type
- **Risk Metrics**: Volatility, beta, Sharpe ratio, max drawdown, and Value at Risk

## Features

### 1. Profit & Loss (P&L)

Calculates comprehensive P&L for the entire portfolio and per-holding breakdowns.

**Metrics:**
- Total cost basis
- Current market value
- Unrealized gains/losses (and percentage)
- Realized gains/losses (from SELL transactions)
- Total gains/losses
- Daily change (value and percentage)

**Per-Holding Breakdown:**
- Current price
- Current value
- Unrealized P&L
- Realized P&L (future enhancement for FIFO/LIFO tracking)

**API Endpoint:**
```
GET /api/analytics/portfolios/{portfolio_id}/pl
```

**Example Response:**
```json
{
  "total_cost_basis": "50000.00",
  "total_current_value": "65000.00",
  "total_unrealized_gain_loss": "15000.00",
  "total_unrealized_gain_loss_pct": "30.00",
  "total_realized_gain_loss": "0.00",
  "total_gain_loss": "15000.00",
  "total_gain_loss_pct": "30.00",
  "daily_change": "500.00",
  "daily_change_pct": "0.77",
  "holdings_breakdown": [
    {
      "ticker": "AAPL",
      "quantity": "100",
      "cost_basis": "15000.00",
      "current_price": "185.50",
      "current_value": "18550.00",
      "unrealized_gain_loss": "3550.00",
      "unrealized_gain_loss_pct": "23.67",
      "realized_gain_loss": "0.00",
      "total_gain_loss": "3550.00"
    }
  ]
}
```

---

### 2. Returns Calculations

Calculates both time-weighted return (TWR) and money-weighted return (MWR/IRR).

#### Time-Weighted Return (TWR)
- **Purpose**: Measures investment performance independent of cash flows
- **Best for**: Comparing portfolio performance to benchmarks
- **Formula**: Eliminates impact of deposits/withdrawals by breaking returns into sub-periods

#### Money-Weighted Return (MWR/IRR)
- **Purpose**: Measures actual investor returns accounting for timing of cash flows
- **Best for**: Understanding personal investment outcomes
- **Formula**: Internal Rate of Return using Newton-Raphson method

**Features:**
- Calculates returns for any date range
- Annualizes returns for periods > 1 year
- Handles complex cash flow patterns

**API Endpoint:**
```
GET /api/analytics/portfolios/{portfolio_id}/returns
  ?start_date=2023-01-01&end_date=2024-01-01
```

**Example Response:**
```json
{
  "time_weighted_return": "25.50",
  "money_weighted_return": "22.30",
  "period_days": 365,
  "start_date": "2023-01-01T00:00:00",
  "end_date": "2024-01-01T00:00:00",
  "annualized_twr": "25.50",
  "annualized_mwr": "22.30"
}
```

---

### 3. Asset Allocations

Provides multi-dimensional portfolio allocation breakdowns.

**Allocation Types:**

1. **By Sector** (Technology, Healthcare, Financials, etc.)
2. **By Market Cap** (Large, Mid, Small, Micro)
3. **By Asset Type** (Stock, ETF, Crypto)
4. **Top Holdings** (Largest positions by value)

**API Endpoint:**
```
GET /api/analytics/portfolios/{portfolio_id}/allocations
```

**Example Response:**
```json
{
  "by_sector": [
    {
      "category": "Technology",
      "value": "35000.00",
      "percentage": "53.85",
      "count": 5
    },
    {
      "category": "Healthcare",
      "value": "20000.00",
      "percentage": "30.77",
      "count": 3
    }
  ],
  "by_market_cap": [
    {
      "category": "LARGE",
      "value": "45000.00",
      "percentage": "69.23",
      "count": 6
    }
  ],
  "by_asset_type": [
    {
      "category": "STOCK",
      "value": "60000.00",
      "percentage": "92.31",
      "count": 8
    }
  ],
  "top_holdings": [
    {
      "ticker": "AAPL",
      "value": 18550.00,
      "percentage": 28.54
    }
  ]
}
```

---

### 4. Risk Metrics

Calculates sophisticated risk measures for portfolio analysis.

**Metrics Calculated:**

1. **Volatility** (Annualized Standard Deviation)
   - Measures portfolio price fluctuation
   - Higher = more volatile/risky

2. **Beta** (vs Benchmark)
   - Measures sensitivity to market movements
   - Beta > 1: More volatile than market
   - Beta < 1: Less volatile than market
   - Beta = 1: Moves with market

3. **Sharpe Ratio** (Risk-Adjusted Return)
   - Measures return per unit of risk
   - Higher = better risk-adjusted performance
   - Formula: (Return - Risk-Free Rate) / Volatility

4. **Maximum Drawdown**
   - Largest peak-to-trough decline
   - Measures worst-case scenario

5. **Value at Risk (VaR)** at 95% confidence
   - Maximum expected loss (5% probability)
   - Useful for risk budgeting

**Configuration:**
- `lookback_days`: Historical period for calculation (default: 252 trading days)
- `benchmark_ticker`: Benchmark for beta (default: SPY)
- `risk_free_rate`: Annual risk-free rate (default: 4%)

**API Endpoint:**
```
GET /api/analytics/portfolios/{portfolio_id}/risk
  ?lookback_days=252&benchmark_ticker=SPY&risk_free_rate=0.04
```

**Example Response:**
```json
{
  "volatility": "18.50",
  "beta": "1.15",
  "sharpe_ratio": "1.25",
  "max_drawdown": "-5000.00",
  "max_drawdown_pct": "-10.50",
  "value_at_risk_95": "2500.00",
  "calculation_period_days": 252,
  "benchmark_ticker": "SPY"
}
```

---

### 5. Performance History

Returns time-series data of portfolio performance.

**Data Points:**
- Daily portfolio values
- Daily returns
- Cumulative returns
- Total and annualized returns

**API Endpoint:**
```
GET /api/analytics/portfolios/{portfolio_id}/performance
  ?start_date=2023-01-01&end_date=2024-01-01
```

**Example Response:**
```json
{
  "portfolio_id": "uuid-here",
  "start_date": "2023-01-01T00:00:00",
  "end_date": "2024-01-01T00:00:00",
  "data_points": [
    {
      "date": "2023-01-01T00:00:00",
      "portfolio_value": "50000.00",
      "daily_return": "0.00",
      "cumulative_return": "0.00"
    },
    {
      "date": "2023-01-02T00:00:00",
      "portfolio_value": "50250.00",
      "daily_return": "0.50",
      "cumulative_return": "0.50"
    }
  ],
  "total_return": "25.50",
  "annualized_return": "25.50"
}
```

---

### 6. Complete Analytics

Get all analytics in a single API call.

**API Endpoint:**
```
GET /api/analytics/portfolios/{portfolio_id}/complete
```

**Response:** Combines all above metrics into one comprehensive response.

---

## Implementation Details

### Service Architecture

```python
class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService(db)

    # Public methods
    def calculate_portfolio_pl(self, portfolio_id: UUID) -> PortfolioPL
    def calculate_returns(self, portfolio_id: UUID, ...) -> ReturnsMetrics
    def calculate_allocations(self, portfolio_id: UUID) -> AllocationBreakdown
    def calculate_risk_metrics(self, portfolio_id: UUID, ...) -> RiskMetrics
    def get_performance_history(self, portfolio_id: UUID, ...) -> PerformanceHistory
    def get_complete_analytics(self, portfolio_id: UUID) -> PortfolioAnalytics
```

### Key Algorithms

#### Time-Weighted Return (TWR)

Simplified implementation:
```
TWR = (End Value - Start Value) / Start Value × 100
```

Full implementation (future enhancement):
- Break portfolio into sub-periods between each cash flow
- Calculate return for each sub-period
- Chain sub-period returns geometrically

#### Money-Weighted Return (IRR)

Uses Newton-Raphson method to solve for IRR:
1. Build cash flow series (deposits = negative, withdrawals = positive)
2. Iteratively solve: NPV = Σ(CF_i / (1 + IRR)^t_i) = 0
3. Converges to IRR typically within 100 iterations

#### Beta Calculation

```
Beta = Covariance(Portfolio Returns, Benchmark Returns) / Variance(Benchmark Returns)
```

Interprets portfolio's sensitivity to market movements.

#### Maximum Drawdown

```
Drawdown_t = Portfolio_Value_t - Cumulative_Max_t
Max Drawdown = Min(Drawdown_t)
```

Tracks largest peak-to-trough decline over the period.

---

## Data Requirements

### Prerequisites

For analytics to work correctly:

1. **Price Data**: Historical price data must exist in `price_data` table
   - Run data backfill: `python scripts/backfill_historical_data.py`
   - Set up daily ingestion: Airflow DAG `data_ingestion_local`

2. **Ticker Metadata**: Tickers must have metadata (sector, market cap, asset type)
   - Populated during ticker creation
   - Required for allocation breakdowns

3. **Portfolio Data**: Portfolio must have holdings with:
   - Valid ticker symbols
   - Purchase dates
   - Quantity and cost basis

4. **Benchmark Data** (for risk metrics): Benchmark ticker (e.g., SPY) must have price data

### Data Quality

The service handles missing data gracefully:
- Missing prices: Holdings excluded from calculations
- Missing ticker metadata: Categorized as "Unknown"
- Insufficient history: Returns empty or partial metrics with warnings

---

## Performance Considerations

### Optimization Strategies

1. **Caching**: Consider caching analytics for frequently accessed portfolios
2. **Background Jobs**: Calculate analytics asynchronously for large portfolios
3. **Database Indexes**: Ensure indexes on:
   - `price_data (ticker, timestamp)`
   - `holdings (portfolio_id)`
   - `transactions (portfolio_id, transaction_date)`

### Performance History Query

Large portfolios with long history may be slow. Optimization options:
- Use TimescaleDB continuous aggregates
- Pre-calculate daily portfolio values in materialized view
- Limit default date range (e.g., 1 year)

---

## Testing

### Test Script

A comprehensive test script is provided: `scripts/test_analytics.py`

Run with:
```bash
python scripts/test_analytics.py
```

Tests include:
- P&L calculations with mock holdings
- Returns calculations over different periods
- Allocation breakdowns
- Risk metrics validation
- Performance history retrieval

### Manual API Testing

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Test endpoints (use your portfolio ID)
curl http://localhost:8000/api/analytics/portfolios/{portfolio_id}/pl
curl http://localhost:8000/api/analytics/portfolios/{portfolio_id}/returns
curl http://localhost:8000/api/analytics/portfolios/{portfolio_id}/allocations
curl http://localhost:8000/api/analytics/portfolios/{portfolio_id}/risk
curl http://localhost:8000/api/analytics/portfolios/{portfolio_id}/complete
```

---

## Future Enhancements

### Phase 2 Improvements

1. **FIFO/LIFO Cost Basis Tracking**
   - Accurate realized gains calculation
   - Tax-loss harvesting suggestions

2. **Multi-Currency Support**
   - Currency conversion for international holdings
   - FX impact on returns

3. **Benchmark Comparison**
   - Compare portfolio vs custom benchmarks
   - Attribution analysis (sector, style, etc.)

4. **Risk Decomposition**
   - Factor-based risk analysis
   - Contribution to portfolio risk by holding

5. **Performance Attribution**
   - Identify sources of outperformance/underperformance
   - Sector/security selection effects

6. **Tax Analytics**
   - Capital gains tracking
   - Tax efficiency metrics
   - Wash sale detection

7. **Scenario Analysis**
   - Stress testing
   - Monte Carlo simulations
   - What-if scenarios

---

## Troubleshooting

### Common Issues

**Issue: Analytics return 0 or empty data**
- **Cause**: No price data available
- **Solution**: Run `python scripts/backfill_historical_data.py`

**Issue: Beta calculation returns 1.0 (default)**
- **Cause**: Benchmark ticker missing price data
- **Solution**: Ensure SPY (or custom benchmark) has price data

**Issue: Risk metrics show "Insufficient data"**
- **Cause**: Less than 30 data points in lookback period
- **Solution**: Reduce `lookback_days` or backfill more historical data

**Issue: Allocations show "Unknown" categories**
- **Cause**: Ticker metadata (sector, market cap) not populated
- **Solution**: Update ticker metadata in `tickers` table

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check analytics calculation logs for errors.

---

## API Reference Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analytics/portfolios/{id}/pl` | GET | Profit/Loss breakdown |
| `/api/analytics/portfolios/{id}/returns` | GET | TWR and MWR/IRR |
| `/api/analytics/portfolios/{id}/allocations` | GET | Asset allocation breakdowns |
| `/api/analytics/portfolios/{id}/risk` | GET | Risk metrics |
| `/api/analytics/portfolios/{id}/performance` | GET | Performance history |
| `/api/analytics/portfolios/{id}/complete` | GET | All analytics combined |

---

## Next Steps

1. ✅ Analytics service implemented
2. ✅ API endpoints created
3. 🔄 Test analytics with real data
4. 🔄 Build frontend components to display analytics
5. 🔄 Add caching layer for performance
6. 🔄 Implement background calculation jobs

See [plan file](https://github.com/user/market-db/blob/main/PLAN.md) for overall project roadmap.

---

**Phase 1B - Market Data & Analytics: COMPLETE**

The analytics service provides institutional-grade portfolio metrics ready for the frontend dashboard.
