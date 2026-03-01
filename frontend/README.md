# Market Intelligence Dashboard - Streamlit Frontend

Python-based dashboard interface built with Streamlit for interactive portfolio analytics and opportunity identification.

## Structure

```
frontend/
├── app.py              # Main Streamlit application entry point
├── pages/              # Multi-page app pages (coming soon)
├── components/         # Reusable UI components (coming soon)
└── utils/              # Utility modules
    ├── config.py       # Configuration management
    └── api_client.py   # Backend API client
```

## Running the Dashboard

```bash
# From project root
uv run streamlit run frontend/app.py

# Or with custom port
uv run streamlit run frontend/app.py --server.port 8501
```

The dashboard will be available at [http://localhost:8501](http://localhost:8501)

## Features

### Current (Phase 1B)
- ✅ Basic navigation and layout
- ✅ API connectivity to FastAPI backend
- ✅ Configuration management
- ✅ Placeholder pages for all major features

### Coming Soon

#### Phase 1C: Portfolio Analytics
- Holdings table with live prices
- Allocation charts (sector, market cap, asset type)
- Performance charts (TWR/MWR over time)
- Risk metrics dashboard (volatility, beta, Sharpe ratio)
- Transaction history

#### Phase 1D: Technical Indicators
- Interactive price charts with overlays
- Technical indicators display (MA, RSI, MACD, volume)
- Indicator calculation visualization

#### Phase 1E: Opportunity Scoring
- Opportunity radar with sortable/filterable table
- Score breakdown visualizations
- Bull/base/bear scenario charts
- Explainability display (feature contributions)
- Asset deep dive with full scoring details

#### Phase 1F: Alerts & Polish
- Alert notifications in sidebar
- Real-time updates
- Error handling and loading states
- Performance optimization

## Development

### Adding New Pages

Streamlit supports multi-page apps using the `pages/` directory:

```python
# frontend/pages/1_Portfolio.py
import streamlit as st

st.title("Portfolio Overview")
# ... page content
```

Pages are automatically added to the sidebar navigation.

### Creating Components

Reusable components can be created in the `components/` directory:

```python
# frontend/components/metric_card.py
import streamlit as st

def metric_card(title: str, value: str, delta: str = None):
    """Display a metric card."""
    st.metric(label=title, value=value, delta=delta)
```

### API Integration

Use the API client for backend communication:

```python
from utils.api_client import get_api_client

api = get_api_client()

# Fetch portfolios
portfolios = api.get_portfolios()

# Check backend health
if api.health_check():
    st.success("Backend connected")
```

## Configuration

Environment variables (from `.env`):
- `BACKEND_PORT`: Backend API port (default: 8000)
- `FRONTEND_PORT`: Streamlit port (default: 8501)

## Dependencies

Key dependencies (see [pyproject.toml](../pyproject.toml)):
- `streamlit>=1.30.0`: Dashboard framework
- `plotly>=5.18.0`: Interactive charts
- `pandas>=2.2.0`: Data manipulation
- `httpx>=0.26.0`: API client

## Design Guidelines

### Layout
- Use `st.set_page_config(layout="wide")` for dashboard pages
- Use columns (`st.columns()`) for responsive layouts
- Use expanders (`st.expander()`) for detailed information

### Styling
- Primary color: Deep blue (#1E40AF)
- Success/High: Green (#059669)
- Warning/Medium: Amber (#D97706)
- Danger/Low: Red (#DC2626)

### User Experience
- Always show loading states (`st.spinner()`)
- Display error messages clearly (`st.error()`)
- Show confidence levels alongside scores
- Provide explainability for all calculations

## Testing

```bash
# Run frontend tests
cd frontend
uv run pytest test_*.py
```

## Troubleshooting

### Backend Connection Failed
- Ensure backend API is running: `cd backend && uv run uvicorn app.main:app --reload`
- Check `BACKEND_PORT` in `.env` matches running backend
- Visit http://localhost:8000/docs to verify API is accessible

### Port Already in Use
```bash
# Run on different port
uv run streamlit run frontend/app.py --server.port 8502
```

### Module Import Errors
```bash
# Reinstall dependencies
uv sync
```

## Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)
- [Backend API Docs](http://localhost:8000/docs)
