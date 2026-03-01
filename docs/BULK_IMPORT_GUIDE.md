# Bulk Ticker Import Guide

Easily add hundreds of tickers to your Market Intelligence platform with automatic metadata fetching and data backfill.

---

## Quick Start

### Option 1: Import from CSV

```bash
# Simple format (just ticker symbols)
python scripts/bulk_import_tickers.py --csv scripts/sample_tickers.csv

# With automatic data backfill (2 years)
python scripts/bulk_import_tickers.py --csv scripts/sample_tickers.csv --backfill

# Custom backfill period (1 year)
python scripts/bulk_import_tickers.py --csv scripts/sample_tickers.csv --backfill --days 365
```

### Option 2: Import from List

```bash
# Comma-separated list
python scripts/bulk_import_tickers.py --tickers TSLA,GOOGL,AMZN,META,NFLX

# With automatic backfill
python scripts/bulk_import_tickers.py --tickers TSLA,GOOGL,AMZN --backfill
```

---

## CSV Formats

### Simple Format (Recommended)

The script will automatically fetch metadata from yfinance.

**File: `tickers.csv`**
```csv
ticker
AAPL
MSFT
GOOGL
TSLA
NVDA
```

### Full Format (Advanced)

Provide complete metadata to skip automatic fetching.

**File: `tickers_full.csv`**
```csv
ticker,name,asset_type,sector,industry,market_cap_category,exchange
AAPL,Apple Inc,STOCK,Technology,Consumer Electronics,MEGA,NASDAQ
MSFT,Microsoft Corporation,STOCK,Technology,Software,MEGA,NASDAQ
GOOGL,Alphabet Inc,STOCK,Communication Services,Internet Content,MEGA,NASDAQ
TSLA,Tesla Inc,STOCK,Consumer Cyclical,Auto Manufacturers,LARGE,NASDAQ
NVDA,NVIDIA Corporation,STOCK,Technology,Semiconductors,MEGA,NASDAQ
```

**Fields:**
- `ticker` (required): Stock symbol
- `name`: Company name
- `asset_type`: STOCK, ETF, CRYPTO, INDEX, MUTUAL_FUND
- `sector`: Business sector
- `industry`: Industry classification
- `market_cap_category`: MEGA, LARGE, MID, SMALL, MICRO
- `exchange`: Trading exchange (NASDAQ, NYSE, etc.)

---

## Command-Line Options

```bash
python scripts/bulk_import_tickers.py [OPTIONS]

Input (required, choose one):
  --csv PATH              Path to CSV file
  --tickers LIST          Comma-separated ticker list

Options:
  --no-metadata          Skip automatic metadata fetching
  --backfill             Automatically backfill historical data
  --days N               Days to backfill (default: 730 = 2 years)
```

---

## Complete Workflow

To fully set up new tickers with all data and scoring:

### 1. Import Tickers with Backfill

```bash
python scripts/bulk_import_tickers.py --csv my_tickers.csv --backfill --days 730
```

**What happens:**
- ✅ Tickers added to database
- ✅ Metadata fetched from yfinance
- ✅ 2 years of historical price data downloaded

### 2. Calculate Technical Indicators

```bash
python backend/jobs/calculate_indicators.py --all
```

**What happens:**
- ✅ 20+ technical indicators calculated
- ✅ Moving averages, RSI, MACD, Bollinger Bands, etc.
- ✅ Stored in database for all tickers

### 3. Score Opportunities

```bash
python backend/jobs/score_opportunities.py --all
```

**What happens:**
- ✅ 10x opportunity scores calculated
- ✅ Component breakdown generated
- ✅ Key drivers and risks identified
- ✅ Bull/base/bear scenarios modeled

### 4. View in Dashboard

Open the Streamlit dashboard and explore:
- **Opportunity Radar**: See all scored opportunities
- **Ticker Deep Dive**: Analyze any ticker
- **Portfolio**: Add tickers to your portfolio

