# Development Without Schwab API

While waiting for Schwab API credentials, you can build and test the **entire platform** using free alternative data sources. This guide shows you everything you can accomplish.

## 🎯 What We Can Do

### ✅ Fully Functional Development

- ✅ **Complete Backend Development** - All services, analytics, scoring
- ✅ **Complete Frontend Development** - All UI components and pages
- ✅ **Database Setup** - PostgreSQL + TimescaleDB with real data
- ✅ **Airflow Pipeline Testing** - Full DAG testing with real market data
- ✅ **Kubernetes Jobs** - Test all batch jobs end-to-end
- ✅ **Analytics Development** - Portfolio metrics, risk calculations
- ✅ **10x Scoring Algorithm** - Full implementation and testing
- ✅ **Alert Generation** - Complete alert system

### 🔄 Using yfinance for Development

We've created a **Market Data Service** that abstracts the data provider. It automatically switches between:

- **Schwab API** (production) - When credentials are configured
- **yfinance** (development) - Free, no auth required

**Benefits of yfinance:**
- ✅ Free, no API key required
- ✅ Real market data (Yahoo Finance)
- ✅ Historical data for any stock/ETF
- ✅ Fundamental metrics (P/E, market cap, etc.)
- ✅ Same data structure as Schwab API

## 🚀 Quick Start (Without Schwab API)

### Step 1: Install Dependencies

```bash
# Update Python dependencies (includes yfinance)
uv sync

# Or manually install yfinance
pip install yfinance
```

### Step 2: Start Database

```bash
# Option A: Docker (Recommended)
docker run -d --name market-db \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=market_intelligence \
  timescale/timescaledb:latest-pg15

# Wait 10 seconds
sleep 10

# Initialize schema
docker exec -i market-db psql -U postgres -d market_intelligence < scripts/init_db.sql
```

### Step 3: Seed Sample Data

```bash
# Add 20 sample tickers (stocks + ETFs)
python scripts/seed_data.py

# OR fetch real data from yfinance (slower but more accurate)
python scripts/seed_data.py --fetch-prices
```

**Sample Tickers Included:**
- Technology: AAPL, MSFT, NVDA, GOOGL, META
- Finance: JPM, V, BAC
- Healthcare: UNH, JNJ, LLY
- Consumer: AMZN, TSLA, WMT, HD
- Energy: XOM, CVX
- ETFs: SPY, QQQ, VTI, IWM

### Step 4: Test Data Ingestion

```bash
# Run data ingestion job manually (uses yfinance)
python backend/jobs/data_ingestion.py --all --days 365

# Check data was inserted
docker exec -i market-db psql -U postgres -d market_intelligence -c \
  "SELECT ticker, COUNT(*) as records FROM price_data GROUP BY ticker;"
```

### Step 5: Start Backend API

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

Visit: http://localhost:8000/docs

### Step 6: Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:3000

## 📋 Development Roadmap (No Schwab API Needed)

### Phase 1: Foundation ✅ COMPLETE

- ✅ Backend structure
- ✅ Database models
- ✅ FastAPI endpoints
- ✅ Frontend scaffolding
- ✅ Airflow + Kubernetes setup

### Phase 2: Market Data Service ✅ COMPLETE

- ✅ Market Data Service abstraction
- ✅ yfinance integration
- ✅ Auto provider detection
- ✅ Data ingestion job updated
- ✅ Seed script for sample tickers

### Phase 3: Analytics Service (IN PROGRESS)

**What to Build:**

1. **Portfolio Analytics Service** - [backend/app/services/analytics_service.py](backend/app/services/analytics_service.py)
   - Calculate P&L (realized & unrealized)
   - Time-weighted returns (TWR)
   - Money-weighted returns (MWR/IRR)
   - Asset allocation breakdowns
   - Risk metrics

2. **Risk Metrics Calculator** - [backend/app/utils/metrics.py](backend/app/utils/metrics.py)
   - Volatility calculation
   - Beta calculation
   - Sharpe ratio
   - Max drawdown
   - Correlation analysis

3. **Portfolio Analytics API** - [backend/app/api/analytics.py](backend/app/api/analytics.py)
   - GET /api/portfolios/{id}/analytics
   - GET /api/portfolios/{id}/performance
   - GET /api/portfolios/{id}/risk
   - GET /api/portfolios/{id}/allocations

**Testing:**
```bash
# Create test portfolio
curl -X POST http://localhost:8000/api/portfolios \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Portfolio", "description": "Development testing"}'

# Add holdings
curl -X POST http://localhost:8000/api/portfolios/{id}/holdings \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "quantity": 10, "cost_basis": 150.00, "purchase_date": "2024-01-01"}'

# Get analytics
curl http://localhost:8000/api/portfolios/{id}/analytics
```

### Phase 4: Opportunity Scoring (IN PROGRESS)

**What to Build:**

1. **Opportunity Scorer Service** - [backend/app/services/opportunity_scorer.py](backend/app/services/opportunity_scorer.py)
   - Implement 5-component scoring algorithm
   - Calculate confidence levels
   - Generate bull/base/bear scenarios
   - Create explainability JSON

2. **Scoring Components:**
   - Momentum Score (25%) - Uses price data + technical indicators
   - Valuation Divergence (20%) - Uses fundamentals from yfinance
   - Growth Acceleration (25%) - Uses fundamental metrics
   - Relative Strength (15%) - Compares to sector peers
   - Sector Momentum (15%) - Sector-level analysis

3. **Opportunity APIs** - Already defined in plan
   - GET /api/opportunities
   - GET /api/opportunities/{symbol}

