-- ============================================================
-- VoltSight BI — KPI SQL Queries
-- Compatible with: SQLite, PostgreSQL, DuckDB
-- Use these in Power BI (DirectQuery or import)
-- ============================================================


-- ── KPI 1: Network Overview ────────────────────────────────

-- Total chargers by type
SELECT
    charger_type,
    COUNT(*)            AS total_chargers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_network
FROM dim_charger
GROUP BY charger_type
ORDER BY total_chargers DESC;


-- Total sessions and revenue (all time)
SELECT
    COUNT(*)                        AS total_sessions,
    ROUND(SUM(energy_kwh), 0)       AS total_energy_kwh,
    ROUND(SUM(revenue_gbp), 2)      AS total_revenue_gbp,
    ROUND(AVG(duration_min), 1)     AS avg_session_min
FROM fact_sessions
WHERE status = 'completed';


-- Monthly sessions trend
SELECT
    d.month_name,
    d.month,
    COUNT(s.session_id)             AS sessions,
    ROUND(SUM(s.revenue_gbp), 2)    AS revenue_gbp
FROM fact_sessions s
JOIN dim_date d ON s.date_key = d.date_key
WHERE s.status = 'completed'
GROUP BY d.month, d.month_name
ORDER BY d.month;


-- ── KPI 2: Charger Utilization ─────────────────────────────

-- Average sessions per charger per day
SELECT
    c.charger_type,
    ROUND(
        COUNT(s.session_id) * 1.0
        / COUNT(DISTINCT c.charger_id)
        / 365, 2
    ) AS avg_sessions_per_day
FROM dim_charger c
LEFT JOIN fact_sessions s ON c.charger_id = s.charger_id
    AND s.status = 'completed'
GROUP BY c.charger_type;


-- Peak hour demand (sessions by hour)
SELECT
    start_hour,
    COUNT(*)    AS sessions,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_sessions
FROM fact_sessions
WHERE status = 'completed'
GROUP BY start_hour
ORDER BY start_hour;


-- ── KPI 3: Uptime & Reliability ────────────────────────────

-- Network-wide uptime %
SELECT
    ROUND(AVG(uptime_pct), 2)   AS avg_uptime_pct,
    MIN(uptime_pct)             AS min_uptime_pct,
    COUNT(CASE WHEN uptime_pct < 95 THEN 1 END) AS days_below_95pct
FROM fact_availability;


-- Fault breakdown by type
SELECT
    fault_type,
    COUNT(*)    AS fault_incidents,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM fact_sessions
WHERE status = 'fault'
    AND fault_type IS NOT NULL
GROUP BY fault_type
ORDER BY fault_incidents DESC;


-- Worst performing chargers (lowest uptime)
SELECT
    a.charger_id,
    c.charger_type,
    c.postcode,
    ROUND(AVG(a.uptime_pct), 1) AS avg_uptime_pct
FROM fact_availability a
JOIN dim_charger c ON a.charger_id = c.charger_id
GROUP BY a.charger_id, c.charger_type, c.postcode
ORDER BY avg_uptime_pct ASC
LIMIT 20;


-- ── KPI 4: Location Intelligence ───────────────────────────

-- Sessions by local authority
SELECT
    c.local_authority,
    COUNT(s.session_id)             AS sessions,
    ROUND(SUM(s.revenue_gbp), 2)    AS revenue_gbp,
    ROUND(AVG(s.energy_kwh), 2)     AS avg_energy_kwh
FROM fact_sessions s
JOIN dim_charger c ON s.charger_id = c.charger_id
WHERE s.status = 'completed'
GROUP BY c.local_authority
ORDER BY sessions DESC;


-- ── KPI 5: Site Priority Score ─────────────────────────────

-- Top 10 locations for new charger installation
SELECT
    postcode,
    ward_name,
    local_authority,
    ROUND(priority_score, 1)        AS priority_score,
    priority_rank,
    ev_registrations_nearby,
    population_density,
    road_type,
    ROUND(nearest_competitor_km, 1) AS nearest_competitor_km
FROM gold_priority_scores
ORDER BY priority_rank
LIMIT 10;


-- Score breakdown for top locations
SELECT
    postcode,
    ROUND(score_demand * 100, 1)        AS demand_score,
    ROUND(score_supply_gap * 100, 1)    AS supply_gap_score,
    ROUND(score_road_access * 100, 1)   AS road_access_score,
    ROUND(score_coverage * 100, 1)      AS coverage_score,
    ROUND(score_utilization * 100, 1)   AS utilization_score,
    ROUND(priority_score, 1)            AS total_score
FROM gold_priority_scores
ORDER BY priority_score DESC
LIMIT 10;
