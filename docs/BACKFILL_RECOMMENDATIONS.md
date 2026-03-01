# Historical Data Backfill Recommendations

## Recommended Durations by Use Case

### Standard Portfolio Analytics (Recommended: **2 Years**)
```bash
uv run python scripts/backfill_historical_data.py --all --days 730
```

**Why 2 years:**
- Sufficient for calculating 1-year returns and volatility
- Captures multiple market cycles (bull/bear)
- Good for beta, Sharpe ratio, and risk metrics
- Balance between completeness and API usage
- ~500 trading days per ticker

### Advanced Analytics (Recommended: **5 Years**)
```bash
uv run python scripts/backfill_historical_data.py --all --days 1825
```

**Why 5 years:**
- Robust historical patterns and trends
- Better statistical significance for risk calculations
- Captures economic cycles (recessions, expansions)
- Required for long-term growth analysis
- ~1,250 trading days per ticker

### Quick Start / Testing (Recommended: **6 Months**)
```bash
uv run python scripts/backfill_historical_data.py --all --days 180
```

**Why 6 months:**
- Fast initial setup
- Enough for basic technical indicators
- Good for testing and development
- Can extend later as needed
- ~125 trading days per ticker

## Handling Different Company Histories

### IPOs and Recent Public Companies

**The API automatically handles limited history:**

```bash
# Request 5 years - will get whatever is available
uv run python scripts/backfill_historical_data.py --tickers SNOW,ABNB --days 1825

# Snowflake (SNOW): IPO Sept 2020 → returns ~3.5 years
# Airbnb (ABNB): IPO Dec 2020 → returns ~3 years
```

**No errors occur** - the API simply returns available data from IPO date to present.

### Checking Company History Before Backfill

```bash
# Check when company went public via yfinance
uv run python -c "
import yfinance as yf
ticker = yf.Ticker('SNOW')
info = ticker.info
print(f\"IPO Date: {info.get('firstTradeDateEpochUtc', 'Unknown')}\")
print(f\"Available History: {ticker.history(period='max').index[0] if not ticker.history(period='max').empty else 'None'}\")"
```

### Strategy for Mixed Portfolio

If your portfolio has both mature companies and recent IPOs:

**Option 1: Uniform Backfill (Simple)**
```bash
# Request 5 years for all - each gets what's available
uv run python scripts/backfill_historical_data.py --all --days 1825
```
- ✅ Simple single command
- ✅ Automatically handles limited history
- ⚠️ May fetch more data than needed for recent IPOs

**Option 2: Tiered Backfill (Efficient)**
```bash
# Old companies (5 years)
uv run python scripts/backfill_historical_data.py --tickers AAPL,MSFT,JPM --days 1825

# Recent IPOs (3 years or since IPO)
uv run python scripts/backfill_historical_data.py --tickers SNOW,ABNB,RIVN --days 1095
```
- ✅ More efficient API usage
- ✅ Tailored to each company
- ⚠️ Requires knowing IPO dates

**Recommendation: Use Option 1 (Uniform Backfill)** - simpler and the API handles it gracefully.

## Storage Considerations

### Database Size Estimates

**Daily OHLCV data per ticker:**
- 1 year: ~250 records × 100 bytes ≈ 25 KB
- 5 years: ~1,250 records × 100 bytes ≈ 125 KB

**For 21 tickers (current seed data):**
- 1 year: ~525 KB
- 5 years: ~2.6 MB

**For 100 tickers:**
- 1 year: ~2.5 MB
- 5 years: ~12.5 MB

**For 500 tickers:**
- 1 year: ~12.5 MB
- 5 years: ~62.5 MB

**TimescaleDB compression** can reduce this by 90%+, so storage is rarely a concern for daily data.

## API Rate Limit Considerations

### Schwab API Limits (Typical)
- **Requests per day**: 10,000 - 120,000 (varies by app tier)
- **Requests per second**: 120

### Backfill API Usage

**One backfill request per ticker** (Schwab returns full date range in one call):
- 21 tickers × 1 request = 21 API calls
- 100 tickers × 1 request = 100 API calls
- 500 tickers × 1 request = 500 API calls

Even with 500 tickers requesting 5 years each, you're only using 500 API calls - well within daily limits.

### Rate Limiting Strategy

For very large portfolios (1000+ tickers), backfill in batches:

```bash
# Batch 1 (tickers 1-250)
uv run python scripts/backfill_historical_data.py --tickers AAPL,MSFT,...[250 tickers] --days 1825

# Wait 60 seconds
sleep 60

# Batch 2 (tickers 251-500)
uv run python scripts/backfill_historical_data.py --tickers GOOGL,AMZN,...[250 tickers] --days 1825
```

## Data Quality for Recent IPOs

### Validating IPO Data

Check data quality after backfilling recent IPOs:

```bash
# Check data ranges for recent IPOs
uv run python scripts/check_data_quality.py --ticker SNOW
```

### Expected Gaps

**Market holidays and weekends** will show as gaps - this is normal:
- Weekends (Saturday/Sunday)
- Federal holidays (NYSE closed)
- Company-specific trading halts

The quality checker excludes weekends automatically.

## Recommended Workflow

### Initial Setup
```bash
# 1. Seed your tickers
uv run python scripts/seed_data.py

# 2. Backfill 2 years (recommended starting point)
uv run python scripts/backfill_historical_data.py --all --days 730

# 3. Verify data quality
uv run python scripts/check_data_quality.py

# 4. Check for any issues
# If everything looks good, extend to 5 years if needed
uv run python scripts/backfill_historical_data.py --all --days 1825
```

### Adding New Tickers

```bash
# Add ticker to database (via API or SQL)
# Then backfill with same duration as existing tickers

# Check existing data range first
uv run python scripts/check_data_quality.py

# Backfill new ticker to match
uv run python scripts/backfill_historical_data.py --tickers NEWCO --days 730
```

### Extending History

```bash
# Already have 2 years, want to extend to 5 years
uv run python scripts/backfill_historical_data.py --all --days 1825

# The upsert logic will:
# - Update existing 2 years (no-op since same data)
# - Insert additional 3 years of history
```

## Best Practices

1. **Start with 2 years** - Good balance for most analytics
2. **Verify before extending** - Run quality checks after initial backfill
3. **Don't worry about IPO dates** - API returns what's available
4. **Use uniform backfill** - Simpler than per-ticker durations
5. **Monitor API usage** - Check Schwab developer portal for limits
6. **Backfill during off-hours** - Reduce impact if API is rate-limited
7. **Keep recent data fresh** - Ensure daily DAG is running

## Next Steps

After backfilling:
1. Run `python scripts/check_data_quality.py` to verify completeness
2. Review any gaps or anomalies found
3. Set up daily Airflow DAG to keep data current
4. Begin building analytics on the historical foundation

See [DATA_PIPELINE.md](DATA_PIPELINE.md) for full pipeline documentation.
