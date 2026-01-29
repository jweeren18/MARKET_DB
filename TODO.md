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
- [ ] Review official Schwab API documentation thoroughly
- [ ] Test all available endpoints with authenticated calls
- [ ] Document capabilities in a dedicated markdown file
- [ ] Identify features that could enhance our platform
- [ ] Assess rate limits and data restrictions
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

## Current Phase: Phase 1E - Frontend & Dashboard

### ✅ Completed
- [x] Bulk ticker import system
- [x] Import 20 sample tickers with metadata
- [x] Backfill 2 years historical data (4,518 price records)
- [x] Streamlit frontend with Opportunity Radar, Portfolio Overview, Ticker Deep Dive
- [x] API endpoints for tickers, prices, indicators, opportunities

### ⏳ In Progress
- [ ] Calculate technical indicators for all 20 tickers (currently running)
- [ ] Score 10x opportunities for all tickers
- [ ] Verify dashboard displays all data correctly

### 📋 Next Steps
1. Wait for indicator calculation to complete
2. Run opportunity scoring: `python backend/jobs/score_opportunities.py --all`
3. Test dashboard with all 20 tickers
4. Document Phase 1E completion

---

## Phase 2 Ideas (Future)

### Sentiment Intelligence
- Reddit API integration (r/wallstreetbets, r/stocks)
- Twitter/X API for ticker mentions
- News sentiment analysis
- Social media volume tracking

### Advanced Features
- Custom scoring algorithm builder
- Backtesting framework
- Portfolio optimization recommendations
- Tax-loss harvesting suggestions
- Email/SMS/push notifications
- Multi-user support

### Mobile
- Progressive Web App (PWA)
- React Native mobile app

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

- Database currently has 20 tickers with 2 years of price data
- System is fully dynamic and can scale to hundreds/thousands of tickers
- All tickers process through batch jobs (indicators, scoring)
- Frontend automatically displays all tickers via API

---

**Last Updated**: 2026-01-29
