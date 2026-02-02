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


def apply_theme(theme: str):
    """Apply custom CSS based on selected theme."""
    if theme == 'dark':
        st.markdown("""
            <style>
            /* Dark theme colors */
            :root {
                --bg-color: #0E1117;
                --secondary-bg: #262730;
                --text-color: #FAFAFA;
                --primary-color: #3B82F6;
            }

            /* Override Streamlit defaults */
            .stApp {
                background-color: #0E1117;
            }

            .main > div {
                padding-top: 2rem;
            }

            h1, h2, h3, h4, h5, h6 {
                color: #3B82F6 !important;
            }

            .stMetric {
                background-color: #262730 !important;
                padding: 1rem;
                border-radius: 0.5rem;
                border: 1px solid #3B3B3B;
            }

            .stMetric label {
                color: #FAFAFA !important;
            }

            /* Sidebar styling */
            [data-testid="stSidebar"] {
                background-color: #262730;
            }

            /* Cards and containers */
            .element-container {
                color: #FAFAFA;
            }

            /* Expanders */
            .streamlit-expanderHeader {
                background-color: #262730 !important;
                color: #FAFAFA !important;
            }

            /* Tables */
            .dataframe {
                color: #FAFAFA !important;
            }

            /* Buttons */
            .stButton button {
                background-color: #3B82F6;
                color: white;
            }

            /* Text inputs */
            .stTextInput input {
                background-color: #262730 !important;
                color: #FAFAFA !important;
                border: 1px solid #3B3B3B;
            }

            /* Select boxes */
            .stSelectbox [data-baseweb="select"] {
                background-color: #262730 !important;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        # Light theme (default)
        st.markdown("""
            <style>
            .main > div {
                padding-top: 2rem;
            }
            h1, h2, h3 {
                color: #1E40AF;
            }
            .stMetric {
                background-color: #F9FAFB;
                padding: 1rem;
                border-radius: 0.5rem;
            }
            </style>
        """, unsafe_allow_html=True)


def main():
    """Main Streamlit application."""

    # Page configuration
    st.set_page_config(
        page_title="Market Intelligence Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize theme in session state
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'

    # Apply theme CSS
    apply_theme(st.session_state.theme)

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

        # Theme toggle
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("Theme")
        with col2:
            if st.button("🌓", help="Toggle dark/light mode", key="theme_toggle"):
                st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
                st.rerun()

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
