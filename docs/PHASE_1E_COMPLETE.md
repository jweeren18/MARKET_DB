# Phase 1E Complete: Streamlit Frontend ✅

**Completion Date:** 2026-01-28
**Status:** Fully Operational

---

## Overview

Phase 1E implements a comprehensive Streamlit-based frontend for the Market Intelligence platform, providing:
- **Opportunity Radar**: 10x investment opportunity scoring dashboard
- **Portfolio Overview**: Portfolio analytics with risk metrics and visualizations
- **Ticker Deep Dive**: Detailed technical analysis and opportunity scores
- **Interactive Charts**: Plotly visualizations for all data

---

## Architecture

### Technology Stack

- **Framework**: Streamlit 1.30+
- **Data Visualization**: Plotly Express & Plotly Graph Objects
- **HTTP Client**: httpx
- **Data Processing**: Pandas
- **Python**: 3.10+

### Project Structure

```
frontend/
├── app.py                          # Main Streamlit application
├── components/
│   ├── opportunity_radar.py        # Opportunity scoring dashboard
│   ├── portfolio_overview.py       # Portfolio analytics
│   └── ticker_deep_dive.py         # Ticker analysis page
├── utils/
│   ├── api_client.py               # Backend API client
│   └── config.py                   # Configuration
├── pages/                          # Additional Streamlit pages (optional)
└── requirements.txt                # Python dependencies
```

---

## Features Implemented

### 1. Opportunity Radar 🎯

**Purpose**: Discover high-potential investment opportunities

**Features**:
- ✅ **Filtering & Sorting**
  - Min score filter (0-100)
  - Min confidence filter (0-100%)
  - Sort by score, confidence, or ticker
  - Limit results (10-500)

- ✅ **Summary Metrics**
  - Total opportunities count
  - Average score
  - Average confidence
  - High confidence count (≥70%)

- ✅ **Expandable Opportunity Cards**
  - Score badge with color coding (High/Medium/Low)
  - Confidence indicator
  - Timestamp

- ✅ **Detailed Views** (4 tabs per opportunity)
  - **Overview**: Key metrics and scenario analysis (Bull/Base/Bear)
  - **Components**: Breakdown of 5 scoring components with contribution chart
  - **Explainability**: Key drivers, risks, and detailed reasoning
  - **Scenarios**: Visual scenario comparison with bar chart

- ✅ **Visualizations**
  - Component contribution bar chart (Plotly)
  - Scenario comparison chart
  - Color-coded metrics (green/amber/red)

### 2. Portfolio Overview 💼

**Purpose**: Track investments with real-time analytics

**Features**:
- ✅ **Portfolio Management**
  - List all portfolios
  - Create new portfolios
  - Select portfolio to view
  - Empty state with guided creation

- ✅ **Summary Metrics**
  - Total value
  - Total gain/loss ($ and %)
  - Cost basis
  - Daily P&L

- ✅ **Holdings Table**
  - Ticker, quantity, price
  - Cost basis, current value
  - Gain/loss ($ and %)
  - Formatted numbers with proper precision

- ✅ **Allocation Charts** (3 views)
  - By Sector (pie/donut chart)
  - By Market Cap (pie/donut chart)
  - By Asset Type (pie/donut chart)

- ✅ **Performance Metrics**
  - Time-Weighted Return (TWR)
  - Money-Weighted Return (MWR)
  - Period returns (1M, 3M, YTD)

- ✅ **Risk Metrics**
  - Volatility (annualized)
  - Beta (vs SPY)
  - Sharpe ratio
  - Max drawdown
  - Risk level assessment (Low/Moderate/High)
  - Beta interpretation

### 3. Ticker Deep Dive 🔍

**Purpose**: Comprehensive analysis of individual assets

**Features**:
- ✅ **Ticker Search**
  - Text input with validation
  - Auto-uppercase conversion
  - Analyze button

- ✅ **Ticker Header**
  - Ticker symbol and name
  - Sector, market cap category
  - Asset type

- ✅ **Price & Chart Tab**
  - 90-day candlestick chart
  - Moving average overlays (SMA 20, SMA 50)
  - Volume bar chart
  - Interactive zoom/pan with Plotly

