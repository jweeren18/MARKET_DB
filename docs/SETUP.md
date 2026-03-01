# Setup Guide

This guide covers local development setup for the Market Intelligence Dashboard.

## Prerequisites

- **Python 3.10+**
- **Docker Desktop** (with Docker Compose)
- **Node.js 18+** (for frontend)
- **uv** package manager (`pip install uv`)

## Quick Start

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/jweeren18/MARKET_DB.git
cd MARKET_DB

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# See "Database Setup" section below for port configuration
```

### 2. Database Setup

#### Important: PostgreSQL Port Conflict

If you have PostgreSQL installed locally on Windows, it will conflict with the Docker container on port 5432.

**Solution:** Run the Docker container on port 5433 instead:

```bash
# Start PostgreSQL with TimescaleDB (mapped to port 5433)
docker run -d \
  --name market-db-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=market_intelligence \
  -p 5433:5432 \
  timescale/timescaledb:latest-pg15
```

**Update your .env file:**
```env
DATABASE_URL=postgresql://postgres:password@127.0.0.1:5433/market_intelligence
```

#### Initialize Database Schema

```bash
# Wait a few seconds for the database to start
sleep 5

# Initialize schema with TimescaleDB hypertables
cat scripts/init_db.sql | docker exec -i market-db-postgres psql -U postgres -d market_intelligence
```

### 3. Seed Sample Data

```bash
# Add 21 sample tickers (AAPL, MSFT, NVDA, etc.)
uv run python scripts/seed_data.py
```

### 4. Fetch Market Data

Since you may not have Schwab API credentials yet, the platform uses **yfinance** for development:

```bash
# Fetch 30 days of data for specific tickers
uv run python backend/jobs/data_ingestion.py --tickers AAPL,MSFT,NVDA --days 30

# Or fetch for all seeded tickers
uv run python backend/jobs/data_ingestion.py --all --days 30
```

### 5. Start the Backend API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API will be available at:
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### 6. Start the Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:3000

## Troubleshooting

### Database Connection Issues

**Error:** `password authentication failed for user "postgres"`

**Causes:**
1. **Port conflict** - Local PostgreSQL using port 5432
2. **Stale Docker volumes** - Old credentials cached

**Solutions:**

1. **Use alternate port (5433):**
   ```bash
   # Stop and remove old container
   docker stop market-db-postgres && docker rm market-db-postgres

   # Remove old volumes
   docker volume prune -f

   # Start on port 5433
   docker run -d --name market-db-postgres \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=market_intelligence \
     -p 5433:5432 \
     timescale/timescaledb:latest-pg15

   # Update .env
   DATABASE_URL=postgresql://postgres:password@127.0.0.1:5433/market_intelligence
   ```

2. **Stop local PostgreSQL service:**
   ```powershell
   # Windows: Stop PostgreSQL service
   net stop postgresql-x64-<version>
   ```

### Module Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:** Job scripts have path setup built-in. Run from project root:
```bash
uv run python backend/jobs/data_ingestion.py --tickers AAPL --days 30
```

### Environment Variables Not Loading

**Error:** `Field required` for `database_url` or `secret_key`

**Solution:** Ensure `.env` file exists in project root:
```bash
# Check .env exists
ls .env

# If not, copy from template
cp .env.example .env
```

## Development Without Schwab API

The platform automatically falls back to **yfinance** when Schwab credentials aren't configured.

See [DEVELOPMENT_WITHOUT_SCHWAB.md](DEVELOPMENT_WITHOUT_SCHWAB.md) for full details.

**What works with yfinance:**
- ✅ Price history (OHLCV data)
- ✅ Real-time quotes
- ✅ Company fundamentals
- ✅ All technical indicators
- ✅ Opportunity scoring

**Limitations:**
- ⚠️ Data is delayed (15-20 minutes)
- ⚠️ Some fundamental metrics may be incomplete

## Verify Setup

Check that everything is working:

```bash
# 1. Database connection
docker exec market-db-postgres psql -U postgres -d market_intelligence -c "SELECT COUNT(*) FROM tickers;"
# Should show: 21 (if seeded)

# 2. Price data
docker exec market-db-postgres psql -U postgres -d market_intelligence -c "SELECT ticker, COUNT(*) FROM price_data GROUP BY ticker;"
# Should show data for tickers you fetched

# 3. Backend API
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

## Next Steps

1. **Fetch more data:** Run data ingestion for all tickers with 1 year of history
2. **Calculate indicators:** Run technical indicator calculation job
3. **Implement analytics:** Build portfolio analytics service (Phase 1C)
4. **Build opportunity scorer:** Implement 10x scoring algorithm (Phase 1D)

## Additional Resources

- [README.md](README.md) - Project overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - Git workflow and branching
- [AIRFLOW_SETUP.md](AIRFLOW_SETUP.md) - Airflow + Kubernetes setup
- [DEVELOPMENT_WITHOUT_SCHWAB.md](DEVELOPMENT_WITHOUT_SCHWAB.md) - yfinance development guide

## Getting Help

- **Issues:** https://github.com/jweeren18/MARKET_DB/issues
- **Discussions:** https://github.com/jweeren18/MARKET_DB/discussions
