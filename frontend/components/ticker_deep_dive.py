"""
Ticker Deep Dive Component - Detailed Analysis of Individual Assets.

Features: Price charts, technical indicators, opportunity scores, signals.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from utils.api_client import get_api_client


def render_ticker_deep_dive():
    """Render the Ticker Deep Dive page."""
    st.title("🔍 Asset Deep Dive")
    st.markdown("### Comprehensive analysis of individual tickers")

    api = get_api_client()

    # Check backend health
    if not api.health_check():
        st.error("❌ Backend API is not responding. Please ensure the backend is running at http://localhost:8000")
        return

    # Ticker input
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input(
            "Enter ticker symbol:",
            value="AAPL",
            placeholder="e.g., AAPL, MSFT, TSLA",
            help="Enter a stock ticker to analyze"
        ).upper()

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)

    if not ticker:
        st.info("👆 Enter a ticker symbol to begin analysis")
        return

    if ticker and (analyze_button or True):  # Always show if ticker provided
        render_ticker_analysis(ticker, api)


def render_ticker_analysis(ticker: str, api):
    """Render full analysis for a ticker."""
    st.markdown("---")

    # Fetch data
    with st.spinner(f"Analyzing {ticker}..."):
        ticker_info = api.get_ticker_info(ticker)
        latest_indicators = api.get_latest_indicators(ticker)
        opportunity = api.get_opportunity(ticker, include_history=False)
        signals = api.detect_signals(ticker)
        price_history = api.get_price_history(ticker, start_date=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"))

    # Check if ticker exists
    if not ticker_info or "error" in ticker_info:
        st.error(f"❌ Ticker '{ticker}' not found in database. Please ensure data has been ingested.")
        return

    # Ticker header
    render_ticker_header(ticker, ticker_info)

    st.markdown("---")

    # Main content in tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Price & Chart",
        "📊 Technical Indicators",
        "🎯 Opportunity Score",
        "⚡ Signals"
    ])

    with tab1:
        render_price_chart_tab(ticker, price_history, latest_indicators, api)

    with tab2:
        render_indicators_tab(ticker, latest_indicators, api)

    with tab3:
        render_opportunity_tab(ticker, opportunity, api)

    with tab4:
        render_signals_tab(ticker, signals)


def render_ticker_header(ticker: str, info: Dict):
    """Render ticker header with key information."""
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.markdown(f"### {ticker}")
        if "name" in info:
            st.caption(info["name"])

    with col2:
        if "sector" in info:
            st.metric("Sector", info["sector"])

    with col3:
        if "market_cap_category" in info:
            st.metric("Market Cap", info["market_cap_category"])

    with col4:
        if "asset_type" in info:
            st.metric("Type", info["asset_type"])


def render_price_chart_tab(ticker: str, price_history: List[Dict], indicators: Dict, api):
    """Render price chart with technical overlays."""
    st.markdown("#### Price Chart with Technical Indicators")

    if not price_history or len(price_history) == 0:
        st.warning("No price history available")
        return

    # Convert to dataframe
    df = pd.DataFrame(price_history)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # Create candlestick chart
    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df["timestamp"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Price"
    ))

    # Add moving averages if available
    if indicators and "sma_20" in indicators:
        # Fetch indicator history for overlays
        indicator_history = api.get_indicator_history(ticker, days=90)
        if indicator_history:
            ind_df = pd.DataFrame(indicator_history)
            ind_df["timestamp"] = pd.to_datetime(ind_df["timestamp"])

            # SMA 20
            sma20_data = ind_df[ind_df["indicator_name"] == "sma_20"]
            if not sma20_data.empty:
                fig.add_trace(go.Scatter(
                    x=sma20_data["timestamp"],
                    y=sma20_data["value"],
                    mode="lines",
                    name="SMA 20",
                    line=dict(color="orange", width=1)
                ))

            # SMA 50
            sma50_data = ind_df[ind_df["indicator_name"] == "sma_50"]
            if not sma50_data.empty:
                fig.add_trace(go.Scatter(
                    x=sma50_data["timestamp"],
                    y=sma50_data["value"],
                    mode="lines",
                    name="SMA 50",
                    line=dict(color="blue", width=1)
                ))

    fig.update_layout(
        title=f"{ticker} Price Chart (90 Days)",
        yaxis_title="Price ($)",
        xaxis_title="Date",
        height=500,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Volume chart
    if "volume" in df.columns:
        st.markdown("#### Volume")
        vol_fig = go.Figure()
        vol_fig.add_trace(go.Bar(
            x=df["timestamp"],
            y=df["volume"],
            name="Volume",
            marker_color="lightblue"
        ))
        vol_fig.update_layout(
            yaxis_title="Volume",
            xaxis_title="Date",
            height=200,
            showlegend=False
        )
        st.plotly_chart(vol_fig, use_container_width=True)


def render_indicators_tab(ticker: str, latest_indicators: Dict, api):
    """Render technical indicators."""
    st.markdown("#### Technical Indicators")

    if not latest_indicators or "indicators" not in latest_indicators:
        st.warning("No indicators available for this ticker")
        return

    indicators = latest_indicators["indicators"]

    # Organize indicators by category
    momentum_indicators = {}
    trend_indicators = {}
    volatility_indicators = {}
    volume_indicators = {}

    for ind_name, ind_value in indicators.items():
        if ind_name in ["rsi_14", "stochastic_k", "stochastic_d", "williams_r"]:
            momentum_indicators[ind_name] = ind_value
        elif ind_name in ["sma_20", "sma_50", "sma_200", "ema_12", "ema_26", "macd", "macd_signal", "macd_histogram", "adx"]:
            trend_indicators[ind_name] = ind_value
        elif ind_name in ["bollinger_upper", "bollinger_middle", "bollinger_lower", "atr_14"]:
            volatility_indicators[ind_name] = ind_value
        elif ind_name in ["obv", "volume_sma_20"]:
            volume_indicators[ind_name] = ind_value

    # Display in columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 📊 Momentum Indicators")
        for name, value in momentum_indicators.items():
            display_name = name.replace("_", " ").upper()
            if value is not None:
                st.metric(display_name, f"{value:.2f}")
            else:
                st.metric(display_name, "N/A")

        st.markdown("---")

        st.markdown("##### 📈 Trend Indicators")
        for name, value in trend_indicators.items():
            display_name = name.replace("_", " ").upper()
            if value is not None:
                if "sma" in name or "ema" in name or "bollinger" in name:
                    st.metric(display_name, f"${value:.2f}")
                else:
                    st.metric(display_name, f"{value:.2f}")
            else:
                st.metric(display_name, "N/A")

    with col2:
        st.markdown("##### 🌊 Volatility Indicators")
        for name, value in volatility_indicators.items():
            display_name = name.replace("_", " ").upper()
            if value is not None:
                if "bollinger" in name:
                    st.metric(display_name, f"${value:.2f}")
                else:
                    st.metric(display_name, f"{value:.2f}")
            else:
                st.metric(display_name, "N/A")

        st.markdown("---")

        st.markdown("##### 📦 Volume Indicators")
        for name, value in volume_indicators.items():
            display_name = name.replace("_", " ").upper()
            if value is not None:
                st.metric(display_name, f"{value:,.0f}")
            else:
                st.metric(display_name, "N/A")

    # RSI Gauge Chart
    if "rsi_14" in indicators and indicators["rsi_14"] is not None:
        st.markdown("---")
        st.markdown("##### RSI Gauge")
        render_rsi_gauge(indicators["rsi_14"])


def render_rsi_gauge(rsi_value: float):
    """Render RSI gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=rsi_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "RSI (14-day)"},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "#059669"},  # Oversold - Green
                {'range': [30, 70], 'color': "lightgray"},  # Neutral
                {'range': [70, 100], 'color': "#DC2626"}  # Overbought - Red
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))

    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    # Interpretation
    if rsi_value < 30:
        st.success("🟢 Oversold: Potential buying opportunity")
    elif rsi_value > 70:
        st.error("🔴 Overbought: Potential selling pressure")
    else:
        st.info("⚪ Neutral: RSI in normal range")


