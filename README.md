# Market Intelligence Dashboard

Personal investment intelligence platform focused on portfolio analytics, quantitative signals, and 10x opportunity identification.

## Quick Start

### Backend Setup

```bash
# 1. Start PostgreSQL with TimescaleDB
docker run -d --name market-db-postgres \
  -p 5433:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=market_intelligence \
  timescale/timescaledb:latest-pg15

# 2. Initialize database
docker exec -i market-db-postgres psql -U postgres -d market_intelligence < scripts/init_db.sql

# 3. Set up environment
cp .env.example .env
# Edit .env: DATABASE_URL=postgresql://postgres:password@127.0.0.1:5433/market_intelligence

# 4. Install backend dependencies
uv sync

# 5. Seed sample data
uv run python scripts/seed_data.py

# 6. Fetch market data (2 years historical)
uv run python scripts/backfill_historical_data.py

# 7. Calculate technical indicators
uv run python backend/jobs/calculate_indicators.py --all

# 8. Calculate opportunity scores
uv run python backend/jobs/score_opportunities.py --all

# 9. Start backend API
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for API documentation.

### Frontend Setup

```bash
# 1. Install frontend dependencies
cd frontend
pip install -r requirements.txt

# 2. Start Streamlit dashboard
streamlit run app.py

# Dashboard will open at http://localhost:8501
```

For detailed setup instructions, see [SETUP.md](SETUP.md) and [PHASE_1E_COMPLETE.md](PHASE_1E_COMPLETE.md).

## 📚 Documentation

- **[PHASE_1E_COMPLETE.md](PHASE_1E_COMPLETE.md)** - Streamlit frontend with interactive dashboards (NEW! ✅)
- **[PHASE_1C_COMPLETE.md](PHASE_1C_COMPLETE.md)** - Signal engine and technical indicators
- **[PHASE_1B_COMPLETE.md](PHASE_1B_COMPLETE.md)** - Analytics engine and data pipeline
- **[ANALYTICS_SERVICE.md](ANALYTICS_SERVICE.md)** - Complete analytics service guide
- **[AIRFLOW_SETUP_GUIDE.md](AIRFLOW_SETUP_GUIDE.md)** - Airflow setup and deployment
- **[DATA_PIPELINE.md](DATA_PIPELINE.md)** - Data pipeline architecture
- **[SETUP.md](SETUP.md)** - Initial setup and configuration

## Current Status

**Phase 1E Complete** ✅ - Full-stack MVP operational with Streamlit frontend!

### Frontend Dashboard (Phase 1E - NEW! ✅)
- ✅ **Opportunity Radar**: Interactive dashboard for 10x opportunity scoring
  - Filtering and sorting (min score, confidence, limit)
  - Expandable opportunity cards with 4 detail tabs
  - Component breakdown charts, scenario analysis
  - Full explainability with key drivers and risks
- ✅ **Portfolio Overview**: Complete portfolio analytics
  - Holdings table with real-time prices
  - Allocation charts (sector, market cap, asset type)
  - Performance metrics (TWR, MWR, period returns)
  - Risk metrics (volatility, beta, Sharpe ratio, max drawdown)
- ✅ **Ticker Deep Dive**: Detailed asset analysis
  - Interactive price charts with technical overlays
  - 20+ technical indicators organized by category
  - RSI gauge with interpretations
  - Trading signals dashboard
  - Opportunity score with explainability
- ✅ Plotly visualizations (candlestick, bar, pie, gauge charts)
- ✅ Color-coded insights and badges
- ✅ Error handling and health checks

### Opportunity Scoring (Phase 1D ✅)
- ✅ Rule-based 10x scoring algorithm (0-100 scale)
- ✅ 5 weighted components: Momentum, Valuation, Growth, Relative Strength, Sector
- ✅ Confidence calculation based on data quality
- ✅ Bull/base/bear scenario modeling
- ✅ Full explainability with key drivers and risks
- ✅ Automated daily scoring (Airflow DAG)
- ✅ Comprehensive opportunities API (8 endpoints)

### Signal Engine (Phase 1C ✅)
- ✅ 20+ technical indicators (MA, RSI, MACD, Bollinger Bands, Stochastic, ADX, etc.)
- ✅ Signal detection with multi-indicator confirmation
- ✅ Automated daily indicator calculations (Airflow DAG)
- ✅ Comprehensive indicators API (8 endpoints)
- ✅ Trading signal analysis (oversold/overbought, bullish/bearish, trending)

### Data Pipeline (Phase 1B)
- ✅ Schwab API OAuth 2.0 integration with auto-refresh
- ✅ Historical data backfill (2 years, 10,578 records across 21 tickers)
- ✅ Automated daily data ingestion (Airflow DAG ready)
- ✅ Comprehensive data quality monitoring
- ✅ Multi-source data fetching (Schwab + yfinance fallback)

### Analytics Engine (Phase 1B)
- ✅ Portfolio P&L calculations (realized/unrealized gains)
- ✅ Returns calculations (TWR and MWR/IRR)
- ✅ Asset allocation breakdowns (sector, market cap, asset type)
- ✅ Risk metrics (volatility, beta, Sharpe ratio, max drawdown, VaR)
- ✅ Performance history tracking
- ✅ Complete analytics API (6 endpoints)

### Backend Infrastructure
- ✅ FastAPI backend with portfolio + analytics + indicators APIs
- ✅ PostgreSQL + TimescaleDB database with hypertables
- ✅ SQLAlchemy models and Pydantic schemas
- ✅ Comprehensive test suites
- ✅ OpenAPI/Swagger documentation

**Phase 1 MVP: COMPLETE** ✅

**Next Steps** (Phase 2): Sentiment intelligence, alerts system, and advanced features.

## Features

### Implemented ✅
- **Portfolio Tracking**: Monitor holdings, P&L, and returns (TWR/MWR)
- **Risk Analytics**: Volatility, beta, Sharpe ratio, max drawdown, VaR
- **Asset Allocations**: Breakdowns by sector, market cap, asset type
- **Performance History**: Daily portfolio values and returns tracking
- **Data Pipeline**: Automated daily data ingestion with quality monitoring
- **Technical Indicators**: 20+ indicators (RSI, MACD, MAs, Bollinger Bands, Stochastic, ADX, etc.)
- **Signal Detection**: Multi-indicator trading signal analysis
- **10x Opportunity Scoring**: Rule-based scoring with full explainability
- **Streamlit Dashboard**: Interactive frontend with Opportunity Radar, Portfolio Overview, and Ticker Deep Dive
- **Interactive Visualizations**: Plotly charts (candlestick, pie, bar, gauge)

### Planned 📋
- **Alerts System**: Get notified of high-confidence opportunities (Phase 2)
- **Historical Trends**: Score trends and performance tracking over time
- **Sentiment Intelligence**: Social media and news sentiment analysis (Phase 2)
- **Advanced Analytics**: Backtesting, portfolio optimization, tax-loss harvesting

## Git Workflow

This project uses a two-branch workflow:

- **`main`** - Production-ready code (protected, deployed to production)
- **`dev`** - Active development (default branch for new work)

👉 **Developers**: Always work on the `dev` branch or create feature branches from `dev`.
👉 **See [CONTRIBUTING.md](CONTRIBUTING.md)** for detailed git workflow and contribution guidelines.

## Technology Stack

### Backend
- Python 3.10+
- FastAPI (REST API)
- PostgreSQL + TimescaleDB
- SQLAlchemy 2.0
- Schwab Developer API

### Orchestration & Jobs
- **Apache Airflow** (workflow orchestration)
- **Kubernetes** (job execution)
- Docker containers
- KubernetesPodOperator

### Frontend
- **Streamlit** (Python-based dashboard framework)
- Plotly for interactive charts
- Pandas for data manipulation

## Architecture

The platform uses a **hybrid architecture**:

- **FastAPI Backend**: Handles real-time API requests from the frontend
- **Airflow + Kubernetes**: Orchestrates and executes daily batch jobs
  - Data ingestion (Schwab API)
  - Indicator calculation
  - Opportunity scoring
  - Alert generation
- **PostgreSQL + TimescaleDB**: Shared data layer for all components

See [AIRFLOW_SETUP.md](AIRFLOW_SETUP.md) for detailed orchestration setup.

## Setup Instructions

### Prerequisites

1. **Python 3.10+** installed
2. **Node.js 18+** installed
3. **PostgreSQL 15+** with **TimescaleDB** extension
4. **Schwab Developer API** credentials

### Database Setup

#### Option 1: Docker (Recommended)

**Note:** If you have PostgreSQL installed locally on Windows, it may conflict with Docker on port 5432. See [SETUP.md](SETUP.md) for port conflict resolution.

```bash
# Pull and run TimescaleDB container
# Use port 5433 if you have local PostgreSQL on 5432
docker run -d --name market-db-postgres \
  -p 5433:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=market_intelligence \
  timescale/timescaledb:latest-pg15