---

## Examples

### Example 1: Tech Stocks

**File: `tech_stocks.csv`**
```csv
ticker
AAPL
MSFT
GOOGL
AMZN
META
NVDA
TSLA
```

**Command:**
```bash
python scripts/bulk_import_tickers.py --csv tech_stocks.csv --backfill
```

**Output:**
```
================================================================================
BULK TICKER IMPORT - 7 tickers
================================================================================
Fetching metadata for AAPL...
[OK] Added AAPL - Apple Inc
Fetching metadata for MSFT...
[OK] Added MSFT - Microsoft Corporation
...

================================================================================
IMPORT SUMMARY
================================================================================
Total tickers: 7
Added: 7
Skipped: 0
Failed: 0

New tickers added: AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA

================================================================================
TRIGGERING DATA BACKFILL
================================================================================
Backfilling 730 days of data for 7 tickers
Backfilling AAPL...
Backfilling MSFT...
...

[OK] Backfill completed!

Next steps:
  1. Calculate indicators:
     python backend/jobs/calculate_indicators.py --all
  2. Score opportunities:
     python backend/jobs/score_opportunities.py --all
================================================================================
```

### Example 2: Quick Add from List

```bash
# Add 5 tickers quickly
python scripts/bulk_import_tickers.py --tickers CRM,ADBE,PYPL,SQ,SHOP

# Add with backfill
python scripts/bulk_import_tickers.py --tickers CRM,ADBE,PYPL,SQ,SHOP --backfill
```

### Example 3: Large-Scale Import (100+ tickers)

**File: `sp500_sample.csv`** (truncated for example)
```csv
ticker
AAPL
MSFT
GOOGL
AMZN
...
(100+ tickers)
```

**Command:**
```bash
# Import without backfill first (faster)
python scripts/bulk_import_tickers.py --csv sp500_sample.csv

# Then backfill in batches or use Airflow for automation
python scripts/backfill_historical_data.py
```

---

## Automation with Airflow

For large-scale operations, you can automate the entire pipeline:

1. **Import tickers** (one-time or scheduled)
2. **Daily data ingestion** (Airflow DAG: `ingest_market_data_local`)
3. **Calculate indicators** (Airflow DAG: `calculate_indicators_local`)
4. **Score opportunities** (Airflow DAG: `score_opportunities_local`)

This ensures all new tickers are automatically processed daily.

---

## Troubleshooting

### Issue: "Could not fetch metadata"

**Cause:** yfinance couldn't find ticker information

**Solution:**
- Verify ticker symbol is correct
- Use full format CSV with manual metadata
- Add `--no-metadata` flag to skip automatic fetching

**Example:**
```bash
# Create CSV with manual metadata
cat > manual.csv << EOF
ticker,name,asset_type,sector
XYZ,Unknown Company,STOCK,Technology
EOF

python scripts/bulk_import_tickers.py --csv manual.csv --no-metadata
```

### Issue: "Ticker already exists"

**Cause:** Ticker is already in the database

**Solution:** This is expected behavior. The script skips existing tickers. To update metadata for existing tickers, you would need to manually update the database or delete and re-import.

### Issue: Backfill fails for some tickers

**Cause:** No historical data available (new IPO, delisted, etc.)

**Solution:** The script continues with other tickers. You can manually investigate problematic tickers later.

---

## Performance Considerations

### Import Speed

- **Metadata fetching**: ~1-2 seconds per ticker (yfinance API)
- **Database insertion**: < 0.1 seconds per ticker
- **Backfill**: ~5-10 seconds per ticker for 2 years of data

**Estimated times:**
- 10 tickers: ~30-60 seconds (with backfill)
- 50 tickers: ~5-10 minutes (with backfill)
- 100 tickers: ~10-20 minutes (with backfill)
- 500 tickers: ~1-2 hours (with backfill)

### Optimization Tips