- ✅ **Technical Indicators Tab**
  - Organized by category:
    - Momentum (RSI, Stochastic, Williams %R)
    - Trend (SMA, EMA, MACD, ADX)
    - Volatility (Bollinger Bands, ATR)
    - Volume (OBV, Volume SMA)
  - RSI gauge chart with interpretation
  - Color-coded zones (oversold/neutral/overbought)

- ✅ **Opportunity Score Tab**
  - Overall score with badge (High/Medium/Low)
  - Confidence level
  - Scenario analysis (Bull/Base/Bear)
  - Key drivers list
  - Risks list
  - Component breakdown with contribution chart

- ✅ **Signals Tab**
  - Active trading signals
  - Signal type (oversold, overbought, bullish, bearish)
  - Indicator source (RSI, MACD, etc.)
  - Strength (strong, moderate)
  - Description
  - Color-coded badges

---

## API Integration

### API Client (`utils/api_client.py`)

Comprehensive client supporting all backend endpoints:

**Portfolio APIs**:
- `get_portfolios()`: List all portfolios
- `get_portfolio(portfolio_id)`: Get portfolio details
- `create_portfolio(name, description)`: Create new portfolio
- `get_portfolio_holdings(portfolio_id)`: Get holdings
- `get_portfolio_analytics(portfolio_id)`: Get analytics

**Market Data APIs**:
- `get_ticker_info(symbol)`: Get ticker details
- `get_price_history(symbol, start_date, end_date)`: Get price history

**Indicator APIs**:
- `get_latest_indicators(ticker)`: Get latest indicator values
- `get_indicator_history(ticker, indicator_name, days)`: Get historical indicators
- `get_indicator_summary(ticker)`: Get indicator summary
- `detect_signals(ticker)`: Detect trading signals

**Opportunity APIs**:
- `list_opportunities(min_score, min_confidence, limit, sort_by)`: List opportunities
- `get_opportunity(ticker, include_history, history_days)`: Get detailed opportunity
- `get_opportunity_components(ticker)`: Get component breakdown
- `get_opportunity_explainability(ticker)`: Get key drivers and risks
- `get_opportunity_history(ticker, days)`: Get historical scores
- `get_top_opportunities(category, limit, min_confidence)`: Get top by category

**Health Check**:
- `health_check()`: Check backend API status

---

## Running the Frontend

### Prerequisites

1. **Backend Running**: Ensure backend API is running at `http://localhost:8000`
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Database Populated**: Ensure you have:
   - Historical price data ingested
   - Technical indicators calculated
   - Opportunity scores generated

### Installation

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Key dependencies:
   - `streamlit>=1.30.0`
   - `plotly>=5.18.0`
   - `pandas>=2.1.0`
   - `httpx>=0.25.0`

3. **Configure environment** (optional):
   Create `.env` file:
   ```env
   BACKEND_URL=http://localhost:8000
   ```

### Start the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Alternative: Run with custom port

```bash
streamlit run app.py --server.port 8502
```

---

## Usage Guide

### 1. Dashboard (Home)

- View current project status
- See summary metrics (portfolios, holdings, value, P&L)
- Quick links to backend API docs

### 2. Opportunity Radar

**Step-by-step**:
1. Navigate to "Opportunities" in sidebar
2. Adjust filters:
   - **Min Score**: Set threshold (e.g., 60 for medium+ opportunities)
   - **Min Confidence**: Set confidence threshold (e.g., 50%)
   - **Sort By**: Choose score, confidence, or ticker
   - **Limit**: Number of results to display
3. View opportunities list with badges
4. Click on any opportunity to expand details
5. Explore tabs:
   - **Overview**: See score and scenarios
   - **Components**: Understand what drives the score
   - **Explainability**: Read key drivers and risks
   - **Scenarios**: Visualize bull/base/bear cases

**Example Use Cases**:
- Find top opportunities: Set min_score=70, sort by score
- Find confident picks: Set min_confidence=70, sort by confidence
- Screen for value: Look for high scores with low price/MA ratios