# Wait for container to start
sleep 5

# Initialize database
docker exec -i market-db-postgres psql -U postgres -d market_intelligence < scripts/init_db.sql

# Update your .env file:
# DATABASE_URL=postgresql://postgres:password@127.0.0.1:5433/market_intelligence
```

#### Option 2: Local PostgreSQL Installation

1. Install PostgreSQL 15+
2. Install TimescaleDB extension:
   - Windows: Download from [TimescaleDB](https://docs.timescale.com/install/latest/windows/)
   - Mac: `brew install timescaledb`
   - Linux: Follow [installation guide](https://docs.timescale.com/install/latest/linux/)

3. Create database:
```bash
# Create database
psql -U postgres -c "CREATE DATABASE market_intelligence;"

# Run initialization script
psql -U postgres -d market_intelligence -f scripts/init_db.sql
```

### Backend Setup

```bash
# Install dependencies with uv
uv sync

# Copy environment variables
cp .env.example .env

# Edit .env with your settings:
# - DATABASE_URL
# - SCHWAB_API_KEY
# - SCHWAB_API_SECRET
# - SECRET_KEY (generate with: openssl rand -hex 32)

# Run database migrations (if using Alembic in the future)
# alembic upgrade head

# Start backend server
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

Backend will be available at http://localhost:8000

