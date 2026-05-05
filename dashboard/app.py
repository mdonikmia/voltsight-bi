"""VoltSight BI — Professional Dashboard"""
from __future__ import annotations
from pathlib import Path
import pandas as pd, numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="VoltSight BI", page_icon="⚡", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*{font-family:'Inter',sans-serif!important}
.stApp{background:#060d1a!important}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1628,#0d1f38)!important;border-right:1px solid rgba(0,196,140,0.15)!important}
section[data-testid="stSidebar"] *{color:#e8f0fe!important}
section[data-testid="stSidebar"] label{color:#e8f0fe!important;font-size:14px!important;font-weight:500!important}
section[data-testid="stSidebar"] label p{color:#e8f0fe!important}
section[data-testid="stSidebar"] .stMultiSelect label{color:#4a8aaa!important;font-size:10px!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:1px!important}
[data-baseweb="tag"]{background:rgba(0,196,140,0.15)!important;border:1px solid rgba(0,196,140,0.3)!important}
[data-baseweb="tag"] *{color:#00e6a8!important;font-weight:600!important}
[data-baseweb="select"]>div{background:rgba(13,31,56,0.9)!important;border-color:rgba(30,58,95,0.8)!important}
[data-baseweb="option"]{background:#0d1f38!important;color:#e8f0fe!important}
header[data-testid="stHeader"]{background:transparent!important}
#MainMenu,footer,.stDeployButton,[data-testid="stToolbar"]{visibility:hidden!important}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:#1e3a5f;border-radius:2px}
.kpi{background:linear-gradient(145deg,#0d1f38,#112540);border:1px solid rgba(255,255,255,0.07);border-radius:20px;padding:22px 24px;position:relative;overflow:hidden;transition:all .3s}
.kpi:hover{transform:translateY(-3px);box-shadow:0 20px 40px rgba(0,0,0,.4)}
.kpi-bar{position:absolute;top:0;left:0;right:0;height:2px}
.kpi-icon{font-size:26px;margin-bottom:8px;display:block}
.kpi-lbl{color:#5a7a9a;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px}
.kpi-val{color:#fff;font-size:28px;font-weight:800;line-height:1;margin-bottom:6px;letter-spacing:-.5px}
.kpi-sub{color:#3a5a7a;font-size:12px}
.ins{background:linear-gradient(135deg,rgba(0,196,140,.07),rgba(0,196,140,.02));border:1px solid rgba(0,196,140,.2);border-left:3px solid #00c48c;border-radius:12px;padding:16px 20px;margin:16px 0}
.ins-t{color:#00c48c;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px}
.ins-b{color:#c8d8ea;font-size:13px;line-height:1.7}
.pg-t{font-size:32px;font-weight:900;color:#fff;letter-spacing:-1px;margin-bottom:2px}
.pg-s{color:#3a5a7a;font-size:13px;margin-bottom:20px}
.sec{color:#e2eaf4;font-size:15px;font-weight:700;margin:18px 0 10px;padding-bottom:8px;border-bottom:1px solid rgba(30,58,95,.6)}
</style>""", unsafe_allow_html=True)

GOLD = Path(__file__).parent.parent/"data"/"gold"
PAL = ["#00c48c","#2196f3","#ff9800","#e91e63","#9c27b0","#00bcd4"]
CTC = {"AC_slow":"#4CAF50","AC_fast":"#2196F3","DC_rapid":"#FF9800","DC_ultra":"#E91E63"}
BASE = dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(10,22,40,0.6)",
    font=dict(color="#8aaccc",family="Inter",size=12),margin=dict(l=0,r=0,t=30,b=0))
AXS = dict(gridcolor="rgba(30,58,95,0.5)",linecolor="rgba(30,58,95,0.5)",tickfont=dict(color="#8aaccc"))

def layout(fig, h=300, **kw):
    fig.update_layout(**BASE, height=h, xaxis=AXS, yaxis=AXS, **kw)
def y2(color): return dict(overlaying="y",side="right",gridcolor="rgba(0,0,0,0)",linecolor="rgba(0,0,0,0)",tickfont=dict(color=color))
def kpi(col,icon,lbl,val,sub,clr): col.markdown(f'<div class="kpi"><div class="kpi-bar" style="background:{clr}"></div><div class="kpi-icon">{icon}</div><div class="kpi-lbl">{lbl}</div><div class="kpi-val">{val}</div><div class="kpi-sub">{sub}</div></div>',unsafe_allow_html=True)
def ins(body,title="💡 Insight"): st.markdown(f'<div class="ins"><div class="ins-t">{title}</div><div class="ins-b">{body}</div></div>',unsafe_allow_html=True)
def sec(t): st.markdown(f'<div class="sec">{t}</div>',unsafe_allow_html=True)

@st.cache_data
def load():
    tbls=["dim_charger","dim_location","dim_date","fact_sessions","fact_availability","gold_priority_scores"]
    d={t:pd.read_parquet(GOLD/f"{t}.parquet") if (GOLD/f"{t}.parquet").exists() else _fake(t) for t in tbls}
    if "month" not in d["fact_sessions"].columns:
        d["fact_sessions"]["month"]=d["fact_sessions"]["date_key"]%10000//100
    return d

def _fake(t):
    np.random.seed(42)
    if t=="dim_charger":
        n=500;tp=np.random.choice(["AC_slow","AC_fast","DC_rapid","DC_ultra"],n,p=[.35,.35,.20,.10])
        return pd.DataFrame({"charger_id":[f"CHR{i:05d}"for i in range(n)],"charger_type":tp,
            "power_kw":[{"AC_slow":7,"AC_fast":22,"DC_rapid":50,"DC_ultra":150}[x]for x in tp],
            "postcode":[f"BS{i%99} {i%9}AA"for i in range(n)],
            "local_authority":np.random.choice(["Bristol","South Gloucestershire","Bath & NE Somerset"],n),
            "site_type":np.random.choice(["Retail","Motorway","Residential","Workplace","Leisure"],n)})
    if t=="fact_sessions":
        n=60000;m=np.random.randint(1,13,n)
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
    if t=="fact_availability":
        n=10000
        return pd.DataFrame({"charger_id":[f"CHR{i:05d}"for i in np.random.randint(0,500,n)],
            "date_key":np.random.randint(20250101,20251231,n),
            "uptime_pct":np.clip(np.random.normal(92,5,n),0,100).round(1),
            "fault_type":np.random.choice([None,"network_timeout","payment_failure","connector_stuck","overheating","power_surge"],n,p=[.92,.016,.016,.016,.016,.016])})
    if t=="gold_priority_scores":
        n=99;sc=np.round(np.random.uniform(20,90,n),1)
        return pd.DataFrame({"postcode":[f"BS{i} 1AA"for i in range(n)],
            "ward_name":[f"Ward_{i%20}"for i in range(n)],
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

def main():
    data=load()
    mn={1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

    # SIDEBAR
    with st.sidebar:
        st.markdown('<div style="text-align:center;padding:28px 0 16px"><div style="font-size:44px;filter:drop-shadow(0 0 16px rgba(0,196,140,.6))">⚡</div><div style="color:#fff;font-size:20px;font-weight:900;margin-top:6px">VoltSight BI</div><div style="color:#3a6a8a;font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-top:4px">EV Infrastructure Analytics</div></div><div style="height:1px;background:linear-gradient(90deg,transparent,rgba(0,196,140,.3),transparent);margin:0 16px 16px"></div>',unsafe_allow_html=True)
        page=st.radio("",["📊  Network Overview","🗺️  Location Intelligence","🔧  Operations","📍  Expansion Planner"],label_visibility="collapsed")
        st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(30,58,95,.6),transparent);margin:12px 0"></div><div style="color:#3a6a8a;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;padding:0 2px">Filters</div>',unsafe_allow_html=True)
        ch=data["dim_charger"]
        las=sorted(ch["local_authority"].dropna().unique())
        sel_la=st.multiselect("Local Authority",las,default=las)
        tps=sorted(ch["charger_type"].unique())
        sel_tp=st.multiselect("Charger Type",tps,default=tps)
        mnths=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        sel_m=st.multiselect("Month",mnths,default=mnths)
        m_nums=[i+1 for i,m in enumerate(mnths) if m in sel_m]
        st.markdown('<div style="margin-top:20px;padding:12px;background:rgba(0,196,140,.05);border-radius:10px;border:1px solid rgba(0,196,140,.1)"><div style="color:#3a6a8a;font-size:10px;line-height:2">📋 UK National Chargepoint Registry<br>🔢 12-month simulation 2025<br>© VoltSight BI 2025</div></div>',unsafe_allow_html=True)

    # FILTER DATA
    chargers=ch.copy()
    if sel_la: chargers=chargers[chargers["local_authority"].isin(sel_la)]
    if sel_tp: chargers=chargers[chargers["charger_type"].isin(sel_tp)]
    cids=set(chargers["charger_id"])
    sess=data["fact_sessions"].copy()
    sess=sess[sess["charger_id"].isin(cids)]
    if m_nums: sess=sess[sess["month"].isin(m_nums)]
    avail=data["fact_availability"][data["fact_availability"]["charger_id"].isin(cids)].copy()
    comp=sess[sess["status"]=="completed"]
    faults=sess[sess["status"]=="fault"]

    # ── PAGE 1: NETWORK OVERVIEW ───────────────────────────────────────────
    if "Network Overview" in page:
        st.markdown('<div class="pg-t">Network Overview</div><div class="pg-s">UK EV Charging Network · Full Year 2025 · Live Performance Metrics</div>',unsafe_allow_html=True)
        c1,c2,c3,c4=st.columns(4)
        kpi(c1,"🔌","Total Chargers",f"{len(chargers):,}","Active on network","linear-gradient(90deg,#00c48c,#00e6a8)")
        kpi(c2,"⚡","Sessions",f"{len(comp):,}","Completed 2025","linear-gradient(90deg,#2196f3,#64b5f6)")
        kpi(c3,"💷","Revenue",f"£{comp['revenue_gbp'].sum():,.0f}","Generated 2025","linear-gradient(90deg,#ff9800,#ffb74d)")
        kpi(c4,"🌿","Energy",f"{comp['energy_kwh'].sum()/1000:,.0f} MWh",f"Avg {comp['duration_min'].mean():.0f} min/session","linear-gradient(90deg,#e91e63,#f48fb1)")
        st.markdown("<br>",unsafe_allow_html=True)

        col1,col2=st.columns([3,2])
        with col1:
            sec("📈 Monthly Performance — Sessions & Revenue")
            mo=comp.groupby("month").agg(sessions=("session_id","count"),revenue=("revenue_gbp","sum")).reset_index()
            mo["mn"]=mo["month"].map(mn)
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=mo["mn"],y=mo["sessions"],fill="tozeroy",fillcolor="rgba(0,196,140,.1)",line=dict(color="#00c48c",width=2.5,shape="spline"),mode="lines+markers",marker=dict(size=7,color="#00c48c",line=dict(width=2,color="#060d1a")),name="Sessions",hovertemplate="<b>%{x}</b><br>Sessions: %{y:,}<extra></extra>"))
            fig.add_trace(go.Bar(x=mo["mn"],y=mo["revenue"],marker=dict(color="rgba(33,150,243,.2)",line=dict(color="rgba(33,150,243,.4)",width=1)),yaxis="y2",name="Revenue £",hovertemplate="<b>%{x}</b><br>£%{y:,.0f}<extra></extra>"))
            layout(fig,280,yaxis2=y2("#2196f3"),legend=dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)",font=dict(color="#8aaccc")),hovermode="x unified")
            st.plotly_chart(fig,use_container_width=True)

        with col2:
            sec("🔌 Charger Type Split")
            tc=chargers["charger_type"].value_counts().reset_index()
            tc.columns=["type","count"]
            fig2=go.Figure(go.Pie(labels=tc["type"],values=tc["count"],hole=0.65,marker=dict(colors=[CTC.get(t,"#888")for t in tc["type"]],line=dict(color="#060d1a",width=3)),textinfo="percent",textfont=dict(color="white",size=11),hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>"))
            layout(fig2,280,legend=dict(orientation="h",y=-0.2,font=dict(color="#8aaccc",size=10)),annotations=[dict(text=f"<b>{len(chargers)}</b>",x=0.5,y=0.5,font=dict(size=22,color="white"),showarrow=False)])
            st.plotly_chart(fig2,use_container_width=True)

        col3,col4=st.columns(2)
        with col3:
            sec("⏰ Peak Hours")
            hr=comp.groupby("start_hour").size().reset_index(name="n")
            fig3=go.Figure(go.Bar(x=hr["start_hour"],y=hr["n"],marker=dict(color=["#00c48c"if h in[7,8,17,18,19]else"rgba(33,58,95,.7)"for h in hr["start_hour"]],line=dict(color="rgba(0,0,0,0)")),hovertemplate="<b>%{x}:00</b><br>%{y:,}<extra></extra>"))
            layout(fig3,240,xaxis=dict(**AXS,tickmode="linear",tick0=0,dtick=3),bargap=0.15)
            st.plotly_chart(fig3,use_container_width=True)

        with col4:
            sec("🏪 Revenue by Site Type")
            if "site_type" in chargers.columns:
                mg=sess.merge(chargers[["charger_id","site_type"]],on="charger_id",how="left")
                st_s=mg[mg["status"]=="completed"].groupby("site_type").agg(rev=("revenue_gbp","sum")).reset_index().sort_values("rev")
                fig4=go.Figure(go.Bar(x=st_s["rev"],y=st_s["site_type"],orientation="h",marker=dict(color=st_s["rev"],colorscale=[[0,"rgba(33,58,95,.5)"],[1,"#00c48c"]],line=dict(color="rgba(0,0,0,0)")),text=[f"£{v:,.0f}"for v in st_s["rev"]],textposition="outside",textfont=dict(color="#8aaccc",size=10),hovertemplate="<b>%{y}</b><br>£%{x:,.0f}<extra></extra>"))
                layout(fig4,240,xaxis=dict(**AXS,showgrid=False,showticklabels=False))
                st.plotly_chart(fig4,use_container_width=True)

        ph=comp.groupby("start_hour").size().idxmax()
        ins(f"Peak demand at <b>{ph}:00</b>. Network generated <b>£{comp['revenue_gbp'].sum():,.0f}</b> from <b>{len(comp):,}</b> sessions. Deploy DC Rapid units at peak-hour commuter hotspots.","💡 Network Intelligence")

    # ── PAGE 2: LOCATION ───────────────────────────────────────────────────
    elif "Location" in page:
        st.markdown('<div class="pg-t">Location Intelligence</div><div class="pg-s">Geographic distribution · Coverage gaps · Demand signals across the UK</div>',unsafe_allow_html=True)
        pr=data["gold_priority_scores"]
        las2=chargers["local_authority"].value_counts()
        c1,c2,c3=st.columns(3)
        kpi(c1,"🏛️","Areas Covered",str(chargers["local_authority"].nunique()),"Local authorities","linear-gradient(90deg,#00c48c,#00e6a8)")
        kpi(c2,"📍","Busiest Area",str(las2.index[0])if len(las2)else"N/A",f"{las2.iloc[0]:,} chargers"if len(las2)else"","linear-gradient(90deg,#2196f3,#64b5f6)")
        kpi(c3,"🚗","Avg EV Density",f"{int(pr['ev_registrations_nearby'].mean()):,}","EV registrations per zone","linear-gradient(90deg,#ff9800,#ffb74d)")
        st.markdown("<br>",unsafe_allow_html=True)

        col1,col2=st.columns([3,2])
        with col1:
            sec("🗺️ Site Priority Heatmap")
            if "latitude" in pr.columns:
                fig=px.scatter_mapbox(pr.sort_values("priority_score"),lat="latitude",lon="longitude",color="priority_score",size="ev_registrations_nearby",hover_name="postcode",hover_data={"priority_score":":.1f","ward_name":True,"road_type":True,"latitude":False,"longitude":False},color_continuous_scale=[[0,"#0d1f38"],[0.4,"#1565c0"],[1,"#00c48c"]],size_max=20,mapbox_style="carto-darkmatter",zoom=9.5,center={"lat":51.45,"lon":-2.58})
                fig.update_layout(**BASE,height=400,coloraxis_colorbar=dict(title=dict(text="Score",font=dict(color="#8aaccc")),tickfont=dict(color="#8aaccc")))
                st.plotly_chart(fig,use_container_width=True)
        with col2:
            sec("📊 EV Demand vs Priority")
            fig2=px.scatter(pr,x="ev_registrations_nearby",y="priority_score",color="road_type",size="population_density",hover_name="postcode",color_discrete_sequence=PAL,labels={"ev_registrations_nearby":"EV Registrations","priority_score":"Priority Score"})
            layout(fig2,400,legend=dict(orientation="h",y=-0.2,font=dict(color="#8aaccc",size=10),bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig2,use_container_width=True)

        sec("🏛️ Performance by Local Authority")
        la_s=comp.merge(chargers[["charger_id","local_authority"]],on="charger_id",how="left")
        la_g=la_s.groupby("local_authority").agg(sessions=("session_id","count"),revenue=("revenue_gbp","sum")).reset_index().sort_values("revenue",ascending=False)
        fig3=go.Figure()
        fig3.add_trace(go.Bar(name="Sessions",x=la_g["local_authority"],y=la_g["sessions"],marker=dict(color="rgba(0,196,140,.7)",line=dict(color="rgba(0,0,0,0)"))))
        fig3.add_trace(go.Scatter(name="Revenue £",x=la_g["local_authority"],y=la_g["revenue"],mode="lines+markers",line=dict(color="#ff9800",width=2.5,shape="spline"),marker=dict(size=9,color="#ff9800"),yaxis="y2"))
        layout(fig3,260,yaxis2=y2("#ff9800"),legend=dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)",font=dict(color="#8aaccc")))
        st.plotly_chart(fig3,use_container_width=True)
        if len(la_g): ins(f"<b>{la_g.iloc[0]['local_authority']}</b> leads with <b>£{la_g.iloc[0]['revenue']:,.0f}</b> from <b>{la_g.iloc[0]['sessions']:,}</b> sessions. Concentrate infrastructure investment here for maximum ROI.","📍 Location Insight")

    # ── PAGE 3: OPERATIONS ─────────────────────────────────────────────────
    elif "Operations" in page:
        st.markdown('<div class="pg-t">Operations & Reliability</div><div class="pg-s">Network health · Fault diagnostics · SLA performance tracking</div>',unsafe_allow_html=True)
        avg_up=avail["uptime_pct"].mean()
        b95=(avail.groupby("charger_id")["uptime_pct"].mean()<95).sum()
        fm=faults["fault_type"].dropna().mode()
        sla_clr="linear-gradient(90deg,#00c48c,#00e6a8)"if avg_up>=95 else"linear-gradient(90deg,#ff9800,#ffb74d)"
        c1,c2,c3,c4=st.columns(4)
        kpi(c1,"📡","Network Uptime",f"{avg_up:.1f}%","Target: 95% SLA",sla_clr)
        kpi(c2,"⚠️","Below SLA",str(int(b95)),"Chargers need attention","linear-gradient(90deg,#e91e63,#f48fb1)")
        kpi(c3,"🔴","Fault Incidents",f"{len(faults):,}","Recorded 2025","linear-gradient(90deg,#ff5722,#ff8a65)")
        kpi(c4,"🛠️","Primary Fault",fm[0].replace("_"," ").title()if len(fm)else"N/A","Most common","linear-gradient(90deg,#9c27b0,#ce93d8)")
        st.markdown("<br>",unsafe_allow_html=True)

        col1,col2=st.columns(2)
        with col1:
            sec("🔴 Fault Type Breakdown")
            fc=faults["fault_type"].dropna().value_counts().reset_index()
            fc.columns=["type","count"]
            fc["label"]=fc["type"].str.replace("_"," ").str.title()
            fig=go.Figure(go.Bar(x=fc["count"],y=fc["label"],orientation="h",marker=dict(color=fc["count"],colorscale=[[0,"rgba(33,58,95,.5)"],[1,"rgba(229,57,53,.8)"]],line=dict(color="rgba(0,0,0,0)")),text=[f"  {v:,}"for v in fc["count"]],textposition="outside",textfont=dict(color="#8aaccc",size=11),hovertemplate="<b>%{y}</b><br>%{x:,}<extra></extra>"))
            layout(fig,280,xaxis=dict(**AXS,showgrid=False,showticklabels=False))
            st.plotly_chart(fig,use_container_width=True)

        with col2:
            sec("📊 Uptime Distribution")
            fig2=go.Figure()
            fig2.add_trace(go.Histogram(x=avail["uptime_pct"],nbinsx=25,marker=dict(color="rgba(33,150,243,.6)",line=dict(color="rgba(33,150,243,.3)",width=1))))
            fig2.add_vline(x=95,line_dash="dash",line_color="#00c48c",line_width=1.5,annotation=dict(text="95% SLA",font=dict(color="#00c48c",size=11),bgcolor="rgba(0,0,0,0)"))
            fig2.add_vline(x=avg_up,line_dash="dot",line_color="#ff9800",line_width=1.5,annotation=dict(text=f"Avg {avg_up:.1f}%",font=dict(color="#ff9800",size=11),bgcolor="rgba(0,0,0,0)"))
            layout(fig2,280)
            st.plotly_chart(fig2,use_container_width=True)

        sec("📅 Monthly Fault Trend")
        mf=faults.groupby("month").size().reset_index(name="faults")
        mc_d=comp.groupby("month").size().reset_index(name="completed")
        mt=mf.merge(mc_d,on="month",how="outer").fillna(0)
        mt["fault_rate"]=(mt["faults"]/(mt["faults"]+mt["completed"])*100).round(1)
        mt["mn"]=mt["month"].map(mn)
        fig3=go.Figure()
        fig3.add_trace(go.Bar(x=mt["mn"],y=mt["faults"],name="Faults",marker=dict(color="rgba(229,57,53,.5)",line=dict(color="rgba(0,0,0,0)"))))
        fig3.add_trace(go.Scatter(x=mt["mn"],y=mt["fault_rate"],name="Fault Rate %",line=dict(color="#ff9800",width=2,shape="spline"),marker=dict(size=7,color="#ff9800"),yaxis="y2"))
        layout(fig3,250,yaxis2=y2("#ff9800"),legend=dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)",font=dict(color="#8aaccc")))
        st.plotly_chart(fig3,use_container_width=True)
        ins(f"Uptime <b>{avg_up:.1f}%</b> vs 95% SLA. <b>{int(b95)} chargers</b> below threshold. Lead fault: <b>{fm[0].replace('_',' ').title()if len(fm)else'N/A'}</b> — schedule preventative maintenance cycle.","🔧 Operations Insight")

    # ── PAGE 4: EXPANSION PLANNER ──────────────────────────────────────────
    elif "Expansion" in page:
        st.markdown('<div class="pg-t">Expansion Planner</div><div class="pg-s">AI-powered site ranking · Identify optimal locations for new EV charger deployment</div>',unsafe_allow_html=True)
        pr=data["gold_priority_scores"].copy()
        sec("⚙️ Priority Weight Configuration")
        st.markdown('<div style="color:#3a6a8a;font-size:12px;margin:-6px 0 14px">Adjust weights to reflect strategic priorities. Rankings update in real time.</div>',unsafe_allow_html=True)
        c1,c2,c3,c4,c5=st.columns(5)
        w1=c1.slider("🚗 EV Demand",0,100,30,5)
        w2=c2.slider("📉 Supply Gap",0,100,25,5)
        w3=c3.slider("🛣️ Road Access",0,100,20,5)
        w4=c4.slider("📡 Coverage",0,100,15,5)
        w5=c5.slider("⚡ Utilisation",0,100,10,5)
        tot=max(w1+w2+w3+w4+w5,1)
        if all(c in pr.columns for c in["score_demand","score_supply_gap"]):
            pr["score"]=((pr["score_demand"]*w1+pr["score_supply_gap"]*w2+pr["score_road_access"]*w3+pr["score_coverage"]*w4+pr["score_utilization"]*w5)/tot*100).round(1)
        else:
            pr["score"]=pr["priority_score"]
        pr=pr.sort_values("score",ascending=False).reset_index(drop=True)
        st.markdown("<br>",unsafe_allow_html=True)

        col1,col2=st.columns([3,2])
        with col1:
            sec("🏆 Top 10 Expansion Sites")
            t10=pr.head(10).copy()
            t10.index=range(1,11)
            disp=pd.DataFrame({"Rank":[f"#{i}"for i in range(1,11)],"Postcode":t10["postcode"].values,"Ward":t10["ward_name"].values,"Authority":t10["local_authority"].values,"Score":[f"{s:.1f}/100"for s in t10["score"].values],"EV Density":[f"{v:,}"for v in t10["ev_registrations_nearby"].values],"Road":t10["road_type"].values,"Gap km":[f"{v:.1f}"for v in t10["nearest_competitor_km"].values]})
            disp.index=range(1,11)
            st.dataframe(disp,use_container_width=True,height=360)
        with col2:
            sec("📊 Score Breakdown — #1 Site")
            t1=pr.iloc[0]
            if "score_demand" in t1.index:
                vals=[round(t1.get(f"score_{k}",0)*100,1)for k in["demand","supply_gap","road_access","coverage","utilization"]]
                fig=go.Figure(go.Bar(x=vals,y=["EV Demand","Supply Gap","Road Access","Coverage","Utilisation"],orientation="h",marker=dict(color=vals,colorscale=[[0,"rgba(33,58,95,.6)"],[1,"rgba(0,196,140,.8)"]],line=dict(color="rgba(0,0,0,0)")),text=[f"{v:.0f}"for v in vals],textposition="outside",textfont=dict(color="#8aaccc",size=12)))
                layout(fig,360,xaxis=dict(**AXS,showgrid=False,showticklabels=False,range=[0,max(vals)*1.3]))
                fig.update_layout(title=dict(text=f"<b>{t1['postcode']}</b> · {t1['score']:.1f}/100",font=dict(color="white",size=13)))
                st.plotly_chart(fig,use_container_width=True)

        ins(f"Top site: <b>{pr.iloc[0]['postcode']}</b> ({pr.iloc[0]['ward_name']}) — score <b>{pr.iloc[0]['score']:.1f}/100</b>. <b>{pr.iloc[0]['ev_registrations_nearby']:,} EVs</b> in catchment, nearest competitor <b>{pr.iloc[0]['nearest_competitor_km']:.1f} km</b>. Recommended: <b>DC Rapid 50kW dual CCS</b>.","🤖 AI Site Recommendation")

if __name__=="__main__":
    main()
