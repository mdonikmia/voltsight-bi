# Gold Layer — Star Schema, KPIs & Site Priority Score

The **Gold layer** is the analytics-ready layer. It contains the star schema tables that Power BI connects to, plus the Site Priority Score that drives the business recommendation.

---

## Star Schema Design

```
                    DIM_DATE
                       │
DIM_LOCATION ──── FACT_SESSIONS ──── DIM_CHARGER
                       │
                 FACT_AVAILABILITY
```

---

## Tables

### DIM_CHARGER
| Column | Type | Description |
|---|---|---|
| charger_id | string | Unique charger ID (CHR00001) |
| charger_type | string | AC_slow / AC_fast / DC_rapid / DC_ultra |
| power_kw | int | Rated power output |
| connector_type | string | Type2 / CCS |
| site_type | string | retail / motorway / residential / workplace |
| installation_date | date | When installed |
| latitude | float | GPS coordinate |
| longitude | float | GPS coordinate |
| postcode | string | UK postcode |
| ward_name | string | Electoral ward |
| local_authority | string | Council area |

### DIM_LOCATION
| Column | Type | Description |
|---|---|---|
| location_id | string | Unique location ID |
| postcode | string | UK postcode |
| ward_name | string | Electoral ward |
| lsoa_code | string | ONS LSOA code |
| population_density | int | Residents per km² |
| ev_registrations_nearby | int | EVs registered in area |
| nearest_competitor_km | float | Distance to nearest competitor |
| road_type | string | motorway / A_road / B_road / urban |

### DIM_DATE
| Column | Type | Description |
|---|---|---|
| date_key | int | YYYYMMDD format |
| date | date | Calendar date |
| day_of_week | string | Monday–Sunday |
| month | int | 1–12 |
| quarter | int | 1–4 |
| is_weekend | bool | Saturday or Sunday? |
| is_peak_season | bool | Nov–Feb (higher EV demand) |

### FACT_SESSIONS
| Column | Type | Description |
|---|---|---|
| session_id | string | Unique session ID |
| charger_id | string | FK → DIM_CHARGER |
| postcode | string | FK → DIM_LOCATION |
| date_key | int | FK → DIM_DATE |
| start_hour | int | Hour of day (0–23) |
| duration_min | int | Session length in minutes |
| energy_kwh | float | Energy delivered |
| revenue_gbp | float | Revenue earned (£) |
| status | string | completed / fault |
| fault_type | string | null if completed |

### FACT_AVAILABILITY
| Column | Type | Description |
|---|---|---|
| charger_id | string | FK → DIM_CHARGER |
| date_key | int | FK → DIM_DATE |
| hours_available | int | Hours operational |
| hours_in_fault | int | Hours in fault |
| uptime_pct | float | % uptime (target: ≥95%) |
| fault_type | string | null if no fault |

---

## Site Priority Score

### Formula
```
Score = demand(0.30) + supply_gap(0.25) + road_access(0.20)
      + coverage_deficit(0.15) + utilization(0.10)
```

### Components (all normalized 0–1)

| Component | Weight | What It Measures |
|---|---|---|
| **Demand** | 30% | EV registrations + population density |
| **Supply Gap** | 25% | Chargers per EV (lower = bigger gap) |
| **Road Access** | 20% | Road type + competitor proximity |
| **Coverage Deficit** | 15% | Distance to nearest charger |
| **Utilization** | 10% | Are existing chargers busy here? |

### Output
- Score: 0–100 (higher = install next charger here)
- Rank: 1 = highest priority location

---

## Key KPIs (for Power BI)

```sql
-- Average uptime % across all chargers
SELECT AVG(uptime_pct) FROM fact_availability;

-- Revenue by charger type
SELECT c.charger_type, SUM(s.revenue_gbp)
FROM fact_sessions s
JOIN dim_charger c ON s.charger_id = c.charger_id
GROUP BY c.charger_type;

-- Sessions by hour (peak demand)
SELECT start_hour, COUNT(*) as sessions
FROM fact_sessions
WHERE status = 'completed'
GROUP BY start_hour ORDER BY start_hour;
```

---

## Next: Power BI Dashboard (Part 4)

Gold → Power BI adds:
- 4-page interactive dashboard
- DAX measures for KPIs
- Map visualisations
- Expansion Planner with adjustable weights