API docs available at http://localhost:8000/docs

### Frontend Setup (Coming Soon)

**Status:** Streamlit frontend will be implemented in Phase 1E after analytics services are complete.

```bash
# Install Streamlit (included in pyproject.toml)
uv sync

# Start Streamlit dashboard (once implemented)
uv run streamlit run frontend/app.py
```

Dashboard will be available at http://localhost:8501

## Market Data Setup

### Option 1: Development with yfinance (No API Required)

The platform automatically uses **yfinance** when Schwab API credentials are not configured. This allows full development capability without waiting for API access.

```bash
# Seed sample tickers
uv run python scripts/seed_data.py

# Fetch market data (30 days)
uv run python backend/jobs/data_ingestion.py --tickers AAPL,MSFT,NVDA --days 30

# Or fetch for all seeded tickers
uv run python backend/jobs/data_ingestion.py --all --days 30
```

See [DEVELOPMENT_WITHOUT_SCHWAB.md](DEVELOPMENT_WITHOUT_SCHWAB.md) for details.

### Option 2: Schwab API (Production)

1. Create a Schwab Developer account at https://developer.schwab.com/
2. Create a new application
3. Note your API Key and Secret
4. Set the callback URL to `http://localhost:8000/auth/callback`
5. Add credentials to your `.env` file

## Project Structure

```
market-db/
├── backend/
│   ├── app/
│   │   ├── api/          # API route handlers
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── tasks/        # Background jobs (unused - see jobs/)
│   │   └── utils/        # Helper functions
│   ├── jobs/             # Airflow job scripts
│   │   ├── data_ingestion.py
│   │   ├── calculate_indicators.py
│   │   ├── score_opportunities.py
│   │   └── generate_alerts.py
│   └── tests/
├── frontend/
│   ├── app.py            # Streamlit main app (to be implemented)
│   ├── pages/            # Streamlit pages
│   └── components/       # Reusable Streamlit components
├── airflow/
│   └── dags/             # Airflow DAG definitions
├── kubernetes/
│   └── jobs/             # Kubernetes job manifests
├── scripts/
│   ├── init_db.sql       # Database initialization
│   └── seed_data.py      # Sample data seeding
├── .env.example
└── pyproject.toml
```

