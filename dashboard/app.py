"""
VoltSight BI — Streamlit Dashboard
===================================
4-page interactive dashboard for EV charging infrastructure analysis.

Pages:
  1. Network Overview     — KPI cards, sessions trend, charger type split
  2. Location Intelligence — Map, coverage gaps, demand vs supply
  3. Operations           — Uptime heatmap, fault analysis
  4. Expansion Planner    — Site Priority Score rankings

Run:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VoltSight BI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Data loading ───────────────────────────────────────────────────────────
GOLD_DIR = Path(__file__).parent.parent / "data" / "gold"


@st.cache_data
def load_gold_data() -> dict[str, pd.DataFrame]:
    """Load all Gold layer tables. Returns sample data if gold not found."""
    tables = [
        "dim_charger", "dim_location", "dim_date",
        "fact_sessions", "fact_availability", "gold_priority_scores",
    ]
    data = {}
    for table in tables:
        path = GOLD_DIR / f"{table}.parquet"
        if path.exists():
            data[table] = pd.read_parquet(path)
        else:
            data[table] = _generate_sample(table)
    return data


def _generate_sample(table: str) -> pd.DataFrame:
    """Generate sample data if Gold layer hasn't been built yet."""
    np.random.seed(42)

    if table == "dim_charger":
        n = 500
        types = np.random.choice(
            ["AC_slow", "AC_fast", "DC_rapid", "DC_ultra"], n,
            p=[0.35, 0.35, 0.20, 0.10]
        )
        return pd.DataFrame({
            "charger_id": [f"CHR{i:05d}" for i in range(n)],
            "charger_type": types,
            "power_kw": [{"AC_slow": 7, "AC_fast": 22, "DC_rapid": 50, "DC_ultra": 150}[t] for t in types],
            "postcode": [f"BS{i%99} {i%9}AA" for i in range(n)],
            "local_authority": np.random.choice(["Bristol", "South Gloucestershire"], n),
            "ward_name": [f"Ward_{i%20}" for i in range(n)],
            "site_type": np.random.choice(["retail", "motorway_services", "residential", "workplace"], n),
        })

    elif table == "fact_sessions":
        n = 50000
        charger_ids = [f"CHR{i:05d}" for i in np.random.randint(0, 500, n)]
        months = np.random.randint(1, 13, n)
        return pd.DataFrame({
            "session_id": [f"S{i:08d}" for i in range(n)],
            "charger_id": charger_ids,
            "postcode": [f"BS{i%99} {i%9}AA" for i in range(n)],
            "date_key": [20250000 + m * 100 + np.random.randint(1, 28) for m in months],
            "start_hour": np.random.choice(range(24), n, p=np.array([
                0.3, 0.2, 0.1, 0.1, 0.2, 0.5,
                0.8, 1.5, 1.8, 1.2, 1.0, 1.1,
                1.2, 1.0, 0.9, 1.0, 1.3, 1.8,
                2.0, 1.9, 1.5, 1.1, 0.7, 0.4,
            ]) / 24),
            "duration_min": np.random.randint(10, 240, n),
            "energy_kwh": np.random.uniform(2, 60, n).round(2),
            "revenue_gbp": np.random.uniform(1, 30, n).round(2),
            "status": np.random.choice(["completed", "fault"], n, p=[0.92, 0.08]),
            "fault_type": np.random.choice(
                [None, "network_timeout", "payment_failure", "connector_stuck"], n,
                p=[0.92, 0.03, 0.03, 0.02]
            ),
            "month": months,
        })

    elif table == "fact_availability":
        n = 10000
        return pd.DataFrame({
            "charger_id": [f"CHR{i:05d}" for i in np.random.randint(0, 500, n)],
            "date_key": np.random.randint(20250101, 20251231, n),
            "uptime_pct": np.random.normal(92, 5, n).clip(0, 100).round(1),
            "hours_in_fault": np.random.choice([0, 24], n, p=[0.92, 0.08]),
            "fault_type": np.random.choice(
                [None, "network_timeout", "payment_failure", "connector_stuck", "overheating"], n,
                p=[0.92, 0.02, 0.02, 0.02, 0.02]
            ),
        })

    elif table == "gold_priority_scores":
        n = 99
        return pd.DataFrame({
            "postcode": [f"BS{i} 1AA" for i in range(n)],
            "ward_name": [f"Ward_{i%20}" for i in range(n)],
            "local_authority": np.random.choice(["Bristol", "South Gloucestershire"], n),
            "priority_score": np.random.uniform(20, 90, n).round(1),
            "priority_rank": range(1, n + 1),
            "ev_registrations_nearby": np.random.randint(50, 2000, n),
            "population_density": np.random.randint(500, 8000, n),
            "road_type": np.random.choice(["motorway", "A_road", "B_road", "urban"], n),
            "nearest_competitor_km": np.random.uniform(0.1, 15, n).round(1),
            "latitude": np.random.uniform(51.35, 51.55, n),
            "longitude": np.random.uniform(-2.75, -2.40, n),
            "score_demand": np.random.uniform(0, 1, n),
            "score_supply_gap": np.random.uniform(0, 1, n),
            "score_road_access": np.random.uniform(0, 1, n),
            "score_coverage": np.random.uniform(0, 1, n),
            "score_utilization": np.random.uniform(0, 1, n),
        })

    elif table == "dim_date":
        dates = pd.date_range("2025-01-01", "2025-12-31")
        return pd.DataFrame({
            "date_key": dates.strftime("%Y%m%d").astype(int),
            "date": dates,
            "month": dates.month,
            "month_name": dates.month_name(),
            "is_weekend": dates.dayofweek >= 5,
        })

    return pd.DataFrame()


