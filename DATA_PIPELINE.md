# Market Data Pipeline Guide

Complete guide for managing daily data ingestion and historical backfills.

## Overview

The Market Intelligence Dashboard uses a two-tier data pipeline:

1. **Daily Ingestion** - Automated daily updates via Airflow (production)
2. **Historical Backfill** - One-time or on-demand historical data loading

Both use the Schwab API (or yfinance fallback) and store data in PostgreSQL/TimescaleDB.

## Daily Data Ingestion

### Airflow DAG (Production)

**DAG Name:** `data_ingestion_daily`

**Schedule:** Mon-Fri at 4:00 PM EST (after market close)

**What it does:**
- Fetches previous trading day's OHLCV data
- Runs for all active tickers in the database
- Automatically handles duplicates (updates existing records)
- Retries 3 times on failure

**Airflow Variables Required:**
```bash
# Set these in Airflow UI: Admin > Variables
database_url=postgresql://postgres:password@127.0.0.1:5433/market_intelligence
schwab_api_key=your_api_key
schwab_api_secret=your_api_secret
schwab_callback_url=https://127.0.0.1:8000/auth/callback
```

**Manual Trigger:**
```bash
# Via Airflow CLI
airflow dags trigger data_ingestion_daily

# Via Airflow UI
# Navigate to DAGs > data_ingestion_daily > Trigger DAG
```

### Manual Daily Update (Development)

For local development without Airflow:

```bash
# Fetch yesterday's data for all active tickers
cd backend
uv run python jobs/data_ingestion.py --all --days 1

# Fetch for specific tickers
uv run python jobs/data_ingestion.py --tickers AAPL,MSFT,NVDA --days 1
```

## Historical Data Backfill

### Option 1: CLI Script (Recommended)

Use the convenient backfill script for manual historical data loading:

```bash
# Backfill 1 year for all active tickers
uv run python scripts/backfill_historical_data.py --all --days 365

# Backfill 2 years for specific tickers
uv run python scripts/backfill_historical_data.py --tickers AAPL,MSFT,NVDA --days 730

# Backfill 5 years for all tickers
uv run python scripts/backfill_historical_data.py --all --days 1825

# Backfill with custom date range
uv run python scripts/backfill_historical_data.py --all --start-date 2020-01-01 --end-date 2023-12-31
```

**Features:**
- Shows existing data ranges before backfilling
- Handles duplicates (updates existing records)
- Progress logging for each ticker
- Summary statistics at completion
- Graceful error handling per ticker

### Option 2: Airflow DAG (Production)

**DAG Name:** `data_backfill_historical`

**Schedule:** Manual trigger only (no automatic schedule)

**Usage via Airflow UI:**

1. Navigate to DAGs > `data_backfill_historical`
2. Click "Trigger DAG"
3. Provide configuration (optional):
   ```json
   {
     "days": 365
   }
   ```
4. Click "Trigger"

**Usage via Airflow CLI:**
```bash
# Backfill 1 year
airflow dags trigger data_backfill_historical --conf '{"days": 365}'

# Backfill 2 years
airflow dags trigger data_backfill_historical --conf '{"days": 730}'
```

**Default Configuration:**
- Days: 365 (1 year)
- Tickers: All active tickers
- Timeout: 2 hours
- Resources: 1GB RAM, 1 CPU

### Option 3: Direct Job Script

Use the data ingestion job directly:

```bash
cd backend

# Backfill 1 year for all tickers
uv run python jobs/data_ingestion.py --all --days 365

# Backfill 2 years for specific tickers
uv run python jobs/data_ingestion.py --tickers AAPL,MSFT,NVDA --days 730
```

## Recommended Backfill Strategy

### Initial Setup (New Database)

```bash
# 1. Seed tickers
uv run python scripts/seed_data.py

# 2. Backfill 2 years of historical data
uv run python scripts/backfill_historical_data.py --all --days 730

# 3. Verify data
uv run python -c "
from backend.app.database import SessionLocal
from backend.app.models import PriceData
from sqlalchemy import func
db = SessionLocal()
result = db.query(PriceData.ticker, func.count(PriceData.ticker)).group_by(PriceData.ticker).all()
for ticker, count in result:
    print(f'{ticker}: {count} records')
db.close()
"
```

### Adding New Tickers

```bash
# 1. Add ticker to database (via API or SQL)
# 2. Backfill historical data for the new ticker
uv run python scripts/backfill_historical_data.py --tickers TSLA --days 730
```

### Filling Gaps

```bash
# Backfill specific date range
uv run python scripts/backfill_historical_data.py --all \
  --start-date 2023-01-01 \
  --end-date 2023-12-31
```

## Data Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Market Data Sources                       │
│                                                              │
│  ┌─────────────────┐           ┌──────────────────┐        │
│  │  Schwab API     │           │   yfinance       │        │
│  │  (Production)   │           │   (Fallback)     │        │
│  └────────┬────────┘           └────────┬─────────┘        │
└───────────┼──────────────────────────────┼──────────────────┘
            │                              │
            └──────────────┬───────────────┘
                          │
                ┌─────────▼──────────┐
                │  Market Data       │
                │  Service Layer     │
                │  (Abstraction)     │
                └─────────┬──────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼─────┐    ┌──────▼──────┐   ┌─────▼──────┐
   │  Daily   │    │  Backfill   │   │  Manual    │
   │  Airflow │    │  Airflow    │   │  CLI       │
   │  DAG     │    │  DAG        │   │  Script    │
   └────┬─────┘    └──────┬──────┘   └─────┬──────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                ┌─────────▼──────────┐
                │  Data Ingestion    │
                │  Job               │
                └─────────┬──────────┘
                          │
                ┌─────────▼──────────┐
                │  PostgreSQL +      │
                │  TimescaleDB       │
                │  (price_data)      │
                └────────────────────┘
