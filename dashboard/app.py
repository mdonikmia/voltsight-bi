"""VoltSight BI — Outstanding Professional Dashboard"""
from __future__ import annotations
from pathlib import Path
import pandas as pd, numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="VoltSight BI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# ── NUCLEAR CSS — Forces dark everywhere ────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* FORCE DARK ON EVERYTHING */
html, body, [class*="css"], .stApp, .main, .block-container,
.stApp > div, .stApp > div > div, .stApp > div > div > div,
section.main, section.main > div, div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewBlockContainer"] {
    background-color: #070d1b !important;
    color: #e8f0fe !important;
    font-family: 'Inter', sans-serif !important;
}

/* MAIN CONTENT AREA */
.block-container {
    padding: 2rem 3rem !important;
    max-width: 100% !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] > div {
    background: linear-gradient(160deg, #0a1628 0%, #0c1e35 50%, #0a1628 100%) !important;
    border-right: 1px solid rgba(0,196,140,0.12) !important;
}
section[data-testid="stSidebar"] * { color: #dce8f8 !important; }
section[data-testid="stSidebar"] label { font-size: 14px !important; font-weight: 500 !important; }
section[data-testid="stSidebar"] label p { color: #dce8f8 !important; font-size: 14px !important; }
[data-testid="stRadio"] > div > label { 
    padding: 6px 10px !important; border-radius: 8px !important; 
    transition: background 0.2s !important; cursor: pointer !important;
}
[data-testid="stRadio"] > div > label:hover { background: rgba(0,196,140,0.1) !important; }

/* FILTER LABELS */
.stMultiSelect > label, [data-testid="stMultiSelect"] > label {
    color: #4a7a9b !important; font-size: 10px !important;
    font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 1.5px !important;
}

/* MULTISELECT TAGS */
[data-baseweb="tag"] {
    background: rgba(0,196,140,0.15) !important;
    border: 1px solid rgba(0,196,140,0.35) !important;
    border-radius: 6px !important;
}
[data-baseweb="tag"] span, [data-baseweb="tag"] * { color: #00e6a8 !important; font-weight: 600 !important; }
[data-baseweb="select"] > div { 
    background: rgba(10,22,40,0.95) !important;
    border: 1px solid rgba(30,58,95,0.7) !important;
    border-radius: 8px !important;
}
[data-baseweb="option"] { background: #0d1f38 !important; color: #dce8f8 !important; }
[data-baseweb="option"]:hover { background: rgba(0,196,140,0.12) !important; }
[data-baseweb="menu"] { background: #0d1f38 !important; border: 1px solid rgba(30,58,95,0.6) !important; }

/* DATAFRAME / TABLE */
[data-testid="stDataFrame"], .stDataFrame,
[data-testid="stDataFrame"] > div, iframe {
    background: transparent !important;
    border-radius: 16px !important;
}
.dvn-scroller { background: #0d1f38 !important; }

/* SLIDERS */
[data-testid="stSlider"] > div > div > div { background: rgba(0,196,140,0.3) !important; }
[data-testid="stSlider"] label { color: #dce8f8 !important; font-size: 12px !important; font-weight: 600 !important; }

/* PLOTLY CHARTS */
.js-plotly-plot, .plot-container { background: transparent !important; }

/* HIDE CLUTTER */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu, footer, [data-testid="stToolbar"], .stDeployButton { display: none !important; }

/* SCROLLBAR */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #070d1b; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #00c48c; }

/* ── COMPONENTS ── */
.kpi {
    background: linear-gradient(145deg, #0c1e35 0%, #0f2540 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px; padding: 20px 22px;
    position: relative; overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    cursor: default;
}
.kpi:hover {
    transform: translateY(-4px);
    box-shadow: 0 24px 48px rgba(0,0,0,0.5);
    border-color: rgba(255,255,255,0.1);
}
.kpi-bar { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.kpi-glow {
    position: absolute; top: -40px; right: -40px;
    width: 100px; height: 100px; border-radius: 50%;
    opacity: 0.06; filter: blur(20px);
}
.kpi-icon { font-size: 24px; margin-bottom: 10px; display: block; }
.kpi-lbl { color: #4a7a9b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
.kpi-val { color: #ffffff; font-size: 26px; font-weight: 900; line-height: 1; margin-bottom: 6px; letter-spacing: -0.5px; }
.kpi-sub { color: #2a4a6a; font-size: 11px; font-weight: 500; }

.insight {
    background: linear-gradient(135deg, rgba(0,196,140,0.06) 0%, rgba(0,150,200,0.03) 100%);
    border: 1px solid rgba(0,196,140,0.18);
    border-left: 3px solid #00c48c;
    border-radius: 14px; padding: 18px 22px; margin: 20px 0;
}
.insight-t { color: #00c48c; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
.insight-b { color: #b8cce0; font-size: 13px; line-height: 1.8; }

.pg-t { font-size: 30px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; }
.pg-s { color: #2a4a6a; font-size: 13px; font-weight: 400; margin-bottom: 24px; margin-top: 2px; }
.sec-h { 
    color: #dce8f8; font-size: 14px; font-weight: 700; 
    margin: 22px 0 12px; padding-bottom: 10px;
    border-bottom: 1px solid rgba(30,58,95,0.5);
    display: flex; align-items: center; gap: 8px;
}
.divider { height: 1px; background: linear-gradient(90deg,transparent,rgba(0,196,140,0.2),transparent); margin: 8px 0; }
</style>""", unsafe_allow_html=True)

# ── CONSTANTS ────────────────────────────────────────────────────────────────
GOLD = Path(__file__).parent.parent / "data" / "gold"
PAL  = ["#00c48c","#2196f3","#ff9800","#e91e63","#9c27b0","#00bcd4","#ff5722"]
CTC  = {"AC_slow":"#4CAF50","AC_fast":"#2196F3","DC_rapid":"#FF9800","DC_ultra":"#E91E63"}
AX   = dict(gridcolor="rgba(30,58,95,0.4)", linecolor="rgba(30,58,95,0.4)",
            tickfont=dict(color="#4a7a9b", size=11), zeroline=False)
B    = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,18,35,0.8)",
           font=dict(color="#8aaccc", family="Inter", size=11),
           margin=dict(l=0,r=0,t=28,b=0), hoverlabel=dict(bgcolor="#0d1f38",font_color="#dce8f8",bordercolor="#1e3a5f"))

def L(fig, h=300, xa=None, ya=None, **kw):
    x = {**AX, **(xa or {})}
    y = {**AX, **(ya or {})}
    fig.update_layout(**B, height=h, xaxis=x, yaxis=y, **kw)

def Y2(c): return dict(overlaying="y",side="right",gridcolor="rgba(0,0,0,0)",linecolor="rgba(0,0,0,0)",tickfont=dict(color=c,size=11))

def kpi(col, icon, lbl, val, sub, c1, c2):
    col.markdown(f"""<div class="kpi">
        <div class="kpi-bar" style="background:linear-gradient(90deg,{c1},{c2})"></div>
        <div class="kpi-glow" style="background:{c1}"></div>
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-lbl">{lbl}</div>
        <div class="kpi-val">{val}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def ins(body, t="💡 Key Insight"):
    st.markdown(f'<div class="insight"><div class="insight-t">{t}</div><div class="insight-b">{body}</div></div>', unsafe_allow_html=True)

def sec(t):
    st.markdown(f'<div class="sec-h">{t}</div>', unsafe_allow_html=True)

def hdr(title, sub):
    st.markdown(f'<div class="pg-t">{title}</div><div class="pg-s">{sub}</div>', unsafe_allow_html=True)

# ── DATA ─────────────────────────────────────────────────────────────────────
@st.cache_data
def load():
    tbls = ["dim_charger","dim_location","dim_date","fact_sessions","fact_availability","gold_priority_scores"]
    d = {t: (pd.read_parquet(GOLD/f"{t}.parquet") if (GOLD/f"{t}.parquet").exists() else _f(t)) for t in tbls}
    if "month" not in d["fact_sessions"].columns:
        d["fact_sessions"]["month"] = d["fact_sessions"]["date_key"] % 10000 // 100
    return d

def _f(t):
    np.random.seed(42)
    if t == "dim_charger":
        n=500; tp=np.random.choice(["AC_slow","AC_fast","DC_rapid","DC_ultra"],n,p=[.35,.35,.20,.10])
        return pd.DataFrame({"charger_id":[f"CHR{i:05d}"for i in range(n)], "charger_type":tp,
            "power_kw":[{"AC_slow":7,"AC_fast":22,"DC_rapid":50,"DC_ultra":150}[x]for x in tp],
            "postcode":[f"BS{i%99} {i%9}AA"for i in range(n)],
            "local_authority":np.random.choice(["Bristol","South Gloucestershire","Bath & NE Somerset"],n),
            "site_type":np.random.choice(["Retail","Motorway","Residential","Workplace","Leisure"],n)})
    if t == "fact_sessions":
        n=60000; m=np.random.randint(1,13,n)
        hw=np.array([.3,.2,.1,.1,.2,.5,.8,1.5,1.8,1.2,1,1.1,1.2,1,.9,1,1.3,1.8,2,1.9,1.5,1.1,.7,.4])
        return pd.DataFrame({"session_id":[f"S{i:08d}"for i in range(n)],
            "charger_id":[f"CHR{i:05d}"for i in np.random.randint(0,500,n)],
            "postcode":[f"BS{i%99} {i%9}AA"for i in range(n)],
            "date_key":[20250000+x*100+np.random.randint(1,28)for x in m],
            "start_hour":np.random.choice(24,n,p=hw/hw.sum()),
            "duration_min":np.random.randint(10,240,n),
            "energy_kwh":np.round(np.random.uniform(2,60,n),2),
            "revenue_gbp":np.round(np.random.uniform(1,30,n),2),
            "status":np.random.choice(["completed","fault"],n,p=[.92,.08]),
            "fault_type":np.random.choice([None,"network_timeout","payment_failure","connector_stuck","overheating","power_surge"],n,p=[.92,.016,.016,.016,.016,.016]),
            "month":m})
    if t == "fact_availability":
        n=10000
        return pd.DataFrame({"charger_id":[f"CHR{i:05d}"for i in np.random.randint(0,500,n)],
            "date_key":np.random.randint(20250101,20251231,n),
            "uptime_pct":np.clip(np.random.normal(92,5,n),0,100).round(1),
            "fault_type":np.random.choice([None,"network_timeout","payment_failure","connector_stuck","overheating","power_surge"],n,p=[.92,.016,.016,.016,.016,.016])})
    if t == "gold_priority_scores":
        n=99; sc=np.round(np.random.uniform(20,90,n),1)
        return pd.DataFrame({"postcode":[f"BS{i} 1AA"for i in range(n)],
            "ward_name":[f"Ward_{i%20}"for i in range(n)],
            "local_authority":np.random.choice(["Bristol","South Gloucestershire","Bath & NE Somerset"],n),
            "priority_score":sc, "priority_rank":pd.Series(sc).rank(ascending=False).astype(int).values,
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

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    data = load()
    MN = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

    # SIDEBAR
    with st.sidebar:
        st.markdown("""<div style="text-align:center;padding:30px 0 18px">
            <div style="font-size:48px;filter:drop-shadow(0 0 20px rgba(0,196,140,.7));line-height:1">⚡</div>
            <div style="color:#fff;font-size:20px;font-weight:900;margin-top:10px;letter-spacing:-.3px">VoltSight BI</div>
            <div style="color:#2a5a7a;font-size:9px;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-top:4px">EV INFRASTRUCTURE ANALYTICS</div>
        </div>
        <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(0,196,140,.25),transparent);margin:0 12px 20px"></div>""", unsafe_allow_html=True)

        page = st.radio("", [
            "📊  Network Overview",
            "🗺️  Location Intelligence",
            "🔧  Operations",
            "📍  Expansion Planner",
        ], label_visibility="collapsed")

        st.markdown("""<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(30,58,95,.5),transparent);margin:16px 0 14px"></div>
        <div style="color:#2a5a7a;font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px">FILTERS</div>""", unsafe_allow_html=True)

        ch = data["dim_charger"]
        las = sorted(ch["local_authority"].dropna().unique())
        sel_la = st.multiselect("Local Authority", las, default=las)
        tps = sorted(ch["charger_type"].unique())
        sel_tp = st.multiselect("Charger Type", tps, default=tps)
        all_m = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        sel_m = st.multiselect("Month", all_m, default=all_m)
        m_nums = [i+1 for i,m in enumerate(all_m) if m in sel_m]

        st.markdown("""<div style="margin-top:24px;padding:14px 16px;background:rgba(0,196,140,.05);border:1px solid rgba(0,196,140,.1);border-radius:12px">
        <div style="color:#2a5a7a;font-size:10px;line-height:2.2;font-weight:500">
        📋 UK National Chargepoint Registry<br>
        📊 12-month simulation · 2025<br>
        🔒 © VoltSight BI 2025
        </div></div>""", unsafe_allow_html=True)

    # FILTER
    chargers = ch.copy()
    if sel_la: chargers = chargers[chargers["local_authority"].isin(sel_la)]
    if sel_tp: chargers = chargers[chargers["charger_type"].isin(sel_tp)]
    cids = set(chargers["charger_id"])
    sess = data["fact_sessions"].copy()
    sess = sess[sess["charger_id"].isin(cids)]
    if m_nums: sess = sess[sess["month"].isin(m_nums)]
    avail = data["fact_availability"][data["fact_availability"]["charger_id"].isin(cids)].copy()
    comp  = sess[sess["status"]=="completed"]
    faults= sess[sess["status"]=="fault"]

    # ══════════════════════ PAGE 1: NETWORK OVERVIEW ══════════════════════
    if "Network Overview" in page:
        hdr("📊 Network Overview", "UK EV Charging Network · Full Year 2025 · Real-time Performance")
        c1,c2,c3,c4 = st.columns(4)
        kpi(c1,"🔌","Total Chargers",f"{len(chargers):,}","Active on network","#00c48c","#00e6a8")
        kpi(c2,"⚡","Sessions",f"{len(comp):,}","Completed 2025","#2196f3","#64b5f6")
        kpi(c3,"💷","Revenue",f"£{comp['revenue_gbp'].sum():,.0f}","Generated 2025","#ff9800","#ffb74d")
        kpi(c4,"🌿","Energy",f"{comp['energy_kwh'].sum()/1000:,.1f} MWh",f"Avg {comp['duration_min'].mean():.0f} min/session","#e91e63","#f48fb1")

        st.markdown("<br>", unsafe_allow_html=True)
        r1c1, r1c2 = st.columns([3,2])
        with r1c1:
            sec("📈 Monthly Sessions & Revenue Trend")
            mo = comp.groupby("month").agg(n=("session_id","count"), rev=("revenue_gbp","sum")).reset_index()
            mo["mn"] = mo["month"].map(MN)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=mo["mn"],y=mo["n"],fill="tozeroy",fillcolor="rgba(0,196,140,.08)",
                line=dict(color="#00c48c",width=2,shape="spline"),mode="lines+markers",
                marker=dict(size=6,color="#00c48c",line=dict(width=2,color="#070d1b")),
                name="Sessions",hovertemplate="<b>%{x}</b><br>%{y:,} sessions<extra></extra>"))
            fig.add_trace(go.Bar(x=mo["mn"],y=mo["rev"],
                marker=dict(color="rgba(33,150,243,.18)",line=dict(color="rgba(33,150,243,.35)",width=1)),
                yaxis="y2",name="Revenue £",hovertemplate="<b>%{x}</b><br>£%{y:,.0f}<extra></extra>"))
            L(fig,270,yaxis2=Y2("#2196f3"),
              legend=dict(orientation="h",y=1.08,x=0,bgcolor="rgba(0,0,0,0)",font=dict(color="#8aaccc")),
              hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        with r1c2:
            sec("🔌 Charger Fleet Composition")
            tc = chargers["charger_type"].value_counts().reset_index()
            tc.columns = ["type","count"]
            fig2 = go.Figure(go.Pie(
                labels=tc["type"], values=tc["count"], hole=0.68,
                marker=dict(colors=[CTC.get(t,"#888")for t in tc["type"]],line=dict(color="#070d1b",width=3)),
                textinfo="percent", textfont=dict(color="white",size=10),
                hovertemplate="<b>%{label}</b><br>%{value:,} units · %{percent}<extra></extra>"))
            L(fig2,270,legend=dict(orientation="h",y=-0.18,font=dict(color="#8aaccc",size=10),bgcolor="rgba(0,0,0,0)"),
              annotations=[dict(text=f"<b>{len(chargers):,}</b><br><span style='font-size:9px;color:#4a7a9b'>CHARGERS</span>",
                x=0.5,y=0.5,font=dict(size=18,color="white"),showarrow=False)])
            st.plotly_chart(fig2, use_container_width=True)

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            sec("⏰ Hourly Demand Pattern")
            hr = comp.groupby("start_hour").size().reset_index(name="n")
            peak = [7,8,17,18,19,20]
            fig3 = go.Figure(go.Bar(x=hr["start_hour"],y=hr["n"],
                marker=dict(color=["rgba(0,196,140,.85)"if h in peak else"rgba(30,58,95,.6)"for h in hr["start_hour"]],
                            line=dict(color="rgba(0,0,0,0)")),
                hovertemplate="<b>%{x}:00</b><br>%{y:,} sessions<extra></extra>"))
            L(fig3,240, xa=dict(**AX,tickmode="linear",tick0=0,dtick=4), bargap=0.12)
            fig3.add_annotation(x=8,y=hr["n"].max()*0.95,text="Morning<br>Rush",showarrow=False,font=dict(color="#00c48c",size=9))
            fig3.add_annotation(x=18,y=hr["n"].max()*0.95,text="Evening<br>Rush",showarrow=False,font=dict(color="#00c48c",size=9))
            st.plotly_chart(fig3, use_container_width=True)

        with r2c2:
            sec("🏪 Revenue by Site Type")
            if "site_type" in chargers.columns:
                mg = sess.merge(chargers[["charger_id","site_type"]],on="charger_id",how="left")
                st_s = mg[mg["status"]=="completed"].groupby("site_type").agg(rev=("revenue_gbp","sum")).reset_index().sort_values("rev")
                fig4 = go.Figure(go.Bar(x=st_s["rev"],y=st_s["site_type"],orientation="h",
                    marker=dict(color=st_s["rev"],colorscale=[[0,"rgba(30,58,95,.4)"],[1,"rgba(0,196,140,.85)"]],
                                line=dict(color="rgba(0,0,0,0)")),
                    text=[f"  £{v:,.0f}"for v in st_s["rev"]],textposition="outside",
                    textfont=dict(color="#8aaccc",size=10),
                    hovertemplate="<b>%{y}</b><br>£%{x:,.0f}<extra></extra>"))
                L(fig4,240,xa=dict(**AX,showgrid=False,showticklabels=False))
                st.plotly_chart(fig4, use_container_width=True)

        ph = comp.groupby("start_hour").size().idxmax()
        ins(f"Peak demand occurs at <b>{ph}:00</b> with rush windows at 07–09 and 17–20. "
            f"Network revenue totals <b>£{comp['revenue_gbp'].sum():,.0f}</b> across <b>{len(comp):,}</b> sessions — "
            f"a strong commercial signal. Recommend deploying DC Rapid units at motorway services during peak windows.", "💡 Network Intelligence")

    # ══════════════════════ PAGE 2: LOCATION ══════════════════════════════
    elif "Location" in page:
        hdr("🗺️ Location Intelligence", "Geographic distribution · Coverage gaps · EV demand signals across the UK")
        pr = data["gold_priority_scores"]
        las2 = chargers["local_authority"].value_counts()
        c1,c2,c3 = st.columns(3)
        kpi(c1,"🏛️","Areas Covered",str(chargers["local_authority"].nunique()),"Local authorities","#00c48c","#00e6a8")
        kpi(c2,"📍","Busiest Area",str(las2.index[0])if len(las2)else"N/A",f"{las2.iloc[0]:,} chargers"if len(las2)else"","#2196f3","#64b5f6")
        kpi(c3,"🚗","Avg EV Density",f"{int(pr['ev_registrations_nearby'].mean()):,}","Registrations per zone","#ff9800","#ffb74d")

        st.markdown("<br>",unsafe_allow_html=True)
        r1c1, r1c2 = st.columns([3,2])
        with r1c1:
            sec("🗺️ Priority Score Heatmap")
            if "latitude" in pr.columns:
                fig = px.scatter_mapbox(pr.sort_values("priority_score"),
                    lat="latitude",lon="longitude",color="priority_score",
                    size="ev_registrations_nearby",hover_name="postcode",
                    hover_data={"priority_score":":.1f","ward_name":True,"road_type":True,"latitude":False,"longitude":False},
                    color_continuous_scale=[[0,"#0d1f38"],[0.3,"#1565c0"],[0.7,"#0097a7"],[1,"#00c48c"]],
                    size_max=18,mapbox_style="carto-darkmatter",zoom=9.5,center={"lat":51.45,"lon":-2.58})
                fig.update_layout(**B,height=390,
                    coloraxis_colorbar=dict(title=dict(text="Score",font=dict(color="#8aaccc")),tickfont=dict(color="#8aaccc")))
                st.plotly_chart(fig,use_container_width=True)
        with r1c2:
            sec("📊 EV Demand vs Priority Score")
            fig2 = px.scatter(pr,x="ev_registrations_nearby",y="priority_score",color="road_type",
                size="population_density",hover_name="postcode",color_discrete_sequence=PAL,
                labels={"ev_registrations_nearby":"EV Registrations","priority_score":"Priority Score","road_type":"Road Type"})
            L(fig2,390,legend=dict(orientation="h",y=-0.2,font=dict(color="#8aaccc",size=10),bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig2,use_container_width=True)

        sec("🏛️ Session & Revenue Performance by Local Authority")
        la_s = comp.merge(chargers[["charger_id","local_authority"]],on="charger_id",how="left")
        la_g = la_s.groupby("local_authority").agg(n=("session_id","count"),rev=("revenue_gbp","sum")).reset_index().sort_values("rev",ascending=False)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Sessions",x=la_g["local_authority"],y=la_g["n"],
            marker=dict(color="rgba(0,196,140,.7)",line=dict(color="rgba(0,0,0,0)"))))
        fig3.add_trace(go.Scatter(name="Revenue £",x=la_g["local_authority"],y=la_g["rev"],
            mode="lines+markers",line=dict(color="#ff9800",width=2.5,shape="spline"),
            marker=dict(size=8,color="#ff9800",line=dict(width=2,color="#070d1b")),yaxis="y2"))
        L(fig3,250,yaxis2=Y2("#ff9800"),legend=dict(orientation="h",y=1.08,bgcolor="rgba(0,0,0,0)",font=dict(color="#8aaccc")))
        st.plotly_chart(fig3,use_container_width=True)
        if len(la_g):
            ins(f"<b>{la_g.iloc[0]['local_authority']}</b> leads with <b>£{la_g.iloc[0]['rev']:,.0f}</b> from "
                f"<b>{la_g.iloc[0]['n']:,}</b> sessions. Prioritise infrastructure investment in high-performing zones for maximum ROI.", "📍 Location Insight")

    # ══════════════════════ PAGE 3: OPERATIONS ════════════════════════════
    elif "Operations" in page:
        hdr("🔧 Operations & Reliability", "Network health monitoring · Fault diagnostics · SLA performance")
        avg_up = avail["uptime_pct"].mean()
        b95 = (avail.groupby("charger_id")["uptime_pct"].mean()<95).sum()
        fm = faults["fault_type"].dropna().mode()
        c1,c2,c3,c4 = st.columns(4)
        sla_ok = avg_up >= 95
        kpi(c1,"📡","Network Uptime",f"{avg_up:.1f}%","Target: 95% SLA",("#00c48c","#00e6a8")[not sla_ok],("#00e6a8","#ffb74d")[not sla_ok])
        kpi(c2,"⚠️","Below SLA",str(int(b95)),"Chargers underperforming","#e91e63","#f48fb1")
        kpi(c3,"🔴","Fault Incidents",f"{len(faults):,}","Recorded 2025","#ff5722","#ff8a65")
        kpi(c4,"🛠️","Primary Fault",fm[0].replace("_"," ").title()if len(fm)else"N/A","Most common type","#9c27b0","#ce93d8")

        st.markdown("<br>",unsafe_allow_html=True)
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            sec("🔴 Fault Type Breakdown")
            fc = faults["fault_type"].dropna().value_counts().reset_index()
            fc.columns = ["type","count"]
            fc["label"] = fc["type"].str.replace("_"," ").str.title()
            fig = go.Figure(go.Bar(x=fc["count"],y=fc["label"],orientation="h",
                marker=dict(color=fc["count"],colorscale=[[0,"rgba(33,58,95,.5)"],[1,"rgba(229,57,53,.85)"]],
                            line=dict(color="rgba(0,0,0,0)")),
                text=[f"  {v:,}"for v in fc["count"]],textposition="outside",
                textfont=dict(color="#8aaccc",size=10),
                hovertemplate="<b>%{y}</b><br>%{x:,} incidents<extra></extra>"))
            L(fig,270,xa=dict(**AX,showgrid=False,showticklabels=False))
            st.plotly_chart(fig,use_container_width=True)

        with r1c2:
            sec("📊 Uptime Distribution vs SLA")
            fig2 = go.Figure()
            fig2.add_trace(go.Histogram(x=avail["uptime_pct"],nbinsx=25,
                marker=dict(color="rgba(33,150,243,.55)",line=dict(color="rgba(33,150,243,.3)",width=1)),
                hovertemplate="Uptime: %{x:.1f}%<br>Count: %{y:,}<extra></extra>"))
            fig2.add_vline(x=95,line_dash="dash",line_color="#00c48c",line_width=1.5,
                annotation=dict(text="95% SLA",font=dict(color="#00c48c",size=10),bgcolor="rgba(0,0,0,0)"))
            fig2.add_vline(x=avg_up,line_dash="dot",line_color="#ff9800",line_width=1.5,
                annotation=dict(text=f"Avg {avg_up:.1f}%",font=dict(color="#ff9800",size=10),bgcolor="rgba(0,0,0,0)"))
            L(fig2,270)
            st.plotly_chart(fig2,use_container_width=True)

        sec("📅 Monthly Fault Volume & Rate")
        mf = faults.groupby("month").size().reset_index(name="faults")
        mc_d = comp.groupby("month").size().reset_index(name="comp")
        mt = mf.merge(mc_d,on="month",how="outer").fillna(0)
        mt["rate"] = (mt["faults"]/(mt["faults"]+mt["comp"])*100).round(1)
        mt["mn"] = mt["month"].map(MN)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=mt["mn"],y=mt["faults"],name="Faults",
            marker=dict(color="rgba(229,57,53,.45)",line=dict(color="rgba(229,57,53,.2)",width=1))))
        fig3.add_trace(go.Scatter(x=mt["mn"],y=mt["rate"],name="Fault Rate %",
            line=dict(color="#ff9800",width=2,shape="spline"),
            marker=dict(size=6,color="#ff9800"),yaxis="y2",
            hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>"))
        L(fig3,250,yaxis2=Y2("#ff9800"),legend=dict(orientation="h",y=1.08,bgcolor="rgba(0,0,0,0)",font=dict(color="#8aaccc")))
        st.plotly_chart(fig3,use_container_width=True)
        ins(f"Network uptime <b>{avg_up:.1f}%</b> vs 95% SLA. <b>{int(b95)} chargers</b> are below threshold. "
            f"Primary fault: <b>{fm[0].replace('_',' ').title()if len(fm)else'N/A'}</b>. "
            f"Immediate action: schedule preventative maintenance cycle for underperforming units.", "🔧 Operations Alert")

    # ══════════════════════ PAGE 4: EXPANSION PLANNER ═════════════════════
    elif "Expansion" in page:
        hdr("📍 Expansion Planner", "AI-powered site ranking · Identify optimal locations for EV charger deployment")
        pr = data["gold_priority_scores"].copy()

        sec("⚙️ Priority Weight Configuration")
        st.markdown('<div style="color:#2a5a7a;font-size:12px;margin:-8px 0 16px;font-weight:400">Adjust weights to align with your strategic priorities. All rankings recalculate in real time.</div>',unsafe_allow_html=True)
        c1,c2,c3,c4,c5 = st.columns(5)
        w1 = c1.slider("🚗 EV Demand",    0,100,30,5, help="EV registration density in area")
        w2 = c2.slider("📉 Supply Gap",   0,100,25,5, help="Charger-to-EV ratio (lower = bigger gap)")
        w3 = c3.slider("🛣️ Road Access",  0,100,20,5, help="Road type & motorway proximity")
        w4 = c4.slider("📡 Coverage",     0,100,15,5, help="Distance from nearest competitor")
        w5 = c5.slider("⚡ Utilisation",  0,100,10,5, help="How busy nearby chargers are")
        tot = max(w1+w2+w3+w4+w5, 1)

        if all(c in pr.columns for c in ["score_demand","score_supply_gap"]):
            pr["score"] = ((pr["score_demand"]*w1+pr["score_supply_gap"]*w2+pr["score_road_access"]*w3+pr["score_coverage"]*w4+pr["score_utilization"]*w5)/tot*100).round(1)
        else:
            pr["score"] = pr["priority_score"]
        pr = pr.sort_values("score",ascending=False).reset_index(drop=True)

        st.markdown("<br>",unsafe_allow_html=True)
        r1c1, r1c2 = st.columns([3,2])
        with r1c1:
            sec("🏆 Top 10 Priority Sites for New Charger")
            t10 = pr.head(10).copy()
            disp = pd.DataFrame({
                "Rank":     [f"#{i}" for i in range(1,11)],
                "Postcode": t10["postcode"].values,
                "Ward":     t10["ward_name"].values,
                "Authority":t10["local_authority"].values,
                "Score":    [f"{s:.1f}" for s in t10["score"].values],
                "EV Count": [f"{v:,}" for v in t10["ev_registrations_nearby"].values],
                "Road":     t10["road_type"].values,
                "Gap (km)": [f"{v:.1f}" for v in t10["nearest_competitor_km"].values],
            })
            disp.index = range(1,11)
            st.dataframe(disp, use_container_width=True, height=350)

        with r1c2:
            sec("📊 Score Breakdown — #1 Site")
            t1 = pr.iloc[0]
            if "score_demand" in t1.index:
                keys = ["demand","supply_gap","road_access","coverage","utilization"]
                lbls = ["EV Demand","Supply Gap","Road Access","Coverage","Utilisation"]
                vals = [round(t1.get(f"score_{k}",0)*100,1) for k in keys]
                fig = go.Figure(go.Bar(x=vals, y=lbls, orientation="h",
                    marker=dict(color=vals, colorscale=[[0,"rgba(30,58,95,.5)"],[0.5,"rgba(33,150,243,.7)"],[1,"rgba(0,196,140,.85)"]],
                                line=dict(color="rgba(0,0,0,0)")),
                    text=[f"{v:.0f}" for v in vals], textposition="outside",
                    textfont=dict(color="#8aaccc",size=11),
                    hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>"))
                L(fig, 350, xa=dict(**AX,showgrid=False,showticklabels=False,range=[0,max(vals)*1.3]))
                fig.update_layout(title=dict(text=f"<b>{t1['postcode']}</b>  ·  {t1['score']:.1f}/100",font=dict(color="white",size=13)))
                st.plotly_chart(fig, use_container_width=True)

        ins(f"Top recommendation: <b>{pr.iloc[0]['postcode']}</b> ({pr.iloc[0]['ward_name']}) — "
            f"priority score <b>{pr.iloc[0]['score']:.1f}/100</b>. "
            f"<b>{pr.iloc[0]['ev_registrations_nearby']:,} EVs</b> in catchment area, "
            f"nearest competitor <b>{pr.iloc[0]['nearest_competitor_km']:.1f} km</b> away. "
            f"Recommended deployment: <b>DC Rapid 50kW with dual CCS connectors</b>.", "🤖 AI Site Recommendation")

if __name__ == "__main__":
    main()
