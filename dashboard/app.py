"""VoltSight BI — World-Class Professional Dashboard"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="VoltSight BI", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

* { font-family: 'Inter', sans-serif !important; }

/* ── BACKGROUND ── */
.stApp { background: #060d1a !important; }
.stApp > div { background: #060d1a !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1628 0%, #0d1f38 100%) !important;
    border-right: 1px solid rgba(0,196,140,0.15) !important;
    width: 260px !important;
}
section[data-testid="stSidebar"] * { color: #e2eaf4 !important; }
section[data-testid="stSidebar"] .stRadio label {
    color: #c8d8ea !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 4px 0 !important;
}
section[data-testid="stSidebar"] p { color: #e2eaf4 !important; }
section[data-testid="stSidebar"] span { color: #e2eaf4 !important; }
section[data-testid="stSidebar"] div { color: #e2eaf4 !important; }
[data-testid="stRadio"] label span { color: #ffffff !important; font-size:14px !important; }
[data-testid="stRadio"] div[role="radiogroup"] { gap: 4px !important; }
[data-testid="stMarkdownContainer"] p { color: #e2eaf4 !important; }

/* Filter labels */
[data-testid="stMultiSelect"] label { color: #7a9cc4 !important; font-size:11px !important; font-weight:600 !important; text-transform:uppercase !important; letter-spacing:1px !important; }
[data-baseweb="tag"] { background: rgba(0,196,140,0.2) !important; border: 1px solid rgba(0,196,140,0.4) !important; border-radius: 6px !important; }
[data-baseweb="tag"] span { color: #00c48c !important; font-weight: 600 !important; }
[data-baseweb="select"] { background: rgba(255,255,255,0.04) !important; border-color: rgba(255,255,255,0.1) !important; border-radius: 8px !important; }

/* ── HIDE CLUTTER ── */
header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, .stDeployButton { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a1628; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 2px; }

/* ── KPI CARDS ── */
.kpi { background: linear-gradient(145deg, #0d1f38 0%, #112540 100%); border: 1px solid rgba(255,255,255,0.07); border-radius: 20px; padding: 22px 24px; position: relative; overflow: hidden; transition: all 0.3s ease; }
.kpi:hover { transform: translateY(-3px); box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
.kpi-bar { position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: 20px 20px 0 0; }
.kpi-icon { font-size: 28px; margin-bottom: 10px; display: block; }
.kpi-lbl { color: #5a7a9a; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px; }
.kpi-val { color: #ffffff; font-size: 28px; font-weight: 800; line-height: 1; margin-bottom: 6px; letter-spacing: -0.5px; }
.kpi-sub { color: #3a5a7a; font-size: 12px; font-weight: 500; }

/* ── INSIGHT CARD ── */
.insight { background: linear-gradient(135deg, rgba(0,196,140,0.08), rgba(0,196,140,0.03)); border: 1px solid rgba(0,196,140,0.25); border-left: 3px solid #00c48c; border-radius: 12px; padding: 16px 20px; margin: 16px 0; }
.insight-t { color: #00c48c; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
.insight-b { color: #c8d8ea; font-size: 13px; line-height: 1.7; }

/* ── PAGE HEADER ── */
.pg-title { font-size: 32px; font-weight: 900; color: #ffffff; letter-spacing: -1px; margin-bottom: 2px; }
.pg-sub { color: #3a5a7a; font-size: 13px; font-weight: 500; margin-bottom: 24px; }

/* ── SECTION ── */
.sec { color: #e2eaf4; font-size: 16px; font-weight: 700; margin: 20px 0 12px; display: flex; align-items: center; gap: 8px; }
.sec::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(30,58,95,0.8), transparent); margin-left: 8px; }

/* ── DATAFRAME ── */
.stDataFrame { border-radius: 16px !important; overflow: hidden !important; }
[data-testid="stDataFrame"] { background: #0d1f38 !important; border-radius: 16px !important; }

/* ══ NUCLEAR SIDEBAR FIX ══ */
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0a1628,#0d1f38) !important; }

/* ALL text in sidebar = white */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {
    color: #e8f0fe !important;
}

/* Radio buttons */
section[data-testid="stSidebar"] [data-testid="stRadio"] label { color: #e8f0fe !important; font-size: 14px !important; font-weight: 500 !important; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label p { color: #e8f0fe !important; }
section[data-testid="stSidebar"] [role="radiogroup"] label { color: #e8f0fe !important; }

/* Multiselect tags */
[data-baseweb="tag"] { background: rgba(0,196,140,0.15) !important; border: 1px solid rgba(0,196,140,0.3) !important; }
[data-baseweb="tag"] span, [data-baseweb="tag"] * { color: #00e6a8 !important; font-weight: 600 !important; }

/* Multiselect dropdown */
[data-baseweb="select"] > div { background: rgba(13,31,56,0.9) !important; border-color: rgba(30,58,95,0.8) !important; }
[data-baseweb="select"] span { color: #e8f0fe !important; }
[data-baseweb="menu"] { background: #0d1f38 !important; }
[data-baseweb="option"] { background: #0d1f38 !important; color: #e8f0fe !important; }
[data-baseweb="option"]:hover { background: rgba(0,196,140,0.15) !important; }

/* Filter labels */
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] [data-testid="stMultiSelect"] label { 
    color: #4a8aaa !important; 
    font-size: 11px !important; 
    font-weight: 700 !important; 
    text-transform: uppercase !important; 
    letter-spacing: 1px !important; 
}

/* Remove collapse button weirdness */
[data-testid="collapsedControl"] { color: #e8f0fe !important; }
button[kind="header"] { color: #e8f0fe !important; background: transparent !important; }

</style>
""", unsafe_allow_html=True)

