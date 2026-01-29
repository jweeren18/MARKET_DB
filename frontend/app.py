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
from components.opportunity_radar import render_opportunity_radar
from components.portfolio_overview import render_portfolio_overview
from components.ticker_deep_dive import render_ticker_deep_dive


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
        st.caption("✅ Phase 1A-1D Complete")
        st.caption("📊 Current: Frontend (Phase 1E)")
        st.caption("🚀 Backend API Ready!")

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
        **Current Status (Phase 1A-1D Complete):**
        - ✅ Backend API operational (FastAPI + PostgreSQL + TimescaleDB)
        - ✅ Schwab API integration with OAuth 2.0
        - ✅ 2 years historical data (10,578 records, 21 tickers)
        - ✅ Portfolio analytics (P&L, returns, risk metrics)
        - ✅ Technical indicators (20+ indicators calculated daily)
        - ✅ Signal detection (RSI, MACD, Bollinger Bands, etc.)
        - ✅ 10x Opportunity Scorer (rule-based with full explainability)
        - ✅ Automated daily scoring via Airflow

        **Phase 1E (Current):**
        - 🚧 Building Streamlit frontend
        - 🚧 Opportunity Radar dashboard
        - 🚧 Portfolio visualizations
        - 🚧 Interactive charts
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
    render_portfolio_overview()


def show_opportunities():
    """Opportunity radar page."""
    render_opportunity_radar()


def show_asset_deep_dive():
    """Asset deep dive page."""
    render_ticker_deep_dive()


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