1. **Import first, backfill later** (faster)
   ```bash
   # Step 1: Fast import
   python scripts/bulk_import_tickers.py --csv large_list.csv

   # Step 2: Backfill separately
   python scripts/backfill_historical_data.py
   ```

2. **Use Airflow for automation** (parallel processing)
   - Set up Airflow DAG to backfill in parallel
   - Can process hundreds of tickers simultaneously

3. **Batch processing** (split large lists)
   ```bash
   # Split into batches
   python scripts/bulk_import_tickers.py --csv batch1.csv --backfill
   python scripts/bulk_import_tickers.py --csv batch2.csv --backfill
   ```

---

## Database Limits

The system is designed to handle:
- **Tickers**: Unlimited (PostgreSQL can handle millions)
- **Price data**: Billions of rows (TimescaleDB optimized)
- **Indicators**: Automatically compressed by TimescaleDB
- **Scores**: Stored efficiently with historical tracking

**Real-world capacity:**
- 1,000 tickers × 2 years × 252 trading days = ~500K price records
- 1,000 tickers × 20 indicators × 252 days = ~5M indicator records
- **Database size**: ~1-5 GB for 1,000 tickers with 2 years of data

---

## Best Practices

### 1. Start Small, Scale Up

Begin with a curated list of tickers:
- Top stocks in your portfolio
- S&P 500 components
- Sector-specific lists

Then expand to broader coverage.

### 2. Verify Data Quality

After import, spot-check a few tickers:
```bash
# Check database
psql -d market_intelligence -c "SELECT COUNT(*) FROM tickers;"
psql -d market_intelligence -c "SELECT ticker, name FROM tickers LIMIT 10;"

# Check price data
psql -d market_intelligence -c "SELECT ticker, COUNT(*) FROM price_data GROUP BY ticker LIMIT 10;"
```

### 3. Keep Metadata Updated

Periodically refresh ticker metadata:
- Company names change
- Sectors get reclassified
- Market cap categories change

Consider creating a refresh script for periodic updates.

### 4. Monitor Failed Imports

Keep track of tickers that fail to import or backfill:
```bash
# Check for tickers with no price data
psql -d market_intelligence -c "
  SELECT t.ticker, t.name
  FROM tickers t
  LEFT JOIN price_data p ON t.ticker = p.ticker
  WHERE p.ticker IS NULL;
"
```

---

## Sample Data

The repository includes `scripts/sample_tickers.csv` with 20 popular tickers to get you started:

- **Tech Giants**: TSLA, GOOGL, AMZN, META, NFLX
- **Semiconductors**: NVDA, AMD, INTC
- **Software**: CRM, ADBE, PLTR, SNOW, DDOG
- **Fintech**: PYPL, SQ, COIN
- **E-commerce**: SHOP, UBER, LYFT, ABNB

Try it:
```bash
python scripts/bulk_import_tickers.py --csv scripts/sample_tickers.csv --backfill
```

---

## API Integration

After importing tickers, they're immediately available via the API:

```bash
# List all tickers
curl http://localhost:8000/api/tickers

# Search tickers
curl "http://localhost:8000/api/tickers?search=tesla"

# Get ticker details
curl http://localhost:8000/api/tickers/TSLA

# Get price history
curl "http://localhost:8000/api/tickers/TSLA/history?days=90"
```

And in the Streamlit dashboard:
- **Ticker Deep Dive**: Enter any ticker symbol
- **Opportunity Radar**: All tickers appear automatically
- **Portfolio**: Add any ticker to your portfolio

---

## Conclusion

The bulk import script makes it easy to scale from 20 tickers to 2,000+ tickers. The system architecture is designed to handle this growth with:

- ✅ **Dynamic queries** (no hardcoded lists)
- ✅ **TimescaleDB** (optimized for time-series data)
- ✅ **Automated pipelines** (Airflow DAGs)
- ✅ **Efficient indexing** (fast queries even with millions of rows)

Start with the provided sample tickers and expand to your entire investment universe!