### 3. Portfolio Overview

**Step-by-step**:
1. Navigate to "Portfolio" in sidebar
2. If no portfolios exist, create one:
   - Enter portfolio name
   - Add optional description
   - Click "Create Portfolio"
3. Select portfolio from dropdown
4. View analytics:
   - **Summary**: Total value, gain/loss, daily P&L
   - **Holdings**: Detailed position table
   - **Allocation**: Sector, market cap, asset type breakdowns
   - **Performance**: Returns (TWR, MWR) and period returns
   - **Risk**: Volatility, beta, Sharpe, max drawdown

**Example Use Cases**:
- Track overall portfolio performance
- Analyze allocation vs target (rebalancing needs)
- Assess risk exposure (beta, volatility)
- Monitor daily P&L

### 4. Ticker Deep Dive

**Step-by-step**:
1. Navigate to "Asset Deep Dive" in sidebar
2. Enter ticker symbol (e.g., AAPL)
3. Click "Analyze" or press Enter
4. Explore tabs:
   - **Price & Chart**: View candlestick chart with MAs and volume
   - **Technical Indicators**: See all 20+ indicators organized by category
   - **Opportunity Score**: View 10x score with full explainability
   - **Signals**: Check active trading signals

**Example Use Cases**:
- Evaluate potential buy: Check RSI (oversold?), opportunity score, key drivers
- Assess risk: Check volatility (ATR, Bollinger width), signals, risks
- Confirm thesis: Check multiple indicators for confluence
- Compare opportunities: Analyze multiple tickers side-by-side

### 5. Settings

- Configure backend API URL
- Select market data provider
- Enable/disable features

---

## UI/UX Design

### Color Palette