GOLD_DIR = Path(__file__).parent.parent / "data" / "gold"
PALETTE = ["#00c48c","#2196f3","#ff9800","#e91e63","#9c27b0","#00bcd4","#ff5722"]
CT_C = {"AC_slow":"#4CAF50","AC_fast":"#2196F3","DC_rapid":"#FF9800","DC_ultra":"#E91E63"}
G = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,22,40,0.6)",
         font=dict(color="#8aaccc", family="Inter, sans-serif", size=12),
         margin=dict(l=0, r=0, t=30, b=0))

AX = dict(gridcolor="rgba(30,58,95,0.5)", linecolor="rgba(30,58,95,0.5)", tickfont=dict(color="#8aaccc"))

def fl(fig, h=300, xax=None, yax=None):
    xaxis = {**AX, **(xax or {})}
    yaxis = {**AX, **(yax or {})}
    fig.update_layout(**G, height=h, xaxis=xaxis, yaxis=yaxis)
    return fig

@st.cache_data
def load():
    tbls = ["dim_charger","dim_location","dim_date","fact_sessions","fact_availability","gold_priority_scores"]
    d = {}
    for t in tbls:
        p = GOLD_DIR / f"{t}.parquet"
        d[t] = pd.read_parquet(p) if p.exists() else _fake(t)
    s = d["fact_sessions"]
    if "month" not in s.columns:
        s["month"] = s["date_key"] % 10000 // 100
    return d

