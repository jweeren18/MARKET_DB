"""
Portfolio Overview Component - Portfolio Analytics and Visualizations.

Features: Holdings table, allocation charts, performance metrics, risk analysis.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional
from datetime import datetime

from utils.api_client import get_api_client


def render_portfolio_overview():
    """Render the main Portfolio Overview dashboard."""
    st.title("💼 Portfolio Overview")
    st.markdown("### Track your investments with real-time analytics")

    api = get_api_client()

    # Check backend health
    if not api.health_check():
        st.error("❌ Backend API is not responding. Please ensure the backend is running at http://localhost:8000")
        return

    # Get portfolios
    with st.spinner("Loading portfolios..."):
        portfolios = api.get_portfolios()

    if not portfolios or len(portfolios) == 0:
        render_empty_state(api)
        return

    # Portfolio selector
    portfolio_names = [p["name"] for p in portfolios]
    selected_portfolio_name = st.selectbox("Select Portfolio", portfolio_names, help="Choose a portfolio to view")

    # Get selected portfolio
    selected_portfolio = next(p for p in portfolios if p["name"] == selected_portfolio_name)
    portfolio_id = selected_portfolio["id"]

    st.markdown("---")

    # Fetch portfolio details
    with st.spinner(f"Loading {selected_portfolio_name} details..."):
        analytics = api.get_portfolio_analytics(portfolio_id)
        holdings = api.get_portfolio_holdings(portfolio_id)

    if not analytics or "error" in analytics:
        st.warning("Could not load portfolio analytics")
        return

    # Summary metrics
    render_summary_metrics(analytics)

    st.markdown("---")

    # Two column layout
    col1, col2 = st.columns(2)

    with col1:
        render_holdings_table(holdings)

    with col2:
        render_allocation_charts(analytics)

    st.markdown("---")

    # Performance and risk
    col1, col2 = st.columns(2)

    with col1:
        render_performance_metrics(analytics)

    with col2:
        render_risk_metrics(analytics)


def render_empty_state(api):
    """Render empty state when no portfolios exist."""
    st.info("👋 Welcome! You don't have any portfolios yet. Let's create your first one.")

    st.markdown("### Create Your First Portfolio")

    with st.form("create_portfolio_form"):
        portfolio_name = st.text_input("Portfolio Name", placeholder="e.g., My Investments")
        portfolio_description = st.text_area("Description (optional)", placeholder="e.g., Long-term growth portfolio")

        submit = st.form_submit_button("Create Portfolio")

        if submit:
            if not portfolio_name:
                st.error("Please provide a portfolio name")
            else:
                result = api.create_portfolio(portfolio_name, portfolio_description)
                if result and "id" in result:
                    st.success(f"✅ Portfolio '{portfolio_name}' created successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create portfolio. Please try again.")


def render_summary_metrics(analytics: Dict):
    """Render summary metrics row."""
    st.markdown("### 📊 Summary")

    # Extract metrics
    total_value = analytics.get("total_value", 0)
    total_cost = analytics.get("total_cost_basis", 0)
    total_gain = analytics.get("total_gain_loss", 0)
    total_gain_pct = analytics.get("total_gain_loss_pct", 0)
    daily_pnl = analytics.get("daily_pnl", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Value",
            f"${total_value:,.2f}",
            help="Current market value of all holdings"
        )

    with col2:
        st.metric(
            "Total Gain/Loss",
            f"${total_gain:,.2f}",
            f"{total_gain_pct:+.2f}%",
            delta_color="normal",
            help="Unrealized gain/loss since purchase"
        )

    with col3:
        st.metric(
            "Cost Basis",
            f"${total_cost:,.2f}",
            help="Total amount invested"
        )

    with col4:
        st.metric(
            "Daily P&L",
            f"${daily_pnl:,.2f}",
            delta_color="normal",
            help="Today's profit/loss"
        )


def render_holdings_table(holdings: List[Dict]):
    """Render holdings table."""
    st.markdown("### 📋 Holdings")

    if not holdings or len(holdings) == 0:
        st.info("No holdings in this portfolio yet.")
        return

    # Create dataframe
    df = pd.DataFrame(holdings)

    # Calculate additional columns if not present
    if "current_value" not in df.columns and "current_price" in df.columns:
        df["current_value"] = df["quantity"] * df["current_price"]

    if "gain_loss" not in df.columns and "current_value" in df.columns and "cost_basis" in df.columns:
        df["gain_loss"] = df["current_value"] - df["cost_basis"]

    if "gain_loss_pct" not in df.columns and "gain_loss" in df.columns and "cost_basis" in df.columns:
        df["gain_loss_pct"] = (df["gain_loss"] / df["cost_basis"]) * 100

    # Select and format columns for display
    display_cols = []
    if "ticker" in df.columns:
        display_cols.append("ticker")
    if "quantity" in df.columns:
        display_cols.append("quantity")
    if "current_price" in df.columns:
        display_cols.append("current_price")
    if "cost_basis" in df.columns:
        display_cols.append("cost_basis")
    if "current_value" in df.columns:
        display_cols.append("current_value")
    if "gain_loss" in df.columns:
        display_cols.append("gain_loss")
    if "gain_loss_pct" in df.columns:
        display_cols.append("gain_loss_pct")

    # Display table
    display_df = df[display_cols].copy()

    # Rename columns
    display_df.columns = [
        "Ticker", "Quantity", "Price", "Cost Basis",
        "Value", "Gain/Loss", "Gain/Loss %"
    ][:len(display_cols)]

    # Format numbers
    format_dict = {}
    if "Quantity" in display_df.columns:
        format_dict["Quantity"] = "{:.4f}"
    if "Price" in display_df.columns:
        format_dict["Price"] = "${:.2f}"
    if "Cost Basis" in display_df.columns:
        format_dict["Cost Basis"] = "${:.2f}"
    if "Value" in display_df.columns:
        format_dict["Value"] = "${:.2f}"
    if "Gain/Loss" in display_df.columns:
        format_dict["Gain/Loss"] = "${:.2f}"
    if "Gain/Loss %" in display_df.columns:
        format_dict["Gain/Loss %"] = "{:.2f}%"

    st.dataframe(
        display_df.style.format(format_dict),
        use_container_width=True,
        hide_index=True,
        height=300
    )


def render_allocation_charts(analytics: Dict):
    """Render allocation charts (sector, market cap, asset type)."""
    st.markdown("### 📊 Allocation")

    allocations = analytics.get("allocations", {})

    if not allocations:
        st.info("Allocation data not available")
        return

    # Tabs for different allocation views
    tab1, tab2, tab3 = st.tabs(["By Sector", "By Market Cap", "By Asset Type"])

    with tab1:
        sector_data = allocations.get("by_sector", {})
        if sector_data:
            render_pie_chart(sector_data, "Sector Allocation")
        else:
            st.info("Sector data not available")

    with tab2:
        market_cap_data = allocations.get("by_market_cap", {})
        if market_cap_data:
            render_pie_chart(market_cap_data, "Market Cap Allocation")
        else:
            st.info("Market cap data not available")

    with tab3:
        asset_type_data = allocations.get("by_asset_type", {})
        if asset_type_data:
            render_pie_chart(asset_type_data, "Asset Type Allocation")
        else:
            st.info("Asset type data not available")


def render_pie_chart(data: Dict, title: str):
    """Render a pie chart for allocation data."""
    if not data:
        st.info("No data available")
        return

    df = pd.DataFrame([
        {"Category": k, "Value": v}
        for k, v in data.items()
    ])

    fig = px.pie(
        df,
        values="Value",
        names="Category",
        title=title,
        hole=0.4  # Donut chart
    )

    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=300)

    st.plotly_chart(fig, use_container_width=True)


def render_performance_metrics(analytics: Dict):
    """Render performance metrics."""
    st.markdown("### 📈 Performance")

    returns = analytics.get("returns", {})

    if not returns:
        st.info("Performance data not available")
        return

    # Time-weighted return
    twr = returns.get("time_weighted_return", 0)
    st.metric("Time-Weighted Return (TWR)", f"{twr:.2f}%", help="Return excluding the impact of cash flows")

    # Money-weighted return (IRR)
    mwr = returns.get("money_weighted_return", 0)
    st.metric("Money-Weighted Return (MWR)", f"{mwr:.2f}%", help="Internal rate of return considering cash flow timing")

    # Period returns
    st.markdown("#### Period Returns")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("1 Month", f"{returns.get('return_1m', 0):.2f}%")
    with col2:
        st.metric("3 Month", f"{returns.get('return_3m', 0):.2f}%")
    with col3:
        st.metric("YTD", f"{returns.get('return_ytd', 0):.2f}%")


def render_risk_metrics(analytics: Dict):
    """Render risk metrics."""
    st.markdown("### ⚠️ Risk Metrics")

    risk = analytics.get("risk_metrics", {})

    if not risk:
        st.info("Risk metrics not available")
        return

    # Volatility
    volatility = risk.get("volatility", 0)
    st.metric("Volatility (Annualized)", f"{volatility:.2f}%", help="Standard deviation of returns")

    # Beta
    beta = risk.get("beta", 0)
    st.metric("Beta (vs SPY)", f"{beta:.2f}", help="Sensitivity to market movements")

    # Sharpe ratio
    sharpe = risk.get("sharpe_ratio", 0)
    st.metric("Sharpe Ratio", f"{sharpe:.2f}", help="Risk-adjusted return (>1.0 is good)")

    # Max drawdown
    max_dd = risk.get("max_drawdown", 0)
    st.metric("Max Drawdown", f"{max_dd:.2f}%", help="Largest peak-to-trough decline")

    # Risk interpretation
    st.markdown("---")
    st.markdown("#### Risk Assessment")

    if volatility < 15:
        risk_level = "🟢 Low"
    elif volatility < 25:
        risk_level = "🟡 Moderate"
    else:
        risk_level = "🔴 High"

    st.markdown(f"**Risk Level:** {risk_level}")

    if beta < 0.8:
        st.caption("Portfolio is less volatile than the market")
    elif beta < 1.2:
        st.caption("Portfolio moves in line with the market")
    else:
        st.caption("Portfolio is more volatile than the market")