```

## Data Flow

### Daily Ingestion Flow

1. **Trigger**: Airflow scheduler at 4:00 PM EST Mon-Fri
2. **Fetch**: Query all active tickers from database
3. **API Call**: Request previous day's OHLCV data from Schwab
4. **Transform**: Convert API response to standardized format
5. **Load**: Upsert data into `price_data` table
6. **Complete**: Log success/failure metrics

### Backfill Flow

1. **Input**: Date range and ticker list
2. **Check**: Query existing data ranges per ticker
3. **Fetch**: Request historical data in chunks (if needed)
4. **Transform**: Convert to standardized format
5. **Load**: Upsert data (update existing, insert new)
6. **Report**: Summary of new vs updated records

## Data Quality & Monitoring

### Checking Data Completeness

```bash
# Check record counts per ticker
uv run python -c "
from backend.app.database import SessionLocal
from backend.app.models import PriceData
from sqlalchemy import func
db = SessionLocal()
result = db.query(
    PriceData.ticker,
    func.count(PriceData.ticker).label('count'),
    func.min(PriceData.timestamp).label('earliest'),
    func.max(PriceData.timestamp).label('latest')
).group_by(PriceData.ticker).all()
print(f'{'Ticker':<8} {'Records':<10} {'Earliest':<12} {'Latest':<12}')
print('-' * 50)
for ticker, count, earliest, latest in result:
    print(f'{ticker:<8} {count:<10} {earliest.date()!s:<12} {latest.date()!s:<12}')
db.close()
"
```

### Identifying Data Gaps

```sql
-- Run in psql or pgAdmin
WITH date_series AS (
  SELECT generate_series(
    '2023-01-01'::date,
    CURRENT_DATE,
    '1 day'::interval
  )::date AS date
),
expected_data AS (
  SELECT
    t.ticker,
    d.date
  FROM tickers t
  CROSS JOIN date_series d
  WHERE t.is_active = true
    AND EXTRACT(DOW FROM d.date) NOT IN (0, 6)  -- Exclude weekends
)
SELECT
  ed.ticker,
  ed.date AS missing_date
FROM expected_data ed
LEFT JOIN price_data pd
  ON pd.ticker = ed.ticker
  AND pd.timestamp::date = ed.date
WHERE pd.ticker IS NULL
ORDER BY ed.ticker, ed.date;
```

### Monitoring Airflow Jobs

```bash
# Check DAG run history
airflow dags list-runs -d data_ingestion_daily --state failed

# View task logs
airflow tasks logs data_ingestion_daily ingest_daily_market_data <execution_date>

# Clear failed task and retry
airflow tasks clear data_ingestion_daily -t ingest_daily_market_data -d <execution_date>
```

## Troubleshooting

### Issue: Missing Data for Recent Days

**Cause:** Daily DAG failed or didn't run

**Solution:**
```bash
# Manual backfill for last 7 days
uv run python scripts/backfill_historical_data.py --all --days 7
```

### Issue: Duplicate Records

**Cause:** Job ran multiple times without deduplication

**Solution:**
The pipeline automatically handles duplicates via upsert logic. Old duplicates can be cleaned:

```sql
-- Remove duplicate records (keep most recent insert)
DELETE FROM price_data a USING (
  SELECT MIN(ctid) as ctid, ticker, timestamp
  FROM price_data
  GROUP BY ticker, timestamp
  HAVING COUNT(*) > 1
) b
WHERE a.ticker = b.ticker
  AND a.timestamp = b.timestamp
  AND a.ctid <> b.ctid;
```

### Issue: Schwab API Authentication Expired

**Symptom:** Jobs fail with "Not authenticated" error

**Solution:**
```bash
# Re-authenticate using quick auth script
uv run python scripts/quick_auth.py

# Or check token expiration
uv run python -c "
import json
from pathlib import Path
token_file = Path('.schwab_tokens.json')
if token_file.exists():
    with open(token_file) as f:
        token = json.load(f)
    from datetime import datetime
    expires = datetime.fromtimestamp(token.get('expires_at', 0))
    print(f'Token expires: {expires}')
    if datetime.now() > expires:
        print('Token EXPIRED - re-authenticate!')
else:
    print('No token file found')
"
```

### Issue: Rate Limiting

**Symptom:** API returns 429 Too Many Requests

**Solution:**
- Schwab API has rate limits per app per day
- Reduce concurrent requests or add delays
- Consider backfilling in smaller chunks:

```bash
# Backfill in yearly chunks instead of all at once
for year in 2020 2021 2022 2023; do
  uv run python scripts/backfill_historical_data.py --all \
    --start-date ${year}-01-01 \
    --end-date ${year}-12-31
  sleep 60  # Wait between chunks
done
```

## Best Practices

1. **Start with shorter history** - Backfill 1 year first, then extend
2. **Verify after backfill** - Check record counts and date ranges
3. **Monitor daily runs** - Set up Airflow alerts for failures
4. **Keep tokens fresh** - OAuth refresh tokens expire after 7 days
5. **Use --all for consistency** - Ensures all active tickers stay synchronized
6. **Check data quality** - Run gap analysis queries periodically
7. **Backup before bulk operations** - `pg_dump` before major backfills

## Next Steps

After setting up your data pipeline:

1. **Phase 1C**: Implement portfolio analytics service
2. **Phase 1D**: Add technical indicator calculations
3. **Phase 1E**: Build opportunity scoring engine
4. **Phase 1F**: Create Streamlit dashboard

See [README.md](README.md) for the full roadmap.
