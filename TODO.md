# Market Intelligence Platform - TODO

## Future Enhancements

### 🔍 Explore Schwab API Capabilities
**Priority**: Medium
**Status**: Not Started
**Created**: 2026-01-29

Thoroughly explore the Charles Schwab Developer API to understand the full extent of their offerings beyond basic market data.

**Areas to investigate:**

1. **Market Data**
   - Real-time vs delayed quotes
   - Historical data granularity (1min, 5min, hourly bars)
   - Extended hours data
   - Option chains and Greeks
   - Market depth (Level 2)
   - Corporate actions (splits, dividends)

2. **Fundamental Data**
   - Earnings data
   - Financial statements (balance sheet, income statement, cash flow)
   - Analyst ratings and price targets
   - SEC filings integration
   - Company news and events

3. **Trading & Account**
   - Order placement capabilities
   - Order types (market, limit, stop, bracket, etc.)
   - Options trading
   - Margin requirements
   - Portfolio performance metrics

4. **Streaming Data**
   - WebSocket streaming for real-time quotes
   - Level 2 market data
   - Time & sales data

5. **Advanced Features**
   - Watchlists management
   - Saved orders
   - Transaction history
   - Tax lot information

**Action Items:**
- [x] Review official Schwab API documentation thoroughly
- [ ] Test all available endpoints with authenticated calls
- [x] Document capabilities in a dedicated markdown file (`docs/SCHWAB_API_REFERENCE.md`)
- [x] Identify features that could enhance our platform (bulk quotes, fundamentals via quotes, movers)
- [x] Assess rate limits and data restrictions (120 calls/min market data — see reference doc)
- [ ] Compare with other broker APIs (Interactive Brokers, Alpaca, etc.)

**Resources:**
- Schwab Developer Portal: https://developer.schwab.com/
- API Documentation: (authenticated access required)
- Our implementation: `backend/app/services/schwab_client.py`

**Potential Benefits:**
- Access to more granular historical data
- Real-time streaming quotes (reduce API calls)
- Fundamental data integration (reduce reliance on yfinance)
- Enhanced portfolio tracking
- Corporate actions tracking (splits, dividends)

---

## Current Phase: Whole-Market Scaling

### ✅ Completed
- [x] Bulk ticker import system
- [x] Import 30 sample tickers with metadata
- [x] Backfill 2 years historical data
- [x] Streamlit frontend with Opportunity Radar, Portfolio Overview, Ticker Deep Dive
- [x] API endpoints for tickers, prices, indicators, opportunities
- [x] Calculate technical indicators for all tickers
- [x] Score 10x opportunities for all tickers
- [x] Alerts generation job
- [x] Pipeline orchestrator (`backend/jobs/run_pipeline.py`) — manual runner for testing/ad-hoc use
- [x] Chained Airflow pipeline DAGs:
  - `market_pipeline_dag.py` — K8s production DAG (4 KubernetesPodOperator tasks, fan-out ready)
  - `market_pipeline_local.py` — local PythonOperator DAG (active, runs via Docker Compose Airflow)
- [x] Airflow local dev environment via Docker Compose (`airflow/docker-compose.yaml`)
  - All 9 DAGs parse cleanly; only `market_pipeline_local` is enabled
- [x] Fixed all DAG import errors (container_resources param, f-string backslash)

### ⏳ In Progress — Whole-Market Scaling (~4,000 tickers)
- [x] Add `--batch-start` / `--batch-size` flags to indicator and scoring jobs (ingest stays single-pod; alerts is lightweight)
- [x] Rewrite `market_pipeline_dag.py` to use Airflow dynamic task mapping (fan-out per stage)
- [ ] Validate K8s pod execution end-to-end with batched workloads
- [ ] Stress-test indicator calculation and scoring at 4,000-ticker scale
- [ ] Update resource presets (SMALL/MEDIUM/LARGE) based on actual batch benchmarks

### 📋 Next Steps (after scaling)
1. Integrate Schwab streaming quotes for real-time price updates
2. Sentiment intelligence (Phase 3 — see below)
3. Explore Schwab API capabilities (see section below)

---

## Phase 2: Whole-Market Scaling (Current)

Goal: move from 30 tickers to the full US equity universe (~4,000 tickers) without blowing up wall-clock time.

### Architecture change
- Each pipeline stage fans out across N Kubernetes pods, each processing a batch of tickers in parallel.
- Airflow dynamic task mapping (`@task` + `.expand()`) generates one task instance per batch at DAG-run time.
- Fan-in (implicit) waits for all batch tasks to finish before the next stage starts.
- `run_pipeline.py` stays as a manual/testing runner; it does NOT need batch support (just loops sequentially).

### Deliverables
1. **Batch flags on jobs** — `--batch-start` / `--batch-size` (or ticker-list file) on:
   - `data_ingestion.py`
   - `calculate_indicators.py`
   - `score_opportunities.py`
   - `generate_alerts.py`
2. **Dynamic task mapping DAG** (`market_pipeline_dag.py`) — replaces the current linear 4-task chain with staged fan-out/fan-in
3. **K8s validation** — deploy batched DAG to a real cluster, verify pods, logs, and DB writes

### Constraints to watch
- **Schwab rate limit: 120 market-data calls/min per API key.** This is a hard ceiling shared across all pods.
  - Price history is single-symbol only → 4,000 calls for full market → ~34 min sequentially.
  - Fanning out ingest across pods doesn't help — they'd just split the same 120/min quota and 429 each other.
  - Solution: run ingest as a single pod with a client-side rate limiter (0.5s sleep between calls).
- **Stages 2–4 are CPU bound (no Schwab calls).** These are the stages that benefit from K8s fan-out.
- TimescaleDB insert throughput for concurrent batch writes — benchmark before tuning chunk sizes.

---

## Phase 3: Sentiment Intelligence (Future)

- Reddit API integration (r/wallstreetbets, r/stocks)
- Twitter/X API for ticker mentions
- News sentiment analysis
- Social media volume tracking

## Phase 3+: Advanced Features (Future)

- Custom scoring algorithm builder
- Backtesting framework
- Portfolio optimization recommendations
- Tax-loss harvesting suggestions
- Email/SMS/push notifications
- Multi-user support
- Progressive Web App (PWA)

---

## Technical Debt & Improvements

- [ ] Add error handling for failed Schwab API calls
- [ ] Implement retry logic with exponential backoff
- [ ] Add API response caching
- [ ] Optimize indicator calculation performance
- [ ] Add comprehensive logging
- [ ] Write unit tests for scoring algorithm
- [ ] Create integration tests for API endpoints
- [ ] Set up CI/CD pipeline
- [ ] Add database backup automation
- [ ] Document deployment process

---

## Notes

- Database currently has 30 tickers with 2 years of price data
- Pipeline runs as a single chained DAG (`market_pipeline_local`) at 4:15 PM ET Mon-Fri via Airflow in Docker
- Airflow UI: `http://localhost:8080` (user: `airflow` / pass: `airflow`) — start with `cd airflow && docker compose up -d`
- `run_pipeline.py` is manual-only; use it for one-off runs or testing, not scheduling
- K8s pipeline DAG (`market_pipeline_dag.py`) is scaffolded and ready; activate when a K8s cluster is available
- Scaling to ~4,000 tickers requires batch flags + dynamic task mapping (see Phase 2 above)

---

**Last Updated**: 2026-02-03