**Testing:**
```bash
# Score a single ticker
python backend/jobs/score_opportunities.py --tickers AAPL

# Score all tickers
python backend/jobs/score_opportunities.py --all

# Check results
docker exec -i market-db psql -U postgres -d market_intelligence -c \
  "SELECT ticker, overall_score, confidence_level FROM opportunity_scores ORDER BY overall_score DESC LIMIT 10;"
```

### Phase 5: Frontend Development

**What to Build:**

1. **Portfolio Details Page** - [frontend/app/portfolio/[id]/page.tsx](frontend/app/portfolio/[id]/page.tsx)
   - Holdings table with live prices
   - Performance charts
   - Allocation pie charts
   - Risk metrics display

2. **Opportunities Page** - [frontend/app/opportunities/page.tsx](frontend/app/opportunities/page.tsx)
   - Sortable opportunities table
   - Score badges and confidence indicators
   - Filter by score/confidence/sector
   - Click to expand for details

3. **Ticker Deep Dive** - [frontend/app/ticker/[symbol]/page.tsx](frontend/app/ticker/[symbol]/page.tsx)
   - Price chart with technical overlays
   - Technical indicators panel
   - Fundamental metrics grid
   - Opportunity score breakdown
   - Bull/base/bear scenarios

4. **Dashboard Components:**
   - Alert notifications
   - Quick stats cards
   - Recent activity feed

### Phase 6: Airflow Testing

**What to Test:**

1. **Build Jobs Container:**
```bash
cd kubernetes
./build-jobs.sh latest
```

2. **Start Airflow:**
```bash
cd airflow
docker-compose up -d
```

3. **Configure Variables** (in Airflow UI):
```
database_url = postgresql://postgres:password@host.docker.internal:5432/market_intelligence
```

4. **Enable and Run DAGs:**
   - data_ingestion → Runs with yfinance
   - calculate_indicators → Works with fetched data
   - score_opportunities → Full scoring algorithm
   - generate_alerts → Alert generation

5. **Monitor Execution:**
   - Watch pods: `kubectl get pods -w`
   - Check logs: `kubectl logs <pod-name>`
   - Verify data in database

## 🧪 Testing Strategy

### Unit Tests

Create tests for:
- Analytics calculations (P&L, TWR, MWR)
- Risk metrics (volatility, Sharpe, etc.)
- Scoring algorithm components
- Technical indicator calculations

```bash
# Run tests
pytest backend/tests/
```

### Integration Tests

Test:
- API endpoints with real database
- Data ingestion with yfinance
- Complete scoring pipeline
- Alert generation logic

### End-to-End Tests

Full workflow:
1. Seed database
2. Run data ingestion
3. Calculate indicators
4. Score opportunities
5. Generate alerts
6. View in frontend

## 📊 Sample Data Available

### Tickers (20 total)
- **Large Cap Tech**: AAPL, MSFT, NVDA, GOOGL, META
- **Finance**: JPM, V, BAC
- **Healthcare**: UNH, JNJ, LLY
- **Consumer**: AMZN, TSLA, WMT, HD
- **Energy**: XOM, CVX
- **ETFs**: SPY, QQQ, VTI, IWM

### Data You Can Fetch (via yfinance)
- Historical prices (up to 10+ years)
- Real-time quotes
- Fundamental metrics
- Sector/industry information
- Market cap data

## 🔄 When Schwab API Becomes Available

Simply add credentials to `.env`:

```env
SCHWAB_API_KEY=your_api_key
SCHWAB_API_SECRET=your_api_secret
```

The `MarketDataService` will **automatically switch** from yfinance to Schwab API. No code changes needed!

## 💡 Pro Tips

### 1. Use Real Portfolios

Create your actual portfolio in the system:
```bash
# Add your real holdings with actual cost basis
# The system will fetch real-time prices via yfinance
```

### 2. Test with Different Market Conditions

```bash
# Fetch data from different time periods
python backend/jobs/data_ingestion.py --tickers AAPL --days 365  # 1 year
python backend/jobs/data_ingestion.py --tickers AAPL --days 1825 # 5 years
```

### 3. Monitor Airflow Logs

```bash
# Airflow scheduler logs
docker-compose -f airflow/docker-compose.yaml logs -f airflow-scheduler

# Kubernetes pod logs
kubectl logs -f <pod-name>
```

### 4. Debug with Jupyter

Create `notebooks/` folder and use Jupyter to:
- Test scoring algorithms
- Analyze indicator calculations
- Validate analytics formulas
- Visualize data

## 📝 Current Status

**Working:**
- ✅ Database setup
- ✅ Market data service (yfinance)
- ✅ Data ingestion job
- ✅ Seed script
- ✅ Basic portfolio CRUD

**TODO (Can Be Done Now):**
- ⏳ Analytics service implementation
- ⏳ Opportunity scorer implementation
- ⏳ Frontend components development
- ⏳ Airflow DAG testing
- ⏳ Alert system implementation

**Waiting for Schwab API:**
- ⏸️ Production deployment
- ⏸️ Real-time live data in production

## 🎯 Next Steps

1. **Run the seed script** to populate tickers
2. **Test data ingestion** to verify yfinance works
3. **Implement analytics service** (Phase 3)
4. **Build opportunity scorer** (Phase 4)
5. **Develop frontend pages** (Phase 5)
6. **Test Airflow pipeline** (Phase 6)

You can build the **entire platform** without Schwab API and simply switch providers when credentials are ready!

## Questions?

See [README.md](README.md) or [AIRFLOW_SETUP.md](AIRFLOW_SETUP.md) for more details.