# ── Colour palette ─────────────────────────────────────────────────────────
COLORS = {
    "primary":   "#00C48C",
    "secondary": "#1E3A5F",
    "warning":   "#FF6B35",
    "neutral":   "#8B9EB7",
    "bg":        "#0F1B2D",
    "card":      "#1A2B3C",
}

CHARGER_COLORS = {
    "AC_slow":  "#4CAF50",
    "AC_fast":  "#2196F3",
    "DC_rapid": "#FF9800",
    "DC_ultra": "#E91E63",
}


# ── Sidebar ─────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/electric-vehicle.png", width=60)
        st.title("VoltSight BI")
        st.caption("EV Infrastructure Analytics")
        st.divider()

        page = st.radio(
            "Navigation",
            ["⚡ Network Overview", "🗺️ Location Intelligence",
             "🔧 Operations", "📍 Expansion Planner"],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption("Data: UK National Chargepoint Registry")
        st.caption("Sessions: 12-month simulation")
        st.caption("© VoltSight BI 2025")

    return page


# ── KPI Card helper ─────────────────────────────────────────────────────────
def kpi_card(col, label: str, value: str, delta: str = "", colour: str = "#00C48C"):
    col.markdown(f"""
    <div style="background:{COLORS['card']};padding:20px;border-radius:10px;
                border-left:4px solid {colour};margin-bottom:10px">
        <div style="color:{COLORS['neutral']};font-size:13px;margin-bottom:4px">{label}</div>
        <div style="color:white;font-size:28px;font-weight:700">{value}</div>
        <div style="color:{colour};font-size:12px">{delta}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Page 1: Network Overview ────────────────────────────────────────────────
def page_network_overview(data: dict):
    st.title("⚡ Network Overview")
    st.caption("UK EV Charging Network — Full Year 2025")
    st.divider()

    sessions = data["fact_sessions"]
    chargers = data["dim_charger"]
    completed = sessions[sessions["status"] == "completed"]

    # KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Total Chargers", f"{len(chargers):,}", "UK Network")
    kpi_card(c2, "Total Sessions", f"{len(completed):,}", "Completed 2025", "#2196F3")
    kpi_card(c3, "Total Revenue", f"£{completed['revenue_gbp'].sum():,.0f}", "Full Year", "#FF9800")
    kpi_card(c4, "Total Energy", f"{completed['energy_kwh'].sum():,.0f} kWh", "Delivered", "#E91E63")

    st.divider()

    col1, col2 = st.columns([2, 1])

    # Sessions trend (by month)
    with col1:
        st.subheader("Monthly Sessions Trend")
        if "month" in completed.columns:
            monthly = completed.groupby("month").size().reset_index(name="sessions")
        else:
            monthly = completed.copy()
            monthly["month"] = (monthly["date_key"] % 10000 // 100)
            monthly = monthly.groupby("month").size().reset_index(name="sessions")

        month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                      7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        monthly["month_name"] = monthly["month"].map(month_names)

        fig = px.area(
            monthly, x="month_name", y="sessions",
            color_discrete_sequence=[COLORS["primary"]],
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="", yaxis_title="Sessions",
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Charger type split
    with col2:
        st.subheader("Charger Types")
        type_counts = chargers["charger_type"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]

        fig2 = px.pie(
            type_counts, values="count", names="type",
            color="type",
            color_discrete_map=CHARGER_COLORS,
            template="plotly_dark",
            hole=0.5,
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Sessions by hour
    st.subheader("Peak Hours (Sessions by Time of Day)")
    hourly = completed.groupby("start_hour").size().reset_index(name="sessions")
    fig3 = px.bar(
        hourly, x="start_hour", y="sessions",
        color="sessions",
        color_continuous_scale=["#1E3A5F", "#00C48C"],
        template="plotly_dark",
        labels={"start_hour": "Hour of Day", "sessions": "Sessions"},
    )
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig3, use_container_width=True)


# ── Page 2: Location Intelligence ──────────────────────────────────────────
def page_location_intelligence(data: dict):
    st.title("🗺️ Location Intelligence")
    st.caption("Charger distribution and coverage gaps across the network")
    st.divider()

    priority = data["gold_priority_scores"]
    chargers = data["dim_charger"]

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Charger Locations & Priority Scores")

        if "latitude" in priority.columns:
            fig = px.scatter_mapbox(
                priority,
                lat="latitude", lon="longitude",
                color="priority_score",
                size="ev_registrations_nearby",
                hover_name="postcode",
                hover_data={"priority_score": True, "ward_name": True},
                color_continuous_scale=["#1E3A5F", "#00C48C", "#FF6B35"],
                mapbox_style="carto-darkmatter",
                zoom=10,
                center={"lat": 51.45, "lon": -2.58},
                template="plotly_dark",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=0, b=0),
                height=450,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Map requires latitude/longitude in priority scores data.")

    with col2:
        st.subheader("Demand vs Supply")
        if "ev_registrations_nearby" in priority.columns:
            fig2 = px.scatter(
                priority,
                x="ev_registrations_nearby",
                y="priority_score",
                color="road_type",
                size="population_density",
                hover_name="postcode",
                template="plotly_dark",
                labels={
                    "ev_registrations_nearby": "EV Registrations Nearby",
                    "priority_score": "Priority Score",
                },
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                height=450,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Local authority breakdown
    st.subheader("Chargers by Local Authority")
    la_counts = chargers.groupby("local_authority").size().reset_index(name="chargers")
    fig3 = px.bar(
        la_counts.sort_values("chargers", ascending=True),
        x="chargers", y="local_authority",
        orientation="h",
        color="chargers",
        color_continuous_scale=["#1E3A5F", "#00C48C"],
        template="plotly_dark",
    )
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
    )
    st.plotly_chart(fig3, use_container_width=True)


# ── Page 3: Operations ──────────────────────────────────────────────────────
def page_operations(data: dict):
    st.title("🔧 Operations & Reliability")
    st.caption("Uptime monitoring and fault analysis across the network")
    st.divider()

    availability = data["fact_availability"]
    sessions = data["fact_sessions"]

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    avg_uptime = availability["uptime_pct"].mean()
    fault_sessions = sessions[sessions["status"] == "fault"]

    kpi_card(c1, "Avg Network Uptime", f"{avg_uptime:.1f}%",
             "Target: 95%" , "#00C48C" if avg_uptime >= 95 else "#FF6B35")
    kpi_card(c2, "Chargers Below 95%",
             f"{(availability.groupby('charger_id')['uptime_pct'].mean() < 95).sum()}",
             "Need attention", "#FF6B35")
    kpi_card(c3, "Fault Incidents", f"{len(fault_sessions):,}", "Total 2025", "#FF9800")
    kpi_card(c4, "Most Common Fault",
             fault_sessions["fault_type"].mode()[0] if len(fault_sessions) > 0 else "N/A",
             "Primary cause", "#8B9EB7")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fault Type Breakdown")
        fault_counts = fault_sessions["fault_type"].value_counts().reset_index()
        fault_counts.columns = ["fault_type", "count"]
        fault_counts = fault_counts[fault_counts["fault_type"].notna()]

        fig = px.bar(
            fault_counts,
            x="count", y="fault_type",
            orientation="h",
            color="count",
            color_continuous_scale=["#1E3A5F", "#FF6B35"],
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Uptime Distribution")
        fig2 = px.histogram(
            availability,
            x="uptime_pct",
            nbins=20,
            color_discrete_sequence=[COLORS["primary"]],
            template="plotly_dark",
            labels={"uptime_pct": "Uptime %"},
        )
        fig2.add_vline(x=95, line_dash="dash", line_color="#FF6B35",
                       annotation_text="95% target")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig2, use_container_width=True)


# ── Page 4: Expansion Planner ───────────────────────────────────────────────
def page_expansion_planner(data: dict):
    st.title("📍 Expansion Planner")
    st.caption("Site Priority Score — Where to install the next charger")
    st.divider()

    priority = data["gold_priority_scores"].copy()

    # Weight sliders
    st.subheader("⚙️ Adjust Priority Weights")
    st.caption("Change the weights to reflect your business priorities")

    col1, col2, col3, col4, col5 = st.columns(5)
    w_demand   = col1.slider("Demand",        0, 100, 30, 5) / 100
    w_supply   = col2.slider("Supply Gap",    0, 100, 25, 5) / 100
    w_road     = col3.slider("Road Access",   0, 100, 20, 5) / 100
    w_coverage = col4.slider("Coverage",      0, 100, 15, 5) / 100
    w_util     = col5.slider("Utilization",   0, 100, 10, 5) / 100

    total_weight = w_demand + w_supply + w_road + w_coverage + w_util
    if abs(total_weight - 1.0) > 0.01:
        st.warning(f"⚠️ Weights sum to {total_weight:.0%} (should be 100%). Normalising automatically.")
        norm = total_weight
        w_demand   /= norm
        w_supply   /= norm
        w_road     /= norm
        w_coverage /= norm
        w_util     /= norm

    # Recalculate score with custom weights
    if all(c in priority.columns for c in ["score_demand", "score_supply_gap"]):
        priority["custom_score"] = round((
            priority["score_demand"]      * w_demand
            + priority["score_supply_gap"]  * w_supply
            + priority["score_road_access"] * w_road
            + priority["score_coverage"]    * w_coverage
            + priority["score_utilization"] * w_util
        ) * 100, 1)
        priority = priority.sort_values("custom_score", ascending=False)
        score_col = "custom_score"
    else:
        priority = priority.sort_values("priority_score", ascending=False)
        score_col = "priority_score"

    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🏆 Top 10 Locations for New Charger")
        top10 = priority.head(10)[[
            "postcode", "ward_name", "local_authority",
            score_col, "ev_registrations_nearby",
            "road_type", "nearest_competitor_km"
        ]].copy()
        top10.index = range(1, 11)
        top10.columns = [
            "Postcode", "Ward", "Local Authority",
            "Priority Score", "EV Registrations",
            "Road Type", "Nearest Competitor (km)"
        ]
        st.dataframe(
            top10,
            use_container_width=True,
        )

    with col2:
        st.subheader("Score Breakdown")
        top1 = priority.iloc[0]
        if "score_demand" in top1.index:
            breakdown = pd.DataFrame({
                "Component": ["Demand", "Supply Gap", "Road Access",
                              "Coverage", "Utilization"],
                "Score": [
                    round(top1.get("score_demand", 0) * 100, 1),
                    round(top1.get("score_supply_gap", 0) * 100, 1),
                    round(top1.get("score_road_access", 0) * 100, 1),
                    round(top1.get("score_coverage", 0) * 100, 1),
                    round(top1.get("score_utilization", 0) * 100, 1),
                ]
            })
            fig = px.bar(
                breakdown, x="Score", y="Component",
                orientation="h",
                color="Score",
                color_continuous_scale=["#1E3A5F", "#00C48C"],
                template="plotly_dark",
                title=f"#{1}: {top1['postcode']}",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, margin=dict(l=0, r=0, t=40, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

    # Full ranked table
    st.subheader("Full Priority Rankings")
    display_df = priority[[
        "postcode", "ward_name", score_col, "road_type", "ev_registrations_nearby"
    ]].copy()
    display_df.index = range(1, len(display_df) + 1)
    display_df.columns = ["Postcode", "Ward", "Score", "Road Type", "EV Registrations"]
    st.dataframe(display_df, use_container_width=True, height=300)


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    data = load_gold_data()
    page = render_sidebar()

    if page == "⚡ Network Overview":
        page_network_overview(data)
    elif page == "🗺️ Location Intelligence":
        page_location_intelligence(data)
    elif page == "🔧 Operations":
        page_operations(data)
    elif page == "📍 Expansion Planner":
        page_expansion_planner(data)


if __name__ == "__main__":
    main()
