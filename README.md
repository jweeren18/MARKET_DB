# Market Intelligence Dashboard

Personal investment intelligence platform focused on portfolio analytics, quantitative signals, and 10x opportunity identification.

## Features

- **Portfolio Tracking**: Monitor holdings, P&L, and returns (TWR/MWR)
- **Risk Analytics**: Volatility, beta, Sharpe ratio, max drawdown
- **10x Opportunity Scoring**: Rule-based scoring with full explainability
- **Technical Signals**: Moving averages, RSI, MACD, volume analysis
- **Dashboard Alerts**: Get notified of high-confidence opportunities

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
- Next.js 14+
- TypeScript
- Tailwind CSS
- Recharts

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

```bash
# Pull and run TimescaleDB container
docker run -d --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=market_intelligence \
  timescale/timescaledb:latest-pg15

# Wait for container to start (30 seconds)
sleep 30

# Initialize database
docker exec -i timescaledb psql -U postgres -d market_intelligence < scripts/init_db.sql
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

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Edit .env.local with backend API URL

# Start development server
npm run dev
```

Frontend will be available at http://localhost:3000

## Schwab API Setup

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
│   │   ├── tasks/        # Background jobs
│   │   └── utils/        # Helper functions
│   └── tests/
├── frontend/
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   ├── lib/              # Utilities
│   └── hooks/            # Custom hooks
├── scripts/
│   └── init_db.sql       # Database initialization
├── .env.example
└── pyproject.toml
```

## Development Workflow

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests
cd frontend
npm test
```

### Database Migrations

When modifying models:

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Daily Batch Jobs

The system runs daily batch jobs to:
- Fetch market data (4:00 PM)
- Calculate technical indicators (4:30 PM)
- Score opportunities (5:00 PM)
- Generate alerts (5:15 PM)

These run automatically via APScheduler when the backend is running.

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

Key environment variables:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/market_intelligence
SCHWAB_API_KEY=your_key
SCHWAB_API_SECRET=your_secret
SECRET_KEY=your-secret-key
```

## Roadmap

### Phase 1A: Foundation ✅
- Backend structure
- Database setup
- Core models
- Portfolio CRUD

### Phase 1B: Market Data & Analytics (In Progress)
- Schwab API integration
- Portfolio analytics
- Price data ingestion

### Phase 1C: Signal Engine
- Technical indicators
- Fundamental metrics

### Phase 1D: Opportunity Scorer
- Rule-based scoring
- Explainability
- Scenario modeling

### Phase 1E: Alerts & Polish
- Alert system
- UI polish

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
