<div align="center">

# ⚡ VoltSight BI

### EV Charging Infrastructure Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-6.7+-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![License](https://img.shields.io/badge/License-MIT-00C48C?style=for-the-badge)](LICENSE)

**"Where should the next EV charger be installed — and which sites need fixing first?"**

[📊 Live Dashboard](https://voltsight-bi.streamlit.app) · [📖 Documentation](#documentation) · [🚀 Quick Start](#quick-start)

</div>

---

## 📌 Project Overview

VoltSight BI is a **production-grade business intelligence platform** for EV charging infrastructure analytics. Built on a **Medallion Architecture** (Bronze → Silver → Gold), it transforms raw UK chargepoint registry data into actionable insights via an interactive Streamlit dashboard.

**Core business question:** *Given 52,847 UK charger locations, 618,000+ simulated sessions, and real demographic data — where should operators invest next, and which existing sites need immediate attention?*

---

## 🏗️ Architecture

```
External Sources
      │
      ▼
┌─────────────────┐
│  BRONZE LAYER   │  Raw ingestion · SHA256 integrity · Manifest logging
│  (Immutable)    │  Source: UK National Chargepoint Registry (DfT)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SILVER LAYER   │  Cleaning · Geo-enrichment · Feature engineering
│  (Validated)    │  Postcode → Ward/LSOA · EV adoption signals
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   GOLD LAYER    │  Star schema · KPIs · Site Priority Score
│  (Analytical)   │  618,223 sessions · 182,500 availability records
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    DASHBOARD    │  4-page Streamlit app · Live filters · AI insights
│  (Serve Layer)  │  Dark theme · Plotly charts · Interactive sliders
└─────────────────┘
```

---

## 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| **⚡ Network Overview** | KPI cards, monthly sessions trend, peak hour heatmap, site type revenue |
| **🗺️ Location Intelligence** | Priority score map, EV demand vs supply scatter, local authority breakdown |
| **🔧 Operations & Reliability** | Network uptime %, fault type analysis, SLA tracking, monthly fault trend |
| **📍 Expansion Planner** | Adjustable priority weights, ranked site recommendations, score breakdown |

---

## 🎯 Site Priority Score

The core analytical model ranks locations for new charger installation:

```
Score = Demand(0.30) + Supply Gap(0.25) + Road Access(0.20)
      + Coverage Deficit(0.15) + Utilisation Signal(0.10)
```

| Component | Weight | Signal |
|-----------|--------|--------|
| EV Demand | 30% | EV registrations + population density |
| Supply Gap | 25% | Chargers per EV (lower = bigger gap) |
| Road Access | 20% | Road type + competitor proximity |
| Coverage Deficit | 15% | Distance to nearest charger |
| Utilisation | 10% | Existing charger occupancy |

Weights are **fully adjustable** via dashboard sliders — enabling operators to align recommendations with business strategy in real time.

---

## 📁 Project Structure

```
voltsight-bi/
├── dashboard/
│   ├── app.py                  # Streamlit dashboard (4 pages)
│   └── requirements.txt        # Dashboard dependencies
├── src/voltsight/
│   ├── bronze/
│   │   ├── ingest.py           # Retry-wrapped data ingestion
│   │   └── validate.py         # Quality checks
│   ├── silver/
│   │   └── transform.py        # Cleaning + geo-enrichment
│   └── gold/
│       ├── simulate.py         # 12-month session simulation
│       └── priority_score.py   # Site Priority Score logic
├── scripts/
│   ├── ingest_bronze.py        # Run bronze ingestion
│   ├── transform_to_silver.py  # Run silver transformation
│   ├── build_gold.py           # Build star schema + KPIs
│   ├── validate_bronze.py      # Validate bronze layer
│   ├── validate_silver.py      # Validate silver layer
│   └── validate_gold.py        # Validate gold layer
├── sql/
│   └── kpi_queries.sql         # Power BI-compatible KPI queries
├── docs/
│   ├── BRONZE_LAYER.md
│   ├── SILVER_LAYER.md
│   └── GOLD_LAYER.md
├── tests/
│   └── test_bronze.py          # 9 unit tests
├── .streamlit/
│   └── config.toml             # Dark theme configuration
├── config/
│   └── sources.yaml            # External data source config
└── requirements.txt            # Root dependencies
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/mdonikmia/voltsight-bi.git
cd voltsight-bi

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Run the Pipeline

```bash
# Step 1: Ingest Bronze layer
python scripts/ingest_bronze.py

# Step 2: Transform to Silver
python scripts/transform_to_silver.py

# Step 3: Build Gold layer (star schema + KPIs)
python scripts/build_gold.py

# Step 4: Launch Dashboard
python -m streamlit run dashboard/app.py
```

### Or use the one-click launcher (Windows)

```bash
run_dashboard.bat
```

---

## 🔢 Data Scale

| Layer | Records | Description |
|-------|---------|-------------|
| Bronze | 52,847 | Raw UK charger locations (National Chargepoint Registry) |
| Silver | 52,847 | Cleaned + geo-enriched + feature-engineered |
| DIM_CHARGER | 500 | Charger dimension (type, power, location) |
| DIM_LOCATION | 99 | Location dimension (demographics, competition) |
| DIM_DATE | 365 | Calendar dimension (weekday, peak, season) |
| FACT_SESSIONS | 618,223 | Simulated charging sessions (2025) |
| FACT_AVAILABILITY | 182,500 | Daily uptime records |
| PRIORITY_SCORES | 99 | Ranked expansion recommendations |

---

## 🛠️ Engineering Highlights

- **Idempotent ingestion** — skip if today's file already exists
- **SHA256 hashing** — file integrity verification on every pull
- **Tenacity retry logic** — exponential backoff for HTTP requests
- **Fail-soft pipeline** — one source failing doesn't block others
- **Structured logging** — timestamped, levelled logs (not print statements)
- **External YAML config** — URLs/sources not hardcoded
- **Parquet + CSV** — both formats for performance and human readability
- **Data lineage manifest** — tracks source, timestamp, row count per file
- **9 unit tests** — covering ingestion, validation, and schema checks

---

## 📈 Key KPIs

```sql
-- Average network uptime
SELECT AVG(uptime_pct) FROM fact_availability;  -- Target: ≥95%

-- Revenue by charger type
SELECT charger_type, SUM(revenue_gbp)
FROM fact_sessions JOIN dim_charger USING (charger_id)
WHERE status = 'completed'
GROUP BY charger_type;

-- Top expansion sites
SELECT postcode, priority_score, priority_rank
FROM gold_priority_scores
ORDER BY priority_rank LIMIT 10;
```

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13 |
| Dashboard | Streamlit + Plotly |
| Data Processing | Pandas, PyArrow |
| Storage | Parquet (fast) + CSV (readable) |
| HTTP | Requests + Tenacity |
| Config | PyYAML |
| Testing | Pytest |
| Version Control | Git + GitHub |
| Deployment | Streamlit Cloud |

---

## 📚 Documentation

- [Bronze Layer](docs/BRONZE_LAYER.md) — Raw ingestion design
- [Silver Layer](docs/SILVER_LAYER.md) — Cleaning and enrichment
- [Gold Layer](docs/GOLD_LAYER.md) — Star schema and KPI definitions

---

## 👤 Author

**MD Onik Mia**
BSc Information Technology (Hons), University of the West of England Bristol, 2026

Specialising in data analytics, machine learning, and cybersecurity.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/md-onik-mia-643322385/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github)](https://github.com/mdonikmia)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=flat&logo=gmail)](mailto:mdonikmia88@gmail.com)

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">
<sub>Built with ⚡ and Python · VoltSight BI 2025</sub>
</div>