- **Primary**: Deep Blue (#1E40AF)
- **Success/High**: Green (#059669)
- **Warning/Medium**: Amber (#D97706)
- **Danger/Low**: Red (#DC2626)
- **Neutral**: Gray scale

### Score Color Coding

| Score Range | Color  | Badge           | Meaning           |
|-------------|--------|-----------------|-------------------|
| 70-100      | Green  | 🟢 HIGH         | Strong opportunity|
| 50-69       | Amber  | 🟡 MEDIUM       | Moderate potential|
| 0-49        | Red    | 🔴 LOW          | Limited upside    |

### Confidence Color Coding

| Confidence  | Color  | Meaning                     |
|-------------|--------|-----------------------------|
| ≥70%        | Green  | High confidence in data     |
| 50-69%      | Amber  | Moderate confidence         |
| <50%        | Red    | Low confidence (data issues)|

---

## Key Components

### Opportunity Card

Expandable card showing:
- Ticker symbol
- Overall score with color badge
- Confidence percentage
- Timestamp
- 4 detail tabs (Overview, Components, Explainability, Scenarios)

### Component Breakdown Chart

Horizontal bar chart showing contribution of each scoring component:
- Momentum (25%)
- Valuation Divergence (20%)
- Growth Acceleration (25%)
- Relative Strength (15%)
- Sector Momentum (15%)

### Scenario Chart

Bar chart comparing Bull/Base/Bear cases:
- Color-coded bars (Green/Amber/Red)
- Y-axis: Score (0-100)
- Shows score range and volatility

### RSI Gauge

Gauge chart for RSI indicator:
- Green zone: 0-30 (Oversold)
- Gray zone: 30-70 (Neutral)
- Red zone: 70-100 (Overbought)
- Current value indicator

### Allocation Pie Charts

Donut charts showing portfolio allocation by:
- Sector
- Market Cap (Large, Mid, Small)
- Asset Type (Stock, ETF, etc.)

---

## Performance Optimizations

1. **API Client Caching**: `@st.cache_resource` for singleton API client
2. **Lazy Loading**: Data fetched only when tabs/expanders opened
3. **Efficient Data Structures**: Pandas DataFrames for table operations
4. **Plotly**: Hardware-accelerated charts with WebGL
5. **Streamlit Caching**: Future enhancement with `@st.cache_data`

---

## Error Handling

### Backend Unavailable

When backend is not responding:
```
❌ Backend API is not responding.
Please ensure the backend is running at http://localhost:8000
```

### No Data Available

When ticker has no data:
```
❌ Ticker 'XYZ' not found in database.
Please ensure data has been ingested.
```

### Missing Opportunities

When no opportunities match filters:
```
No opportunities match your filters.
Try adjusting the criteria.
```

### API Errors

Graceful degradation:
- Error message displayed in UI
- Component shows "N/A" or empty state
- Application continues functioning

---

## Configuration

### Backend URL

Set via environment variable or config file:

`.env`:
```env
BACKEND_URL=http://localhost:8000
```

Or edit `frontend/utils/config.py`:
```python
def get_api_url():
    return os.getenv("BACKEND_URL", "http://localhost:8000")
```

### Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1E40AF"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F9FAFB"
textColor = "#1F2937"
font = "sans serif"

[server]
port = 8501
headless = false
```

---

## Testing the Frontend

### Manual Testing Checklist

#### Opportunity Radar
- [ ] Filters work correctly (min score, min confidence, sort, limit)
- [ ] Opportunities list displays with correct badges
- [ ] Expandable cards show all 4 tabs
- [ ] Component breakdown chart renders
- [ ] Scenario chart displays correctly
- [ ] Key drivers and risks show
- [ ] Empty state handled gracefully

#### Portfolio Overview
- [ ] Can create new portfolio
- [ ] Portfolio selector works
- [ ] Holdings table displays correctly
- [ ] Allocation charts render (sector, market cap, asset type)
- [ ] Performance metrics display
- [ ] Risk metrics display with interpretation
- [ ] Empty state shows portfolio creation form

#### Ticker Deep Dive
- [ ] Ticker input accepts symbols
- [ ] Price chart renders with candlesticks
- [ ] Moving averages overlay correctly
- [ ] Volume chart displays
- [ ] Technical indicators organized by category
- [ ] RSI gauge renders with correct zones
- [ ] Opportunity score displays
- [ ] Signals tab shows active signals
- [ ] Invalid ticker shows error message

#### General
- [ ] Sidebar navigation works
- [ ] Backend health check displays status
- [ ] Error messages are user-friendly
- [ ] Charts are interactive (zoom, pan, hover)
- [ ] Mobile responsive (basic)

### End-to-End Test

1. **Start backend**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Verify backend health**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Start frontend**:
   ```bash
   cd frontend
   streamlit run app.py
   ```

4. **Test flow**:
   - Visit Dashboard → See status
   - Visit Opportunities → Filter scores ≥60 → Expand top opportunity
   - Visit Portfolio → Create portfolio (if needed) → View analytics
   - Visit Asset Deep Dive → Enter "AAPL" → Analyze

---

## Troubleshooting

### Issue: "Backend API is not responding"

**Solution**:
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify backend URL in config matches actual URL
3. Check firewall/network settings

### Issue: "No opportunities found"

**Solution**:
1. Verify opportunity scores exist in database:
   ```sql
   SELECT COUNT(*) FROM opportunity_scores;
   ```
2. Run scoring job if needed:
   ```bash
   python backend/jobs/score_opportunities.py --all
   ```
3. Adjust filters (lower min_score/min_confidence)

### Issue: "Ticker not found"

**Solution**:
1. Check ticker exists in database:
   ```sql
   SELECT * FROM tickers WHERE ticker = 'XYZ';
   ```
2. Verify price data exists:
   ```sql
   SELECT COUNT(*) FROM price_data WHERE ticker = 'XYZ';
   ```
3. Run data ingestion if needed

### Issue: Charts not rendering

**Solution**:
1. Check browser console for JavaScript errors
2. Update Plotly: `pip install --upgrade plotly`
3. Clear Streamlit cache: `streamlit cache clear`
4. Try different browser

### Issue: Slow performance

**Solution**:
1. Reduce data size (limit parameter)
2. Use shorter time ranges for charts
3. Optimize database queries in backend
4. Enable Streamlit caching with `@st.cache_data`

---

## Future Enhancements

### Phase 2 (Planned)

1. **Dashboard Widgets**
   - Top opportunities widget on home
   - Portfolio summary cards
   - Recent alerts feed

2. **Advanced Charts**
   - Historical score trends (line chart)
   - Correlation heatmaps
   - Risk/return scatter plots

3. **Interactivity**
   - Click ticker in holdings → Jump to deep dive
   - Click opportunity → Add to watchlist
   - Drag-and-drop portfolio rebalancing

4. **Performance**
   - Caching with `@st.cache_data`
   - Lazy loading for large datasets
   - Virtual scrolling for tables

5. **Mobile Optimization**
   - Responsive layouts
   - Touch-friendly controls
   - Simplified mobile views

6. **Export/Reporting**
   - Download portfolio report (PDF)
   - Export opportunities to CSV
   - Share deep dive analysis

7. **Alerts Dashboard**
   - Alert history table
   - Alert filtering
   - Mark as read functionality
   - Alert notifications

---

## Integration with Backend

### Backend Requirements

The frontend expects the backend to provide:

1. **API Endpoints** (documented in backend/app/api/):
   - Portfolio CRUD
   - Market data access
   - Technical indicators
   - Opportunity scores

2. **Data Format** (JSON):
   - Consistent field names
   - Proper data types (floats, dates)
   - Error handling with status codes

3. **CORS Headers** (if needed):
   ```python
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:8501"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

4. **Health Endpoint**:
   ```python
   @app.get("/health")
   def health_check():
       return {"status": "healthy"}
   ```

---

## Development Workflow

### Adding a New Component

1. Create component file: `frontend/components/my_component.py`

2. Define render function:
   ```python
   def render_my_component():
       st.title("My Component")
       # Component logic here
   ```

3. Import in `app.py`:
   ```python
   from components.my_component import render_my_component
   ```

4. Add to navigation:
   ```python
   page = st.radio("Navigation", [..., "My Component"])

   if page == "My Component":
       render_my_component()
   ```

### Adding a New Chart

Use Plotly for consistency:

```python
import plotly.express as px
import plotly.graph_objects as go

# Simple chart
fig = px.bar(df, x="category", y="value", title="My Chart")
st.plotly_chart(fig, use_container_width=True)

# Complex chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["x"], y=df["y"], mode="lines"))
fig.update_layout(title="My Chart", height=400)
st.plotly_chart(fig, use_container_width=True)
```

---

## Dependencies

### Required Packages

```txt
streamlit>=1.30.0
plotly>=5.18.0
pandas>=2.1.0
httpx>=0.25.0
python-dotenv>=1.0.0
```

### Installation

```bash
pip install -r frontend/requirements.txt
```

---

## Conclusion

Phase 1E successfully implements a comprehensive Streamlit frontend with:
- ✅ Full integration with backend API
- ✅ Interactive visualizations with Plotly
- ✅ Opportunity Radar for discovering investments
- ✅ Portfolio analytics and risk metrics
- ✅ Detailed ticker analysis with technical indicators
- ✅ User-friendly UI with color-coded insights
- ✅ Error handling and graceful degradation

**Next Steps**:
1. Run the application: `streamlit run frontend/app.py`
2. Explore the features
3. Provide feedback for improvements
4. Consider Phase 2 enhancements

---

**Total Lines of Code**: ~1,500+
**Components**: 3 major components
**API Endpoints Used**: 15+
**Charts/Visualizations**: 10+ chart types
**Development Time**: Phase 1E completed in single session

---

## Quick Reference

### Common Commands

```bash
# Start frontend
cd frontend && streamlit run app.py

# Start frontend with custom port
streamlit run app.py --server.port 8502

# Clear cache
streamlit cache clear

# View Streamlit config
streamlit config show

# Install dependencies
pip install -r requirements.txt
```

### API URLs (for debugging)

```
http://localhost:8000/docs                          # Backend API docs
http://localhost:8000/health                        # Health check
http://localhost:8000/api/opportunities             # Opportunities list
http://localhost:8000/api/portfolios                # Portfolios list
http://localhost:8000/api/indicators/tickers/AAPL/latest  # Indicators
```

---

**Phase 1E: COMPLETE** ✅
