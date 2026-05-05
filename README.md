# VoltSight BI

> **Intelligent planning of EV charging infrastructure.**
>
> A business intelligence system that helps network operators and city planners decide where to install the next charger, what type it should be, and which existing sites need urgent attention.

---

## The Question VoltSight Answers

> *Where should the next EV charger be installed, what type should it be, and which existing sites are failing first?*

Every layer of this system exists to answer that question.

---

## Architecture (Medallion Pattern)

```
External sources  →  Bronze (raw)  →  Silver (clean)  →  Gold (modelled)  →  Power BI + Claude AI
```

| Layer | Purpose | Status |
|---|---|---|
| **Bronze** | Immutable raw ingestion with provenance | ✅ Complete |
| **Silver** | Cleaned, deduplicated, geo-enriched | ✅ Complete |
| **Gold** | Star schema with KPIs and Site Priority Score | ✅ Complete |
| **Serve** | Power BI dashboard + Claude AI insights layer | ⏳ Planned |

---

## Tech Stack

- **Python 3.10+** — ingestion, transformation, simulation
- **Pandas + PyArrow** — data handling and parquet I/O
- **GeoPandas + Shapely** — geospatial enrichment
- **Tenacity** — production-grade retry logic
- **PyYAML** — externalised configuration
- **Pytest** — automated quality checks
- **Power BI** — visualisation (4-page dashboard)
- **Streamlit + Anthropic API** — natural-language insights layer
- **SQL** (SQLite for portfolio; PostgreSQL-compatible) — Gold layer queries

---

## Repository Structure

```
voltsight-bi/
├── config/
│   └── sources.yaml             # All external data sources defined here
├── src/voltsight/               # Importable Python package
│   ├── config.py                # Typed config loader
│   ├── logger.py                # Structured logging
│   ├── http_client.py           # Retry-wrapped downloads
│   ├── manifest.py              # Data lineage records
│   └── bronze/
│       ├── ingest.py            # Bronze ingestion logic
│       └── validate.py          # Bronze quality checks
├── scripts/
│   ├── ingest_bronze.py         # Run: download all Bronze sources
│   └── validate_bronze.py       # Run: quality-check all Bronze sources
├── tests/
│   └── test_bronze.py           # Unit tests for Bronze logic
├── docs/
│   └── BRONZE_LAYER.md          # Detailed docs per layer
├── data/
│   └── bronze/                  # (Gitignored — created by ingestion)
├── requirements.txt
├── .gitignore
└── README.md                    # This file
```

---

## Running the Bronze Layer

```bash
# 1. Install dependencies (preferably in a virtual environment)
python -m venv .venv
source .venv/bin/activate          # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Ingest all configured sources
python scripts/ingest_bronze.py

# 3. Validate the ingested data
python scripts/validate_bronze.py

# 4. Run tests
pytest tests/ -v
```

Output appears under `data/bronze/<source_key>/` with both CSV and Parquet copies plus a `_manifest.json` lineage record.

See [`docs/BRONZE_LAYER.md`](docs/BRONZE_LAYER.md) for the engineering rationale behind every decision in this layer.

---

## Engineering Standards

This project follows production-grade practices, not student-grade ones:

- **Type-hinted Python** throughout (`from __future__ import annotations`)
- **Structured logging** rather than print statements
- **External configuration** via YAML — no hardcoded URLs or paths
- **Retry-with-backoff** for all network operations (`tenacity`)
- **SHA256 file hashing** for data integrity verification
- **Idempotent operations** — safe to re-run without side effects
- **Fail-soft** error handling — one source failing does not block others
- **Unit tests** with pytest — focused on pure logic
- **Manifest files** for every dataset — full data lineage

---

## Roadmap

- [x] **Part 1** — Bronze layer (raw ingestion + validation)
- [ ] **Part 2** — Silver layer (cleaning + geo-enrichment)
- [ ] **Part 3** — Simulation script (12 months of session data)
- [ ] **Part 4** — Gold layer (star schema in SQL)
- [ ] **Part 5** — KPI queries (uptime, utilization, congestion, revenue)
- [ ] **Part 6** — Site Priority Score model
- [ ] **Part 7** — Power BI dashboard (4 pages, DAX)
- [ ] **Part 8** — Claude AI insights layer (Streamlit app)
- [ ] **Part 9** — Documentation, executive summary, Loom walkthrough

---

## Author

**MD Onik Mia** — BSc (Hons) Information Technology, University of the West of England, Bristol (2026)
Specialising in data analytics, machine learning, and cybersecurity.
Eligible for the UK Graduate Route visa (2 years, no sponsorship needed).

📫 mdonikmia88@gmail.com
🔗 [GitHub](https://github.com/mdonikmia)
💼 [LinkedIn](https://www.linkedin.com/in/md-onik-mia-643322385/)

---

## License

Code: MIT.
External data sources retain their original licenses (Open Government Licence v3.0 for UK government data).

---

## Gold Layer — Star Schema

| Table | Rows | Description |
|---|---|---|
| `dim_charger` | 500 | Charger attributes (type, power, location) |
| `dim_location` | 99 | Location enrichment (population, EV registrations) |
| `dim_date` | 365 | Calendar dimension (weekday, peak hours, season) |
| `fact_sessions` | 618,223 | Simulated charging sessions (12 months) |
| `fact_availability` | 182,500 | Daily charger uptime records |
| `gold_priority_scores` | 99 | **Site Priority Scores** — ranked expansion targets |

### Site Priority Score Formula
```
Score = demand(0.30) + supply_gap(0.25) + road_access(0.20)
      + coverage_deficit(0.15) + utilization(0.10)
```