def render_opportunity_tab(ticker: str, opportunity: Dict, api):
    """Render opportunity score and explainability."""
    st.markdown("#### 🎯 10x Opportunity Score")

    if not opportunity or "error" in opportunity:
        st.warning(f"No opportunity score available for {ticker}")
        return

    # Main score
    score = opportunity.get("score", 0)
    confidence = opportunity.get("confidence", 0)

    # Score color coding
    if score >= 70:
        score_color = "#059669"
        badge = "🟢 HIGH OPPORTUNITY"
    elif score >= 50:
        score_color = "#D97706"
        badge = "🟡 MODERATE OPPORTUNITY"
    else:
        score_color = "#DC2626"
        badge = "🔴 LOW OPPORTUNITY"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Overall Score", f"{score:.1f}/100")
        st.markdown(f"**{badge}**")

    with col2:
        st.metric("Confidence", f"{confidence:.0f}%")

    with col3:
        st.metric("Updated", opportunity.get("timestamp", "N/A")[:10])

    st.markdown("---")

    # Scenarios
    scenarios = opportunity.get("scenarios", {})
    if scenarios:
        st.markdown("#### Scenario Analysis")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🐂 Bull Case", f"{scenarios.get('bull', 0):.1f}")
        with col2:
            st.metric("📊 Base Case", f"{scenarios.get('base', 0):.1f}")
        with col3:
            st.metric("🐻 Bear Case", f"{scenarios.get('bear', 0):.1f}")

    st.markdown("---")

    # Get explainability
    explainability = api.get_opportunity_explainability(ticker)

    if explainability:
        col1, col2 = st.columns(2)

        with col1:
            # Key Drivers
            key_drivers = explainability.get("key_drivers", [])
            if key_drivers:
                st.markdown("#### 🚀 Key Drivers")
                for i, driver in enumerate(key_drivers, 1):
                    st.markdown(f"{i}. {driver}")

        with col2:
            # Risks
            risks = explainability.get("risks", [])
            if risks:
                st.markdown("#### ⚠️ Risks")
                for i, risk in enumerate(risks, 1):
                    st.markdown(f"{i}. {risk}")

    # Components
    st.markdown("---")
    st.markdown("#### Component Breakdown")

    components = opportunity.get("components", {})
    if components:
        # Create dataframe
        comp_list = []
        for comp_name, comp_data in components.items():
            comp_list.append({
                "Component": comp_name.replace("_", " ").title(),
                "Score": comp_data["score"],
                "Weight": comp_data["weight"] * 100,
                "Contribution": comp_data["contribution"]
            })

        df = pd.DataFrame(comp_list)

        # Bar chart
        fig = px.bar(
            df,
            x="Component",
            y="Contribution",
            color="Contribution",
            color_continuous_scale="RdYlGn",
            title="Component Contributions"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def render_signals_tab(ticker: str, signals: Dict):
    """Render trading signals."""
    st.markdown("#### ⚡ Trading Signals")

    if not signals or "error" in signals:
        st.warning(f"No signals available for {ticker}")
        return

    signal_list = signals.get("signals", [])

    if not signal_list or len(signal_list) == 0:
        st.info("No active signals detected for this ticker")
        return

    st.markdown(f"**{len(signal_list)} signal(s) detected**")

    # Display signals
    for signal in signal_list:
        signal_type = signal.get("type", "unknown")
        indicator = signal.get("indicator", "unknown")
        strength = signal.get("strength", "moderate")
        description = signal.get("description", "No description")

        # Color coding
        if signal_type in ["oversold", "bullish"]:
            color = "green"
            icon = "🟢"
        elif signal_type in ["overbought", "bearish"]:
            color = "red"
            icon = "🔴"
        else:
            color = "gray"
            icon = "⚪"

        # Strength badge
        if strength == "strong":
            strength_badge = "🔥 STRONG"
        else:
            strength_badge = "MODERATE"

        with st.container():
            st.markdown(f"{icon} **{signal_type.upper()}** - {indicator} ({strength_badge})")
            st.caption(description)
            st.markdown("---")
