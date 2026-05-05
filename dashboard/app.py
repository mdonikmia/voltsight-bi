"""
VoltSight BI — Professional Dashboard v2
"""
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
.stApp{background-color:#0a0f1e}
section[data-testid="stSidebar"]{background-color:#0d1426;border-right:1px solid #1e3a5f}
header[data-testid="stHeader"]{background:transparent}
.kpi-card{background:linear-gradient(135deg,#0d1f35,#1a2f4a);border:1px solid #1e3a5f;border-radius:16px;padding:24px;margin:8px 0;position:relative;overflow:hidden}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:16px 16px 0 0}
.kpi-green::before{background:linear-gradient(90deg,#00c48c,#00e6a8)}
.kpi-blue::before{background:linear-gradient(90deg,#2196f3,#64b5f6)}
.kpi-orange::before{background:linear-gradient(90deg,#ff9800,#ffb74d)}
.kpi-pink::before{background:linear-gradient(90deg,#e91e63,#f48fb1)}
.kpi-label{color:#7a9cc4;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
.kpi-value{color:#fff;font-size:30px;font-weight:800;line-height:1.1;margin-bottom:4px}
.kpi-delta{color:#7a9cc4;font-size:12px}
.insight-card{background:linear-gradient(135deg,#0d1f35,#1a2f4a);border:1px solid #1e3a5f;border-left:4px solid #00c48c;border-radius:12px;padding:16px 20px;margin:12px 0}
.insight-title{color:#00c48c;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.insight-text{color:#c8d8ea;font-size:14px;line-height:1.6}
.page-title{font-size:34px;font-weight:900;color:#fff;margin-bottom:4px}
.page-sub{color:#7a9cc4;font-size:14px;margin-bottom:20px}
.sec-header{color:#fff;font-size:18px;font-weight:700;padding:8px 0 4px;border-bottom:1px solid #1e3a5f;margin-bottom:12px}
#MainMenu,footer{visibility:hidden}
</style>
""", unsafe_allow_html=True)

GOLD_DIR = Path(__file__).parent.parent / "data" / "gold"
PALETTE = ["#00c48c","#2196f3","#ff9800","#e91e63","#9c27b0","#00bcd4"]
CT_COLORS = {"AC_slow":"#4CAF50","AC_fast":"#2196F3","DC_rapid":"#FF9800","DC_ultra":"#E91E63"}
BASE = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,31,53,0.5)",
            font=dict(color="#c8d8ea"), margin=dict(l=0,r=0,t=30,b=0),
            xaxis=dict(gridcolor="#1e3a5f"), yaxis=dict(gridcolor="#1e3a5f"))

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
            "site_type":np.random.choice(["retail","motorway_services","residential","workplace"],n)})
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
            "fault_type":np.random.choice([None,"network_timeout","payment_failure","connector_stuck"],n,p=[.92,.027,.027,.026])})
    if t == "gold_priority_scores":
        n=99; sc=np.round(np.random.uniform(20,90,n),1)
        return pd.DataFrame({"postcode":[f"BS{i} 1AA" for i in range(n)],
            "ward_name":[f"Ward_{i%20}" for i in range(n)],
            "local_authority":np.random.choice(["Bristol","South Gloucestershire","Bath & NE Somerset"],n),
            "priority_score":sc,"priority_rank":pd.Series(sc).rank(ascending=False).astype(int).values,
            "ev_registrations_nearby":np.random.randint(50,2000,n),
            "population_density":np.random.randint(500,8000,n),
            "road_type":np.random.choice(["motorway","A_road","B_road","urban"],n),
            "nearest_competitor_km":np.round(np.random.uniform(.1,15,n),1),
            "latitude":np.random.uniform(51.35,51.55,n),
            "longitude":np.random.uniform(-2.75,-2.40,n),
            "score_demand":np.random.uniform(0,1,n),"score_supply_gap":np.random.uniform(0,1,n),
            "score_road_access":np.random.uniform(0,1,n),"score_coverage":np.random.uniform(0,1,n),
            "score_utilization":np.random.uniform(0,1,n)})
    return pd.DataFrame()

def kpi(col, lbl, val, delta, colour, icon):
    col.markdown(f'<div class="kpi-card kpi-{colour}"><div class="kpi-label">{icon} {lbl}</div><div class="kpi-value">{val}</div><div class="kpi-delta">{delta}</div></div>', unsafe_allow_html=True)

def insight(txt, title="💡 Insight"):
    st.markdown(f'<div class="insight-card"><div class="insight-title">{title}</div><div class="insight-text">{txt}</div></div>', unsafe_allow_html=True)

def sec(t):
    st.markdown(f'<div class="sec-header">{t}</div>', unsafe_allow_html=True)

def fl(fig, h=300):
    fig.update_layout(**BASE, height=h)
    return fig

def main():
    data = load()

    with st.sidebar:
        st.markdown('<div style="text-align:center;padding:20px 0 10px"><div style="font-size:36px">⚡</div><div style="color:white;font-size:20px;font-weight:800">VoltSight BI</div><div style="color:#7a9cc4;font-size:11px">EV Infrastructure Analytics</div></div>', unsafe_allow_html=True)
        st.divider()
        page = st.radio("", ["📊 Network Overview","🗺️ Location Intelligence","🔧 Operations","📍 Expansion Planner"], label_visibility="collapsed")
        st.divider()
        st.markdown('<div style="color:#7a9cc4;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Filters</div>', unsafe_allow_html=True)
        ch = data["dim_charger"]
        las = sorted(ch["local_authority"].dropna().unique())
        sel_la = st.multiselect("Local Authority", las, default=las)
        tps = sorted(ch["charger_type"].unique())
        sel_tp = st.multiselect("Charger Type", tps, default=tps)
        mnths = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        sel_m = st.multiselect("Month", mnths, default=mnths)
        m_nums = [i+1 for i,m in enumerate(mnths) if m in sel_m]
        st.divider()
        st.markdown('<div style="color:#3a5a7a;font-size:10px">Data: UK National Chargepoint Registry<br>Sessions: 12-month simulation (2025)<br><br>© VoltSight BI 2025</div>', unsafe_allow_html=True)

    # Filter
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

    # ── PAGE 1 ─────────────────────────────────────────────────────────────
    if page == "📊 Network Overview":
        st.markdown('<div class="page-title">📊 Network Overview</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-sub">UK EV Charging Network — Full Year 2025 Performance</div>', unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        kpi(c1,"Total Chargers",f"{len(chargers):,}","Active on network","green","🔌")
        kpi(c2,"Total Sessions",f"{len(comp):,}","Completed 2025","blue","⚡")
        kpi(c3,"Total Revenue",f"£{comp['revenue_gbp'].sum():,.0f}","Full year","orange","💷")
        kpi(c4,"Avg Session",f"{comp['duration_min'].mean():.0f} min",f"{comp['energy_kwh'].sum():,.0f} kWh total","pink","⏱")
        st.markdown("<br>", unsafe_allow_html=True)

        c1,c2 = st.columns([3,2])
        with c1:
            sec("📈 Monthly Sessions & Revenue")
            mo = comp.groupby("month").agg(sessions=("session_id","count"),revenue=("revenue_gbp","sum")).reset_index()
            mo["mn"] = mo["month"].map(mn)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=mo["mn"],y=mo["sessions"],fill="tozeroy",
                fillcolor="rgba(0,196,140,0.15)",line=dict(color="#00c48c",width=3),
                mode="lines+markers",marker=dict(size=8,color="#00c48c"),name="Sessions"))
            fig.add_trace(go.Bar(x=mo["mn"],y=mo["revenue"],marker_color="rgba(33,150,243,0.25)",
                yaxis="y2",name="Revenue £"))
            fig.update_layout(**BASE,height=280,
                yaxis2=dict(overlaying="y",side="right",gridcolor="transparent",color="#7a9cc4"),
                legend=dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            sec("🔌 Charger Type Split")
            tc = chargers["charger_type"].value_counts().reset_index()
            tc.columns = ["type","count"]
            fig2 = go.Figure(go.Pie(labels=tc["type"],values=tc["count"],hole=0.6,
                marker=dict(colors=[CT_COLORS.get(t,"#888") for t in tc["type"]],
                            line=dict(color="#0a0f1e",width=3)),
                textfont=dict(color="white",size=11)))
            fig2.update_layout(**BASE,height=280,
                legend=dict(orientation="h",y=-0.2,font=dict(color="#c8d8ea",size=10)),
                annotations=[dict(text=f"<b>{len(chargers)}</b>",x=0.5,y=0.5,
                    font=dict(size=20,color="white"),showarrow=False)])
            st.plotly_chart(fig2, use_container_width=True)

        c3,c4 = st.columns(2)
        with c3:
            sec("⏰ Peak Hours")
            hr = comp.groupby("start_hour").size().reset_index(name="n")
            fig3 = go.Figure(go.Bar(x=hr["start_hour"],y=hr["n"],
                marker_color=["#00c48c" if h in [7,8,17,18,19] else "#1a2f4a" for h in hr["start_hour"]],
                hovertemplate="Hour %{x}:00<br>Sessions: %{y:,}<extra></extra>"))
            fig3.update_layout(**BASE,height=240,bargap=0.1)
            st.plotly_chart(fig3, use_container_width=True)

        with c4:
            sec("🏪 Sessions by Site Type")
            if "site_type" in chargers.columns:
                mg = sess.merge(chargers[["charger_id","site_type"]],on="charger_id",how="left")
                st_s = mg[mg["status"]=="completed"].groupby("site_type").size().reset_index(name="n").sort_values("n")
                fig4 = go.Figure(go.Bar(x=st_s["n"],y=st_s["site_type"],orientation="h",
                    marker=dict(color=st_s["n"],colorscale=[[0,"#0d1f35"],[1,"#00c48c"]]),
                    hovertemplate="<b>%{y}</b><br>%{x:,}<extra></extra>"))
                fig4.update_layout(**BASE,height=240)
                st.plotly_chart(fig4, use_container_width=True)

        ph = comp.groupby("start_hour").size().idxmax()
        insight(f"Peak demand at <b>{ph}:00</b>. Network delivered <b>£{comp['revenue_gbp'].sum():,.0f}</b> revenue across <b>{len(comp):,}</b> sessions in 2025. Consider deploying DC Rapid units at peak-hour hotspots.", "💡 Network Insight")

    # ── PAGE 2 ─────────────────────────────────────────────────────────────
    elif page == "🗺️ Location Intelligence":
        st.markdown('<div class="page-title">🗺️ Location Intelligence</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-sub">Geographic distribution, coverage gaps, and demand signals</div>', unsafe_allow_html=True)
        pr = data["gold_priority_scores"]
        c1,c2,c3 = st.columns(3)
        las2 = chargers["local_authority"].value_counts()
        kpi(c1,"Local Authorities",str(chargers["local_authority"].nunique()),"Areas covered","green","🏛️")
        kpi(c2,"Top Area",str(las2.index[0]) if len(las2) else "N/A",f"{las2.iloc[0]:,} chargers" if len(las2) else "","blue","📍")
        kpi(c3,"Avg EV Registrations",f"{int(pr['ev_registrations_nearby'].mean()):,}","Per coverage zone","orange","🚗")
        st.markdown("<br>",unsafe_allow_html=True)

        c1,c2 = st.columns([3,2])
        with c1:
            sec("🗺️ Priority Score Map")
            if "latitude" in pr.columns:
                fig = px.scatter_mapbox(pr.sort_values("priority_score"),
                    lat="latitude",lon="longitude",color="priority_score",
                    size="ev_registrations_nearby",hover_name="postcode",
                    color_continuous_scale=[[0,"#0d1f35"],[0.5,"#2196f3"],[1,"#00c48c"]],
                    size_max=18,mapbox_style="carto-darkmatter",zoom=9.5,
                    center={"lat":51.45,"lon":-2.58})
                fig.update_layout(**BASE,height=400)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            sec("📊 Demand vs Supply")
            fig2 = px.scatter(pr,x="ev_registrations_nearby",y="priority_score",
                color="road_type",size="population_density",hover_name="postcode",
                color_discrete_sequence=PALETTE,
                labels={"ev_registrations_nearby":"EV Registrations","priority_score":"Priority Score"})
            fig2.update_layout(**BASE,height=400,legend=dict(orientation="h",y=-0.15,font=dict(color="#c8d8ea",size=10)))
            st.plotly_chart(fig2, use_container_width=True)

        sec("🏛️ Revenue by Local Authority")
        la_s = comp.merge(chargers[["charger_id","local_authority"]],on="charger_id",how="left")
        la_g = la_s.groupby("local_authority").agg(sessions=("session_id","count"),revenue=("revenue_gbp","sum")).reset_index().sort_values("revenue",ascending=False)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Sessions",x=la_g["local_authority"],y=la_g["sessions"],marker_color="#00c48c"))
        fig3.add_trace(go.Scatter(name="Revenue £",x=la_g["local_authority"],y=la_g["revenue"],
            mode="lines+markers",line=dict(color="#ff9800",width=3),yaxis="y2"))
        fig3.update_layout(**BASE,height=260,yaxis2=dict(overlaying="y",side="right",gridcolor="transparent",color="#ff9800"),
            legend=dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig3, use_container_width=True)
        if len(la_g): insight(f"<b>{la_g.iloc[0]['local_authority']}</b> leads with <b>£{la_g.iloc[0]['revenue']:,.0f}</b> revenue from <b>{la_g.iloc[0]['sessions']:,}</b> sessions. Prioritise investment here for maximum ROI.", "📍 Location Insight")

    # ── PAGE 3 ─────────────────────────────────────────────────────────────
    elif page == "🔧 Operations":
        st.markdown('<div class="page-title">🔧 Operations & Reliability</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-sub">Network health, uptime monitoring, and fault diagnostics</div>', unsafe_allow_html=True)
        avg_up = avail["uptime_pct"].mean()
        b95 = (avail.groupby("charger_id")["uptime_pct"].mean() < 95).sum()
        fm = faults["fault_type"].dropna().mode()
        c1,c2,c3,c4 = st.columns(4)
        kpi(c1,"Avg Network Uptime",f"{avg_up:.1f}%","Target: 95%","green" if avg_up>=95 else "orange","📡")
        kpi(c2,"Chargers Below 95%",str(int(b95)),"Need attention","pink","⚠️")
        kpi(c3,"Fault Incidents",f"{len(faults):,}","Total 2025","orange","🔴")
        kpi(c4,"Top Fault",fm[0] if len(fm) else "N/A","Primary cause","blue","🛠️")
        st.markdown("<br>",unsafe_allow_html=True)

        c1,c2 = st.columns(2)
        with c1:
            sec("🔴 Fault Breakdown")
            fc = faults["fault_type"].dropna().value_counts().reset_index()
            fc.columns = ["type","count"]
            fig = go.Figure(go.Bar(x=fc["count"],y=fc["type"],orientation="h",
                marker=dict(color=fc["count"],colorscale=[[0,"#1a2f4a"],[1,"#ff6b6b"]]),
                text=fc["count"],textposition="outside",textfont=dict(color="#c8d8ea")))
            fig.update_layout(**BASE,height=280)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            sec("📊 Uptime Distribution")
            fig2 = go.Figure(go.Histogram(x=avail["uptime_pct"],nbinsx=25,
                marker=dict(color="#2196f3",opacity=0.8,line=dict(color="#0a0f1e",width=1))))
            fig2.add_vline(x=95,line_dash="dash",line_color="#00c48c",line_width=2,annotation_text="95% SLA",annotation_font_color="#00c48c")
            fig2.add_vline(x=avg_up,line_dash="dot",line_color="#ff9800",line_width=2,annotation_text=f"Avg {avg_up:.1f}%",annotation_font_color="#ff9800")
            fig2.update_layout(**BASE,height=280)
            st.plotly_chart(fig2, use_container_width=True)

        sec("📅 Monthly Fault Trend")
        mf = faults.groupby("month").size().reset_index(name="faults")
        mc = comp.groupby("month").size().reset_index(name="completed")
        mt = mf.merge(mc,on="month",how="outer").fillna(0)
        mt["fault_rate"] = (mt["faults"]/(mt["faults"]+mt["completed"])*100).round(1)
        mt["mn"] = mt["month"].map(mn)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=mt["mn"],y=mt["faults"],name="Faults",marker_color="rgba(255,107,107,0.7)"))
        fig3.add_trace(go.Scatter(x=mt["mn"],y=mt["fault_rate"],name="Fault Rate %",
            line=dict(color="#ff9800",width=2,dash="dot"),yaxis="y2",mode="lines+markers"))
        fig3.update_layout(**BASE,height=250,yaxis2=dict(overlaying="y",side="right",gridcolor="transparent",color="#ff9800"),
            legend=dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig3, use_container_width=True)
        insight(f"Uptime <b>{avg_up:.1f}%</b> vs 95% target. <b>{int(b95)} chargers</b> underperforming. Top fault: <b>{fm[0] if len(fm) else 'N/A'}</b> — schedule preventative maintenance.", "🔧 Operations Insight")

    # ── PAGE 4 ─────────────────────────────────────────────────────────────
    elif page == "📍 Expansion Planner":
        st.markdown('<div class="page-title">📍 Expansion Planner</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-sub">AI-powered site ranking — Where to install the next EV charger</div>', unsafe_allow_html=True)
        pr = data["gold_priority_scores"].copy()
        sec("⚙️ Adjust Priority Weights")
        c1,c2,c3,c4,c5 = st.columns(5)
        w1=c1.slider("🚗 Demand",0,100,30,5)
        w2=c2.slider("📉 Supply Gap",0,100,25,5)
        w3=c3.slider("🛣️ Road Access",0,100,20,5)
        w4=c4.slider("📡 Coverage",0,100,15,5)
        w5=c5.slider("⚡ Utilization",0,100,10,5)
        tot = max(w1+w2+w3+w4+w5, 1)
        if all(c in pr.columns for c in ["score_demand","score_supply_gap"]):
            pr["score"] = ((pr["score_demand"]*w1+pr["score_supply_gap"]*w2+pr["score_road_access"]*w3+pr["score_coverage"]*w4+pr["score_utilization"]*w5)/tot*100).round(1)
        else:
            pr["score"] = pr["priority_score"]
        pr = pr.sort_values("score",ascending=False).reset_index(drop=True)
        st.markdown("<br>",unsafe_allow_html=True)

        c1,c2 = st.columns([3,2])
        with c1:
            sec("🏆 Top 10 Sites for New Charger")
            t10 = pr.head(10).copy()
            t10.index = range(1,11)
            t10["Score"] = t10["score"].apply(lambda x: f"{x:.1f}/100")
            t10["EV Demand"] = t10["ev_registrations_nearby"].apply(lambda x: f"{x:,}")
            t10["Competition"] = t10["nearest_competitor_km"].apply(lambda x: f"{x:.1f} km")
            st.dataframe(t10[["postcode","ward_name","local_authority","Score","road_type","EV Demand","Competition"]].rename(columns={"postcode":"Postcode","ward_name":"Ward","local_authority":"Local Authority","road_type":"Road"}), use_container_width=True, height=360)

        with c2:
            sec(f"📊 Score: #{1} Site")
            t1 = pr.iloc[0]
            if "score_demand" in t1.index:
                bd = pd.DataFrame({"Component":["🚗 Demand","📉 Supply Gap","🛣️ Road","📡 Coverage","⚡ Utilization"],
                    "Score":[round(t1.get("score_demand",0)*100,1),round(t1.get("score_supply_gap",0)*100,1),
                              round(t1.get("score_road_access",0)*100,1),round(t1.get("score_coverage",0)*100,1),
                              round(t1.get("score_utilization",0)*100,1)]})
                fig = go.Figure(go.Bar(x=bd["Score"],y=bd["Component"],orientation="h",
                    marker=dict(color=bd["Score"],colorscale=[[0,"#1a2f4a"],[1,"#00c48c"]]),
                    text=[f"{s:.0f}" for s in bd["Score"]],textposition="outside",textfont=dict(color="#c8d8ea")))
                fig.update_layout(**BASE,height=360,title=dict(text=f"<b>{t1['postcode']}</b> — {t1['score']:.1f}/100",font=dict(color="white",size=13)))
                st.plotly_chart(fig, use_container_width=True)

        insight(f"Top site: <b>{pr.iloc[0]['postcode']}</b> ({pr.iloc[0]['ward_name']}) — Score <b>{pr.iloc[0]['score']:.1f}/100</b>. "
                f"<b>{pr.iloc[0]['ev_registrations_nearby']:,} EVs</b> nearby, nearest competitor <b>{pr.iloc[0]['nearest_competitor_km']:.1f} km</b>. "
                f"Recommended: <b>DC Rapid 50kW</b> unit.", "🤖 AI Recommendation")

if __name__ == "__main__":
    main()
