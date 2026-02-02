"""
Opportunity Radar Component - 10x Investment Opportunities Dashboard.

Main feature: Displays scored opportunities with filtering, sorting, and detailed explainability.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from utils.api_client import get_api_client


def render_opportunity_radar():
    """Render the main Opportunity Radar dashboard."""
    st.title("🎯 Opportunity Radar")
    st.markdown("### Discover high-potential investment opportunities with AI-powered scoring")

    api = get_api_client()

    # Check backend health
    if not api.health_check():
        st.error("❌ Backend API is not responding. Please ensure the backend is running at http://localhost:8000")
        return

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        min_score = st.slider("Min Score", 0, 100, 60, 5, help="Minimum opportunity score (0-100)")
    with col2:
        min_confidence = st.slider("Min Confidence", 0, 100, 50, 5, help="Minimum confidence level")
    with col3:
        sort_by = st.selectbox("Sort By", ["score", "confidence", "ticker"], help="Sort opportunities by")
    with col4:
        limit = st.number_input("Limit", 10, 500, 50, 10, help="Maximum results to return")

    st.markdown("---")

    # Fetch opportunities with full details in one API call
    with st.spinner("Loading opportunities..."):
        result = api.list_opportunities(
            min_score=min_score,
            min_confidence=min_confidence,
            limit=limit,
            sort_by=sort_by,
            include_details=True  # Get all data in one API call for faster loading
        )

    if not result or "error" in result:
        st.warning("No opportunities found or error fetching data.")
        return

    opportunities = result.get("opportunities", [])
    count = result.get("count", 0)

    if count == 0:
        st.info("No opportunities match your filters. Try adjusting the criteria.")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    scores = [opp["score"] for opp in opportunities]
    confidences = [opp["confidence"] for opp in opportunities]

    with col1:
        st.metric("Total Opportunities", count)
    with col2:
        st.metric("Avg Score", f"{sum(scores) / len(scores):.1f}")
    with col3:
        st.metric("Avg Confidence", f"{sum(confidences) / len(confidences):.1f}%")
    with col4:
        high_confidence_count = sum(1 for c in confidences if c >= 70)
        st.metric("High Confidence (≥70%)", high_confidence_count)

    st.markdown("---")

    # Opportunities table with expandable details
    st.markdown("### 📊 Scored Opportunities")

    for opp in opportunities:
        render_opportunity_card(opp)


def render_opportunity_card(opp: Dict):
    """Render an expandable opportunity card."""
    ticker = opp["ticker"]
    score = opp["score"]
    confidence = opp["confidence"]
    timestamp = opp["timestamp"]

    # Score color coding
    if score >= 70:
        score_color = "#059669"  # Green
        badge = "🟢 HIGH"
    elif score >= 50:
        score_color = "#D97706"  # Amber
        badge = "🟡 MEDIUM"
    else:
        score_color = "#DC2626"  # Red
        badge = "🔴 LOW"

    # Confidence color
    if confidence >= 70:
        conf_color = "#059669"
    elif confidence >= 50:
        conf_color = "#D97706"
    else:
        conf_color = "#DC2626"

    # Card header
    with st.expander(f"**{ticker}** | Score: **{score:.1f}** {badge} | Confidence: **{confidence:.0f}%** | {timestamp}", expanded=False):
        # Use pre-loaded data from the list API call
        if "explanation" not in opp or "components" not in opp:
            st.warning(f"Detailed data not available for {ticker}")
            return

        # Extract data for rendering tabs
        explanation = opp["explanation"]

        # Build details object for overview and scenarios tabs
        details = {
            "ticker": ticker,
            "score": score,
            "confidence": confidence,
            "timestamp": timestamp,
            "scenarios": explanation.get("scenarios", {})
        }

        # Build components data for components tab
        components_data = {
            "components": opp["components"]
        }

        # Explainability is already in the right format
        explainability = {
            "key_drivers": explanation.get("key_drivers", []),
            "risks": explanation.get("risks", []),
            "components": explanation.get("components", {})
        }

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🔍 Components", "💡 Explainability", "📊 Scenarios"])

        with tab1:
            render_overview_tab(details)

        with tab2:
            render_components_tab(components_data)

        with tab3:
            render_explainability_tab(explainability)

        with tab4:
            render_scenarios_tab(details)


def render_overview_tab(details: Dict):
    """Render overview tab with key metrics."""
    st.markdown("#### Key Metrics")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Score", f"{details['score']:.1f}/100")
    with col2:
        st.metric("Confidence", f"{details['confidence']:.1f}%")
    with col3:
        st.metric("Timestamp", details["timestamp"][:10])

    st.markdown("---")

    # Scenarios
    scenarios = details.get("scenarios", {})
    if scenarios:
        st.markdown("#### Scenario Analysis")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🐂 Bull Case", f"{scenarios.get('bull', 0):.1f}")
        with col2:
            st.metric("📊 Base Case", f"{scenarios.get('base', 0):.1f}")
        with col3:
            st.metric("🐻 Bear Case", f"{scenarios.get('bear', 0):.1f}")


def render_components_tab(components_data: Dict):
    """Render components breakdown with visualization."""
    if not components_data or "components" not in components_data:
        st.warning("No component data available")
        return

    st.markdown("#### Component Breakdown")

    components = components_data["components"]

    # Create dataframe for visualization
    comp_list = []
    for comp_name, comp_data in components.items():
        comp_list.append({
            "Component": comp_name.replace("_", " ").title(),
            "Score": comp_data["score"],
            "Weight": comp_data["weight"] * 100,
            "Contribution": comp_data["contribution"]
        })

    df = pd.DataFrame(comp_list)

    # Display as table
    st.dataframe(
        df.style.format({
            "Score": "{:.1f}",
            "Weight": "{:.0f}%",
            "Contribution": "{:.1f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    # Bar chart of contributions
    fig = px.bar(
        df,
        x="Component",
        y="Contribution",
        title="Component Contributions to Overall Score",
        labels={"Contribution": "Points Contributed"},
        color="Contribution",
        color_continuous_scale="RdYlGn"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Detailed breakdown for each component
    st.markdown("---")
    st.markdown("#### Detailed Component Analysis")

    for comp_name, comp_data in components.items():
        with st.expander(f"{comp_name.replace('_', ' ').title()} - Score: {comp_data['score']:.1f}/100"):
            st.markdown(f"**Weight:** {comp_data['weight']*100:.0f}%")
            st.markdown(f"**Contribution:** {comp_data['contribution']:.1f} points")

            details = comp_data.get("details", {})
            if details:
                st.markdown("**Factors:**")
                for factor_name, factor_data in details.items():
                    # Skip non-dict entries (like "sector": "Technology")
                    if not isinstance(factor_data, dict):
                        st.markdown(f"- **{factor_name.replace('_', ' ').title()}:** {factor_data}")
                        continue

                    value = factor_data.get("value", "N/A")
                    reason = factor_data.get("reason", "No reason provided")
                    st.markdown(f"- **{factor_name.replace('_', ' ').title()}:** {value}")
                    st.caption(reason)


def render_explainability_tab(explainability: Dict):
    """Render explainability with key drivers and risks."""
    if not explainability:
        st.warning("No explainability data available")
        return

    # Key Drivers
    key_drivers = explainability.get("key_drivers", [])
    if key_drivers:
        st.markdown("#### 🚀 Key Drivers")
        st.markdown("Factors supporting the opportunity score:")
        for i, driver in enumerate(key_drivers, 1):
            st.markdown(f"{i}. {driver}")

    st.markdown("---")

    # Risks
    risks = explainability.get("risks", [])
    if risks:
        st.markdown("#### ⚠️ Risks")
        st.markdown("Factors that may limit potential:")
        for i, risk in enumerate(risks, 1):
            st.markdown(f"{i}. {risk}")

    st.markdown("---")

    # Component explanations
    components = explainability.get("components", {})
    if components:
        st.markdown("#### 📋 Component Explanations")
        for comp_name, comp_data in components.items():
            with st.expander(comp_name.replace("_", " ").title()):
                st.json(comp_data)


def render_scenarios_tab(details: Dict):
    """Render scenario analysis with visualization."""
    scenarios = details.get("scenarios", {})
    if not scenarios:
        st.warning("No scenario data available")
        return

    st.markdown("#### Scenario Modeling")
    st.markdown("Expected scores under different market conditions:")

    bull = scenarios.get("bull", 0)
    base = scenarios.get("base", 0)
    bear = scenarios.get("bear", 0)

    # Bar chart
    scenario_df = pd.DataFrame({
        "Scenario": ["🐻 Bear Case", "📊 Base Case", "🐂 Bull Case"],
        "Score": [bear, base, bull],
        "Color": ["#DC2626", "#D97706", "#059669"]
    })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=scenario_df["Scenario"],
        y=scenario_df["Score"],
        marker_color=scenario_df["Color"],
        text=scenario_df["Score"].round(1),
        textposition="outside"
    ))

    fig.update_layout(
        title="Opportunity Score Scenarios",
        yaxis_title="Score",
        yaxis_range=[0, 100],
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Explanation
    st.markdown("---")
    st.markdown("**Scenario Definitions:**")
    st.markdown("""
    - **🐂 Bull Case:** Top quartile performance for each component (optimistic market conditions)
    - **📊 Base Case:** Current score based on latest data
    - **🐻 Bear Case:** Bottom quartile performance for each component (adverse market conditions)
    """)

    # Score range
    score_range = bull - bear
    st.markdown(f"**Score Range:** {score_range:.1f} points ({bear:.1f} - {bull:.1f})")

    if score_range > 30:
        st.info("⚡ High volatility: Score is sensitive to market conditions")
    elif score_range < 15:
        st.info("🛡️ Low volatility: Score is relatively stable across scenarios")


def render_top_opportunities_section():
    """Render top opportunities by category."""
    st.markdown("---")
    st.markdown("### 🏆 Top Opportunities by Category")

    api = get_api_client()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Highest Score")
        result = api.get_top_opportunities(category="highest_score", limit=5, min_confidence=50.0)
        if result and "opportunities" in result:
            for opp in result["opportunities"]:
                st.markdown(f"- **{opp['ticker']}**: {opp['score']:.1f}")

    with col2:
        st.markdown("#### Highest Confidence")
        result = api.get_top_opportunities(category="highest_confidence", limit=5, min_confidence=50.0)
        if result and "opportunities" in result:
            for opp in result["opportunities"]:
                st.markdown(f"- **{opp['ticker']}**: {opp['confidence']:.0f}%")

    with col3:
        st.markdown("#### Best Bull Case")
        result = api.get_top_opportunities(category="best_bull_case", limit=5, min_confidence=50.0)
        if result and "opportunities" in result:
            for opp in result["opportunities"]:
                bull = opp.get("bull_case", 0)
                st.markdown(f"- **{opp['ticker']}**: {bull:.1f}")