def _fake(t):
    np.random.seed(42)
    if t == "dim_charger":
        n=500; tp=np.random.choice(["AC_slow","AC_fast","DC_rapid","DC_ultra"],n,p=[.35,.35,.20,.10])
        return pd.DataFrame({"charger_id":[f"CHR{i:05d}" for i in range(n)],"charger_type":tp,
            "power_kw":[{"AC_slow":7,"AC_fast":22,"DC_rapid":50,"DC_ultra":150}[x] for x in tp],
            "postcode":[f"BS{i%99} {i%9}AA" for i in range(n)],
            "local_authority":np.random.choice(["Bristol","South Gloucestershire","Bath & NE Somerset"],n),
            "site_type":np.random.choice(["Retail","Motorway Services","Residential","Workplace","Leisure"],n)})
    if t == "fact_sessions":
        n=60000; m=np.random.randint(1,13,n)
        hw=np.array([.3,.2,.1,.1,.2,.5,.8,1.5,1.8,1.2,1,1.1,1.2,1,.9,1,1.3,1.8,2,1.9,1.5,1.1,.7,.4])
        return pd.DataFrame({"session_id":[f"S{i:08d}" for i in range(n)],
            "charger_id":[f"CHR{i:05d}" for i in np.random.randint(0,500,n)],
            "postcode":[f"BS{i%99} {i%9}AA" for i in range(n)],
            "date_key":[20250000+x*100+np.random.randint(1,28) for x in m],
            "start_hour":np.random.choice(24,n,p=hw/hw.sum()),
            "duration_min":np.random.randint(10,240,n),
            "energy_kwh":np.round(np.random.uniform(2,60,n),2),
            "revenue_gbp":np.round(np.random.uniform(1,30,n),2),
            "status":np.random.choice(["completed","fault"],n,p=[.92,.08]),
            "fault_type":np.random.choice([None,"network_timeout","payment_failure","connector_stuck","overheating","power_surge"],n,p=[.92,.016,.016,.016,.016,.016]),
            "month":m})
    if t == "fact_availability":
        n=10000
        return pd.DataFrame({"charger_id":[f"CHR{i:05d}" for i in np.random.randint(0,500,n)],
            "date_key":np.random.randint(20250101,20251231,n),
            "uptime_pct":np.clip(np.random.normal(92,5,n),0,100).round(1),
            "fault_type":np.random.choice([None,"network_timeout","payment_failure","connector_stuck","overheating","power_surge"],n,p=[.92,.016,.016,.016,.016,.016])})
    if t == "gold_priority_scores":
        n=99; sc=np.round(np.random.uniform(20,90,n),1)
        return pd.DataFrame({"postcode":[f"BS{i} 1AA" for i in range(n)],
            "ward_name":[f"Ward_{i%20}" for i in range(n)],
            "local_authority":np.random.choice(["Bristol","South Gloucestershire","Bath & NE Somerset"],n),
            "priority_score":sc,"priority_rank":pd.Series(sc).rank(ascending=False).astype(int).values,
            "ev_registrations_nearby":np.random.randint(50,2000,n),
            "population_density":np.random.randint(500,8000,n),
            "road_type":np.random.choice(["Motorway","A Road","B Road","Urban"],n),
            "nearest_competitor_km":np.round(np.random.uniform(.1,15,n),1),
            "latitude":np.random.uniform(51.35,51.55,n),
            "longitude":np.random.uniform(-2.75,-2.40,n),
            "score_demand":np.random.uniform(0,1,n),"score_supply_gap":np.random.uniform(0,1,n),
            "score_road_access":np.random.uniform(0,1,n),"score_coverage":np.random.uniform(0,1,n),
            "score_utilization":np.random.uniform(0,1,n)})
    return pd.DataFrame()

