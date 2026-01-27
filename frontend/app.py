"""
Market Intelligence Dashboard - Streamlit Frontend

Main entry point for the Streamlit dashboard application.
"""

import streamlit as st
from pathlib import Path
import sys

# Add backend to path for imports
BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from utils.config import get_api_url


def main():
    """Main Streamlit application."""

    # Page configuration
    st.set_page_config(
        page_title="Market Intelligence Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main > div {
            padding-top: 2rem;
        }
        h1 {
            color: #1E40AF;
        }
        .stMetric {
            background-color: #F9FAFB;
            padding: 1rem;
            border-radius: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.title("📊 Market Intelligence")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["Dashboard", "Portfolio", "Opportunities", "Asset Deep Dive", "Settings"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.caption("Phase 1B: Data Ingestion Complete")
        st.caption("Next: Analytics Service (Phase 1C)")

    # Main content area
    if page == "Dashboard":
        show_dashboard()
    elif page == "Portfolio":
        show_portfolio()
    elif page == "Opportunities":
        show_opportunities()
    elif page == "Asset Deep Dive":
        show_asset_deep_dive()
    elif page == "Settings":
        show_settings()


def show_dashboard():
    """Home dashboard page."""
    st.title("Market Intelligence Dashboard")
    st.markdown("### Welcome to your personal investment intelligence platform")

    st.info("""
        **Current Status (Phase 1B):**
        - ✅ Backend API operational
        - ✅ PostgreSQL + TimescaleDB configured
        - ✅ Market data ingestion (yfinance)
        - ✅ 21 sample tickers seeded

        **Coming Soon:**
        - Portfolio analytics (Phase 1C)
        - Technical indicators (Phase 1D)
        - 10x opportunity scoring (Phase 1E)
    """)

    # Placeholder metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Portfolios", "0", help="Total portfolios tracked")
    with col2:
        st.metric("Holdings", "0", help="Total positions")
    with col3:
        st.metric("Total Value", "$0", help="Combined portfolio value")
    with col4:
        st.metric("Today's P&L", "$0", help="Today's profit/loss")

    st.markdown("---")
    st.markdown("### Recent Market Activity")
    st.info("Market data visualization coming in Phase 1C")


def show_portfolio():
    """Portfolio overview page."""
    st.title("Portfolio Overview")
    st.info("Portfolio analytics coming in Phase 1C")

    st.markdown("### Planned Features:")
    st.markdown("""
    - Holdings table with live prices
    - Allocation charts (sector, market cap, asset type)
    - Performance charts (TWR/MWR)
    - Risk metrics dashboard
    - Transaction history
    """)


def show_opportunities():
    """Opportunity radar page."""
    st.title("Opportunity Radar")
    st.info("10x opportunity scoring coming in Phase 1E")

    st.markdown("### Planned Features:")
    st.markdown("""
    - Sortable/filterable opportunity table
    - Score badges with color coding
    - Confidence indicators
    - Score breakdown visualizations
    - Bull/base/bear scenario charts
    """)


def show_asset_deep_dive():
    """Asset deep dive page."""
    st.title("Asset Deep Dive")

    # Ticker input
    ticker = st.text_input("Enter ticker symbol:", value="AAPL").upper()

    if ticker:
        st.info(f"Technical indicators and opportunity scores for {ticker} coming in Phases 1D-1E")

        st.markdown("### Planned Features:")
        st.markdown("""
        - Interactive price chart with technical overlays
        - Technical indicators panel (RSI, MACD, etc.)
        - Fundamental metrics grid
        - Opportunity score card with explainability
        - Key drivers and risks
        """)


def show_settings():
    """Settings page."""
    st.title("Settings")

    st.markdown("### API Configuration")
    api_url = st.text_input("Backend API URL:", value=get_api_url())

    st.markdown("### Data Provider")
    provider = st.selectbox(
        "Market Data Provider:",
        ["Auto (yfinance in dev, Schwab in prod)", "Schwab API", "yfinance"],
        help="Select your preferred market data provider"
    )

    st.markdown("### Preferences")
    st.checkbox("Show portfolio allocation chart", value=True)
    st.checkbox("Show risk metrics", value=True)
    st.checkbox("Enable alert notifications", value=True)

    if st.button("Save Settings"):
        st.success("Settings saved successfully!")


if __name__ == "__main__":
    main()