## Development Workflow

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests (to be implemented with Streamlit)
cd frontend
uv run pytest test_*.py
```

### Database Migrations

When modifying models:

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Daily Batch Jobs (Airflow + Kubernetes)

The system runs daily batch jobs orchestrated by Airflow:
- **Data Ingestion** (4:00 PM): Fetch market data from Schwab/yfinance
- **Calculate Indicators** (4:30 PM): Calculate technical indicators
- **Score Opportunities** (5:00 PM): Run 10x scoring algorithm
- **Generate Alerts** (5:15 PM): Generate dashboard alerts

Jobs run in isolated Kubernetes pods. See [AIRFLOW_SETUP.md](AIRFLOW_SETUP.md) for configuration.

For development, jobs can be run manually:
```bash
# Run data ingestion
uv run python backend/jobs/data_ingestion.py --tickers AAPL,MSFT --days 30

# Run indicator calculation (coming in Phase 1D)
uv run python backend/jobs/calculate_indicators.py

# Run opportunity scoring (coming in Phase 1E)
uv run python backend/jobs/score_opportunities.py
```

## API Endpoints

### Portfolio APIs
- `GET /api/portfolios` - List portfolios
- `POST /api/portfolios` - Create portfolio
- `GET /api/portfolios/{id}` - Get portfolio details
- `GET /api/portfolios/{id}/analytics` - Get analytics

### Market Data APIs
- `GET /api/tickers/{symbol}` - Get ticker info
- `GET /api/tickers/{symbol}/history` - Get price history
- `GET /api/tickers/{symbol}/indicators` - Get technical indicators

### Opportunity APIs
- `GET /api/opportunities` - List scored opportunities
- `GET /api/opportunities/{symbol}` - Get opportunity details

### Alert APIs
- `GET /api/alerts` - Get recent alerts
- `PUT /api/alerts/{id}/read` - Mark alert as read

## Configuration

Key environment variables (see [.env.example](.env.example)):

```env
# Use port 5433 if you have local PostgreSQL on 5432
DATABASE_URL=postgresql://postgres:password@127.0.0.1:5433/market_intelligence
TIMESCALEDB_ENABLED=true

# Optional - falls back to yfinance for development
SCHWAB_API_KEY=your_api_key_here
SCHWAB_API_SECRET=your_api_secret_here

# Generate with: openssl rand -hex 32
SECRET_KEY=your-secret-key-change-this-in-production

# Backend/Frontend ports
BACKEND_PORT=8000
FRONTEND_PORT=8501

# Job schedules (cron format)
DATA_INGESTION_SCHEDULE=0 16 * * *
SCORING_SCHEDULE=0 17 * * *
```

## Roadmap

### Phase 1A: Foundation ✅
- Backend structure with FastAPI
- Database setup (PostgreSQL + TimescaleDB)
- SQLAlchemy core models
- Portfolio CRUD APIs
- Airflow + Kubernetes integration

### Phase 1B: Market Data Ingestion ✅
- Market data service with provider abstraction (Schwab/yfinance)
- Daily price data ingestion job
- Sample data seeding (21 tickers)
- Database initialization scripts
- Development workflow without Schwab API

### Phase 1C: Portfolio Analytics (Next)
- Portfolio P&L calculations
- Time-weighted returns (TWR)
- Money-weighted returns (MWR)
- Asset allocation breakdowns
- Risk metrics (volatility, beta, Sharpe ratio, max drawdown)

### Phase 1D: Signal Engine
- Technical indicator calculations (MA, RSI, MACD, volume)
- Fundamental metric calculations
- Signal calculation batch job
- Indicator storage and APIs

### Phase 1E: Opportunity Scorer
- Rule-based 10x scoring algorithm (5 components)
- Confidence level calculation
- Bull/base/bear scenario modeling
- Explainability generation
- Opportunity scoring batch job

### Phase 1F: Streamlit Dashboard
- Portfolio overview page
- Holdings table with live prices
- Allocation charts (sector, market cap)
- Performance charts (TWR/MWR)
- Risk metrics dashboard
- Opportunity radar with score breakdown
- Asset deep dive with indicators
- Alert notifications

### Phase 1G: Alerts & Production Polish
- Alert generation logic
- Alert notification system
- Error handling and logging
- Performance optimization
- Production deployment preparation

### Phase 2: Sentiment Intelligence (Future)
- Data collection
- NLP processing
- Integration

## Contributing

This is a personal project. Feel free to fork and customize for your own use.

## License

MIT License

## Disclaimer

This platform is for personal research and decision support only. It does not provide financial advice. Always do your own research and consult with financial professionals before making investment decisions.