def kpi(col, icon, lbl, val, sub, color):
    col.markdown(f"""
    <div class="kpi">
        <div class="kpi-bar" style="background:{color}"></div>
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-lbl">{lbl}</div>
        <div class="kpi-val">{val}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def ins(body, title="💡 Insight"):
    st.markdown(f'<div class="insight"><div class="insight-t">{title}</div><div class="insight-b">{body}</div></div>', unsafe_allow_html=True)

def sec(t):
    st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)



def yax2(color):
    return dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)", linecolor="rgba(0,0,0,0)", tickfont=dict(color=color), color=color)

def main():
    data = load()

    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:28px 0 20px">
            <div style="font-size:44px;filter:drop-shadow(0 0 20px rgba(0,196,140,0.6))">⚡</div>
            <div style="color:#ffffff;font-size:20px;font-weight:900;letter-spacing:-0.5px;margin-top:8px">VoltSight BI</div>
            <div style="color:#3a6a8a;font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;margin-top:4px">EV Infrastructure Analytics</div>
        </div>
        <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(0,196,140,0.3),transparent);margin:0 16px 20px"></div>
        """, unsafe_allow_html=True)

        page = st.radio("", [
            "📊  Network Overview",
            "🗺️  Location Intelligence",
            "🔧  Operations",
            "📍  Expansion Planner",
        ], label_visibility="collapsed")

        st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(30,58,95,0.6),transparent);margin:16px 0"></div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#3a6a8a;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;padding:0 4px">Filters</div>', unsafe_allow_html=True)

        ch = data["dim_charger"]
        las = sorted(ch["local_authority"].dropna().unique())
        sel_la = st.multiselect("Local Authority", las, default=las)
        tps = sorted(ch["charger_type"].unique())
        sel_tp = st.multiselect("Charger Type", tps, default=tps)
        mnths = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        sel_m = st.multiselect("Month", mnths, default=mnths)
        m_nums = [i+1 for i,m in enumerate(mnths) if m in sel_m]

        st.markdown("""
        <div style="margin-top:24px;padding:12px 16px;background:rgba(0,196,140,0.06);border-radius:10px;border:1px solid rgba(0,196,140,0.12)">
            <div style="color:#3a6a8a;font-size:10px;line-height:1.8">
                📋 Data: UK National Chargepoint Registry<br>
                🔢 Sessions: 12-month simulation (2025)<br>
                🏛️ © VoltSight BI 2025
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Filter ──────────────────────────────────────────────────────────────
    chargers = ch.copy()
    if sel_la: chargers = chargers[chargers["local_authority"].isin(sel_la)]
    if sel_tp: chargers = chargers[chargers["charger_type"].isin(sel_tp)]
    cids = set(chargers["charger_id"])
    sess = data["fact_sessions"].copy()
    sess = sess[sess["charger_id"].isin(cids)]
    if m_nums: sess = sess[sess["month"].isin(m_nums)]
    avail = data["fact_availability"].copy()
    avail = avail[avail["charger_id"].isin(cids)]
    comp = sess[sess["status"]=="completed"]
    faults = sess[sess["status"]=="fault"]
    mn = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 1: NETWORK OVERVIEW
    # ══════════════════════════════════════════════════════════════════════
    if "Network Overview" in page:
        st.markdown('<div class="pg-title">Network Overview</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">UK EV Charging Network · Full Year 2025 · Live Performance Metrics</div>', unsafe_allow_html=True)

        c1,c2,c3,c4 = st.columns(4)
        kpi(c1,"🔌","Total Chargers",f"{len(chargers):,}","Active on UK network","linear-gradient(90deg,#00c48c,#00e6a8)")
        kpi(c2,"⚡","Sessions Completed",f"{len(comp):,}","Full year 2025","linear-gradient(90deg,#2196f3,#64b5f6)")
        kpi(c3,"💷","Total Revenue",f"£{comp['revenue_gbp'].sum():,.0f}","Generated in 2025","linear-gradient(90deg,#ff9800,#ffb74d)")
        kpi(c4,"⚡","Energy Delivered",f"{comp['energy_kwh'].sum()/1000:,.0f} MWh",f"Avg {comp['duration_min'].mean():.0f} min/session","linear-gradient(90deg,#e91e63,#f48fb1)")

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns([3,2])

        with c1:
            sec("📈 Monthly Performance")
            mo = comp.groupby("month").agg(sessions=("session_id","count"),revenue=("revenue_gbp","sum")).reset_index()
            mo["mn"] = mo["month"].map(mn)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=mo["mn"],y=mo["sessions"],
                fill="tozeroy", fillcolor="rgba(0,196,140,0.1)",
                line=dict(color="#00c48c",width=2.5,shape="spline"),
                mode="lines+markers",marker=dict(size=7,color="#00c48c",line=dict(width=2,color="#0a1628")),
                name="Sessions",hovertemplate="<b>%{x}</b><br>Sessions: %{y:,}<extra></extra>"))
            fig.add_trace(go.Bar(x=mo["mn"],y=mo["revenue"],
                marker=dict(color="rgba(33,150,243,0.2)",line=dict(color="rgba(33,150,243,0.4)",width=1)),
                yaxis="y2",name="Revenue £",
                hovertemplate="<b>%{x}</b><br>Revenue: £%{y:,.0f}<extra></extra>"))
            fl(fig, 280)
                fig.update_layout(
                yaxis2=yax2("#2196f3"),
                legend=dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)",font=dict(color="#8aaccc",size=11)),
                hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            sec("🔌 Network Composition")
            tc = chargers["charger_type"].value_counts().reset_index()
            tc.columns = ["type","count"]
            fig2 = go.Figure(go.Pie(
                labels=tc["type"],values=tc["count"],hole=0.65,
                marker=dict(colors=[CT_C.get(t,"#888") for t in tc["type"]],
                            line=dict(color="#060d1a",width=3)),
                textinfo="percent",textfont=dict(color="white",size=11),
                hovertemplate="<b>%{label}</b><br>%{value:,} chargers (%{percent})<extra></extra>"))
            fl(fig2, 280)
                fig2.update_layout(
                legend=dict(orientation="h",y=-0.2,font=dict(color="#8aaccc",size=10)),
                annotations=[dict(text=f"<b style='font-size:22px'>{len(chargers)}</b><br><span style='font-size:10px'>chargers</span>",
                    x=0.5,y=0.5,font=dict(size=16,color="white"),showarrow=False)])
            st.plotly_chart(fig2, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            sec("⏰ Demand by Hour of Day")
            hr = comp.groupby("start_hour").size().reset_index(name="n")
            peak = [7,8,17,18,19]
            fig3 = go.Figure(go.Bar(
                x=hr["start_hour"],y=hr["n"],
                marker=dict(
                    color=["#00c48c" if h in peak else "rgba(33,58,95,0.7)" for h in hr["start_hour"]],
                    line=dict(color="rgba(0,0,0,0)",width=0)),
                hovertemplate="<b>%{x}:00</b><br>Sessions: %{y:,}<extra></extra>"))
            fl(fig3, 240, xax=dict(tickmode="linear",tick0=0,dtick=3))
            fig3.update_layout(bargap=0.15)
            st.plotly_chart(fig3, use_container_width=True)

        with c4:
            sec("🏪 Revenue by Site Type")
            if "site_type" in chargers.columns:
                mg = sess.merge(chargers[["charger_id","site_type"]],on="charger_id",how="left")
                st_s = mg[mg["status"]=="completed"].groupby("site_type").agg(rev=("revenue_gbp","sum")).reset_index().sort_values("rev")
                fig4 = go.Figure(go.Bar(
                    x=st_s["rev"],y=st_s["site_type"],orientation="h",
                    marker=dict(color=st_s["rev"],
                        colorscale=[[0,"rgba(33,58,95,0.5)"],[1,"#00c48c"]],
                        line=dict(color="rgba(0,0,0,0)")),
                    text=[f"£{v:,.0f}" for v in st_s["rev"]],
                    textposition="outside",textfont=dict(color="#8aaccc",size=11),
                    hovertemplate="<b>%{y}</b><br>£%{x:,.0f}<extra></extra>"))
                fl(fig4, 240)
                fig4.update_layout(xaxis=dict(showgrid=False,showticklabels=False))
                st.plotly_chart(fig4, use_container_width=True)

        ph = comp.groupby("start_hour").size().idxmax()
        top_type = chargers["charger_type"].value_counts().index[0]
        ins(f"Peak charging demand occurs at <b>{ph}:00</b> — align rapid charger deployment to morning and evening commuter windows. "
            f"<b>{top_type.replace('_',' ').title()}</b> units dominate at <b>{chargers['charger_type'].value_counts().iloc[0]}</b> sites. "
            f"Network generated <b>£{comp['revenue_gbp'].sum():,.0f}</b> in 2025 — a strong commercial signal for expansion.", "💡 Network Intelligence")

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 2: LOCATION INTELLIGENCE
    # ══════════════════════════════════════════════════════════════════════
    elif "Location Intelligence" in page:
        st.markdown('<div class="pg-title">Location Intelligence</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Geographic distribution · Coverage gaps · Demand signals across UK</div>', unsafe_allow_html=True)

        pr = data["gold_priority_scores"]
        las2 = chargers["local_authority"].value_counts()
        c1,c2,c3 = st.columns(3)
        kpi(c1,"🏛️","Areas Covered",str(chargers["local_authority"].nunique()),"Local authorities","linear-gradient(90deg,#00c48c,#00e6a8)")
        kpi(c2,"📍","Busiest Area",str(las2.index[0]) if len(las2) else "N/A",f"{las2.iloc[0]:,} chargers" if len(las2) else "","linear-gradient(90deg,#2196f3,#64b5f6)")
        kpi(c3,"🚗","Avg EV Density",f"{int(pr['ev_registrations_nearby'].mean()):,}","EV registrations per zone","linear-gradient(90deg,#ff9800,#ffb74d)")

        st.markdown("<br>",unsafe_allow_html=True)
        c1,c2 = st.columns([3,2])

        with c1:
            sec("🗺️ Site Priority Heatmap")
            if "latitude" in pr.columns:
                fig = px.scatter_mapbox(pr.sort_values("priority_score"),
                    lat="latitude",lon="longitude",color="priority_score",
                    size="ev_registrations_nearby",hover_name="postcode",
                    hover_data={"priority_score":":.1f","ward_name":True,"road_type":True,"latitude":False,"longitude":False},
                    color_continuous_scale=[[0,"#0d1f38"],[0.4,"#1565c0"],[0.7,"#0097a7"],[1,"#00c48c"]],
                    size_max=20,mapbox_style="carto-darkmatter",zoom=9.5,
                    center={"lat":51.45,"lon":-2.58},
                    labels={"priority_score":"Priority Score"})
                fl(fig, 420)
                fig.update_layout(
                    coloraxis_colorbar=dict(title=dict(text="Score",font=dict(color="#8aaccc")),
                        tickfont=dict(color="#8aaccc"),bgcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            sec("📊 EV Demand vs Priority")
            fig2 = px.scatter(pr,x="ev_registrations_nearby",y="priority_score",
                color="road_type",size="population_density",hover_name="postcode",
                color_discrete_sequence=PALETTE,
                labels={"ev_registrations_nearby":"EV Registrations Nearby","priority_score":"Priority Score","road_type":"Road Type"})
            fl(fig2, 420)
                fig2.update_layout(legend=dict(orientation="h",y=-0.18,font=dict(color="#8aaccc",size=10),bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig2, use_container_width=True)

        sec("🏛️ Performance by Local Authority")
        la_s = comp.merge(chargers[["charger_id","local_authority"]],on="charger_id",how="left")
        la_g = la_s.groupby("local_authority").agg(sessions=("session_id","count"),revenue=("revenue_gbp","sum")).reset_index().sort_values("revenue",ascending=False)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Sessions",x=la_g["local_authority"],y=la_g["sessions"],
            marker=dict(color="rgba(0,196,140,0.7)",line=dict(color="rgba(0,0,0,0)"))))
        fig3.add_trace(go.Scatter(name="Revenue £",x=la_g["local_authority"],y=la_g["revenue"],
            mode="lines+markers",line=dict(color="#ff9800",width=2.5,shape="spline"),
            marker=dict(size=9,color="#ff9800",line=dict(width=2,color="#060d1a")),yaxis="y2"))
        fl(fig3, 260)
                fig3.update_layout(yaxis2=yax2("#ff9800"),
            legend=dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)",font=dict(color="#8aaccc")))
        st.plotly_chart(fig3, use_container_width=True)
        if len(la_g):
            ins(f"<b>{la_g.iloc[0]['local_authority']}</b> leads performance with <b>£{la_g.iloc[0]['revenue']:,.0f}</b> revenue from <b>{la_g.iloc[0]['sessions']:,}</b> sessions. "
                f"Concentrating infrastructure investment in high-performing zones yields the strongest commercial returns.", "📍 Location Insight")

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 3: OPERATIONS
    # ══════════════════════════════════════════════════════════════════════
    elif "Operations" in page:
        st.markdown('<div class="pg-title">Operations & Reliability</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Network health monitoring · Fault diagnostics · SLA performance tracking</div>', unsafe_allow_html=True)

        avg_up = avail["uptime_pct"].mean()
        b95 = (avail.groupby("charger_id")["uptime_pct"].mean() < 95).sum()
        fm = faults["fault_type"].dropna().mode()
        sla_color = "linear-gradient(90deg,#00c48c,#00e6a8)" if avg_up>=95 else "linear-gradient(90deg,#ff9800,#ffb74d)"

        c1,c2,c3,c4 = st.columns(4)
        kpi(c1,"📡","Network Uptime",f"{avg_up:.1f}%","Target: 95% SLA",sla_color)
        kpi(c2,"⚠️","Below SLA",str(int(b95)),"Chargers need attention","linear-gradient(90deg,#e91e63,#f48fb1)")
        kpi(c3,"🔴","Fault Incidents",f"{len(faults):,}","Total recorded 2025","linear-gradient(90deg,#ff5722,#ff8a65)")
        kpi(c4,"🛠️","Primary Fault",fm[0].replace("_"," ").title() if len(fm) else "N/A","Most common failure","linear-gradient(90deg,#9c27b0,#ce93d8)")

        st.markdown("<br>",unsafe_allow_html=True)
        c1,c2 = st.columns(2)

        with c1:
            sec("🔴 Fault Type Analysis")
            fc = faults["fault_type"].dropna().value_counts().reset_index()
            fc.columns = ["type","count"]
            fc["label"] = fc["type"].str.replace("_"," ").str.title()
            fig = go.Figure(go.Bar(
                x=fc["count"],y=fc["label"],orientation="h",
                marker=dict(color=fc["count"],
                    colorscale=[[0,"rgba(33,58,95,0.5)"],[0.5,"rgba(255,152,0,0.7)"],[1,"rgba(229,57,53,0.8)"]],
                    line=dict(color="rgba(0,0,0,0)")),
                text=[f"  {v:,}" for v in fc["count"]],
                textposition="outside",textfont=dict(color="#8aaccc",size=11),
                hovertemplate="<b>%{y}</b><br>Incidents: %{x:,}<extra></extra>"))
            fl(fig, 280, xax=dict(showgrid=False,showticklabels=False))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            sec("📊 Uptime Distribution")
            fig2 = go.Figure()
            fig2.add_trace(go.Histogram(x=avail["uptime_pct"],nbinsx=25,
                marker=dict(color="rgba(33,150,243,0.6)",line=dict(color="rgba(33,150,243,0.3)",width=1)),
                hovertemplate="Uptime: %{x:.0f}%<br>Count: %{y:,}<extra></extra>"))
            fig2.add_vline(x=95,line_dash="dash",line_color="#00c48c",line_width=1.5,
                annotation=dict(text="95% SLA",font=dict(color="#00c48c",size=11),bgcolor="rgba(0,0,0,0)"))
            fig2.add_vline(x=avg_up,line_dash="dot",line_color="#ff9800",line_width=1.5,
                annotation=dict(text=f"Avg {avg_up:.1f}%",font=dict(color="#ff9800",size=11),bgcolor="rgba(0,0,0,0)"))
            fl(fig2, 280)
            st.plotly_chart(fig2, use_container_width=True)

        sec("📅 Monthly Fault Trend")
        mf = faults.groupby("month").size().reset_index(name="faults")
        mc_d = comp.groupby("month").size().reset_index(name="completed")
        mt = mf.merge(mc_d,on="month",how="outer").fillna(0)
        mt["fault_rate"] = (mt["faults"]/(mt["faults"]+mt["completed"])*100).round(1)
        mt["mn"] = mt["month"].map(mn)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=mt["mn"],y=mt["faults"],name="Faults",
            marker=dict(color="rgba(229,57,53,0.5)",line=dict(color="rgba(229,57,53,0.3)",width=1))))
        fig3.add_trace(go.Scatter(x=mt["mn"],y=mt["fault_rate"],name="Fault Rate %",
            line=dict(color="#ff9800",width=2,shape="spline"),
            marker=dict(size=7,color="#ff9800"),yaxis="y2",
            hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>"))
        fl(fig3, 250)
                fig3.update_layout(yaxis2=yax2("#ff9800"),
            legend=dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)",font=dict(color="#8aaccc")))
        st.plotly_chart(fig3, use_container_width=True)
        ins(f"Network uptime <b>{avg_up:.1f}%</b> vs 95% SLA target. <b>{int(b95)} chargers</b> below threshold — prioritise for maintenance. "
            f"Leading fault: <b>{fm[0].replace('_',' ').title() if len(fm) else 'N/A'}</b>. Predictive maintenance schedule recommended.", "🔧 Operations Insight")

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 4: EXPANSION PLANNER
    # ══════════════════════════════════════════════════════════════════════
    elif "Expansion Planner" in page:
        st.markdown('<div class="pg-title">Expansion Planner</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">AI-powered site ranking · Prioritise where to install the next EV charger</div>', unsafe_allow_html=True)

        pr = data["gold_priority_scores"].copy()
        sec("⚙️ Priority Weight Configuration")
        st.markdown('<div style="color:#3a6a8a;font-size:12px;margin:-8px 0 16px">Adjust weights to reflect your organisation\'s strategic priorities. Rankings update in real time.</div>', unsafe_allow_html=True)

        c1,c2,c3,c4,c5 = st.columns(5)
        w1=c1.slider("🚗 EV Demand",0,100,30,5,help="Weight given to EV registration density")
        w2=c2.slider("📉 Supply Gap",0,100,25,5,help="Under-served areas with few chargers")
        w3=c3.slider("🛣️ Road Access",0,100,20,5,help="Proximity to A-roads and motorways")
        w4=c4.slider("📡 Coverage",0,100,15,5,help="Distance from nearest competitor")
        w5=c5.slider("⚡ Utilisation",0,100,10,5,help="How busy existing nearby chargers are")

        tot = max(w1+w2+w3+w4+w5,1)
        st.markdown(f'<div style="color:#3a6a8a;font-size:11px;text-align:right;margin-top:-8px">Weight total: <b style="color:{"#00c48c" if abs(tot-100)<5 else "#ff9800"}">{tot}%</b></div>', unsafe_allow_html=True)

        if all(c in pr.columns for c in ["score_demand","score_supply_gap"]):
            pr["score"] = ((pr["score_demand"]*w1+pr["score_supply_gap"]*w2+pr["score_road_access"]*w3+pr["score_coverage"]*w4+pr["score_utilization"]*w5)/tot*100).round(1)
        else:
            pr["score"] = pr["priority_score"]
        pr = pr.sort_values("score",ascending=False).reset_index(drop=True)

        st.markdown("<br>",unsafe_allow_html=True)
        c1,c2 = st.columns([3,2])

        with c1:
            sec("🏆 Top Expansion Sites")
            t10 = pr.head(10).copy()
            t10.index = range(1,11)
            display = pd.DataFrame({
                "Rank": [f"#{i}" for i in range(1,11)],
                "Postcode": t10["postcode"].values,
                "Ward": t10["ward_name"].values,
                "Authority": t10["local_authority"].values,
                "Score": [f"{s:.1f}/100" for s in t10["score"].values],
                "EV Density": [f"{v:,}" for v in t10["ev_registrations_nearby"].values],
                "Road": t10["road_type"].values,
                "Gap (km)": [f"{v:.1f}" for v in t10["nearest_competitor_km"].values],
            })
            display.index = range(1,11)
            st.dataframe(display, use_container_width=True, height=370)

        with c2:
            sec(f"📊 Component Breakdown")
            t1 = pr.iloc[0]
            if "score_demand" in t1.index:
                comps = ["EV Demand","Supply Gap","Road Access","Coverage","Utilisation"]
                vals = [round(t1.get(f"score_{k}",0)*100,1) for k in ["demand","supply_gap","road_access","coverage","utilization"]]
                fig = go.Figure(go.Bar(
                    x=vals, y=comps, orientation="h",
                    marker=dict(color=vals,
                        colorscale=[[0,"rgba(33,58,95,0.6)"],[0.5,"rgba(33,150,243,0.7)"],[1,"rgba(0,196,140,0.8)"]],
                        line=dict(color="rgba(0,0,0,0)")),
                    text=[f"{v:.0f}" for v in vals],
                    textposition="outside",textfont=dict(color="#8aaccc",size=12),
                    hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>"))
                fl(fig, 370, xax=dict(showgrid=False,showticklabels=False,range=[0,max(vals)*1.3]))
                fig.update_layout(title=dict(text=f"<b>{t1['postcode']}</b>  ·  {t1['score']:.1f}/100", font=dict(color="white",size=13)))
                st.plotly_chart(fig, use_container_width=True)

        ins(f"Top recommendation: <b>{pr.iloc[0]['postcode']}</b> ({pr.iloc[0]['ward_name']}) — priority score <b>{pr.iloc[0]['score']:.1f}/100</b>. "
            f"<b>{pr.iloc[0]['ev_registrations_nearby']:,} EVs</b> registered in the catchment area, "
            f"nearest competitor <b>{pr.iloc[0]['nearest_competitor_km']:.1f} km</b> away. "
            f"Recommended deployment: <b>DC Rapid 50kW</b> with dual CCS connectors.", "🤖 AI Site Recommendation")

if __name__ == "__main__":
    main()
