"""
Session data simulator for VoltSight BI.

Generates 12 months of realistic EV charging session data
based on real-world patterns:

  - Peak hours: 07:00-09:00 and 17:00-20:00
  - Weekend vs weekday usage differences
  - Charger type affects session duration + energy
  - Random faults (realistic uptime ~92%)
  - Seasonal variation (more charging in winter)

This simulated data feeds the Gold layer star schema.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from voltsight.logger import get_logger

log = get_logger(__name__)

# ── Simulation parameters ──────────────────────────────────────────────────

CHARGER_TYPES = {
    "AC_slow":  {"power_kw": 7,   "avg_duration_min": 180, "connector": "Type2"},
    "AC_fast":  {"power_kw": 22,  "avg_duration_min": 90,  "connector": "Type2"},
    "DC_rapid": {"power_kw": 50,  "avg_duration_min": 40,  "connector": "CCS"},
    "DC_ultra": {"power_kw": 150, "avg_duration_min": 25,  "connector": "CCS"},
}

FAULT_TYPES = [
    "network_timeout",
    "payment_failure",
    "connector_stuck",
    "overheating",
    "power_surge",
]

# Peak hour multipliers (0–23 hours)
HOUR_WEIGHTS = [
    0.3, 0.2, 0.1, 0.1, 0.2, 0.5,   # 00-05
    0.8, 1.5, 1.8, 1.2, 1.0, 1.1,   # 06-11
    1.2, 1.0, 0.9, 1.0, 1.3, 1.8,   # 12-17
    2.0, 1.9, 1.5, 1.1, 0.7, 0.4,   # 18-23
]

# Monthly demand multipliers (Jan-Dec)
MONTHLY_WEIGHTS = [
    1.2, 1.1, 1.0, 0.9, 0.85, 0.8,   # Jan-Jun (higher in winter)
    0.8, 0.8, 0.9, 1.0, 1.1, 1.2,   # Jul-Dec
]


# ── Dimension builders ─────────────────────────────────────────────────────

def build_dim_charger(silver_df: pd.DataFrame, n_chargers: int = 500) -> pd.DataFrame:
    """
    Build DIM_CHARGER dimension table.

    Samples from Silver charger data and assigns:
      - Charger type (AC slow/fast, DC rapid/ultra)
      - Power rating (kW)
      - Installation date
      - Site type (retail, motorway, residential, etc.)
    """
    log.info(f"Building DIM_CHARGER with {n_chargers} chargers")

    np.random.seed(42)
    sample = silver_df.sample(n=min(n_chargers, len(silver_df)), random_state=42).copy()
    sample = sample.reset_index(drop=True)

    charger_type_choices = list(CHARGER_TYPES.keys())
    charger_type_weights = [0.35, 0.35, 0.20, 0.10]  # AC_slow most common

    sample["charger_id"] = [f"CHR{i:05d}" for i in range(len(sample))]
    sample["charger_type"] = np.random.choice(
        charger_type_choices, size=len(sample), p=charger_type_weights
    )
    sample["power_kw"] = sample["charger_type"].map(
        {k: v["power_kw"] for k, v in CHARGER_TYPES.items()}
    )
    sample["connector_type"] = sample["charger_type"].map(
        {k: v["connector"] for k, v in CHARGER_TYPES.items()}
    )

    site_types = ["retail", "motorway_services", "residential", "workplace", "leisure"]
    site_weights = [0.30, 0.15, 0.25, 0.20, 0.10]
    sample["site_type"] = np.random.choice(site_types, size=len(sample), p=site_weights)

    # Installation date: random within last 5 years
    base_date = datetime(2021, 1, 1)
    sample["installation_date"] = [
        (base_date + timedelta(days=int(np.random.uniform(0, 365 * 5)))).date()
        for _ in range(len(sample))
    ]

    dim_charger = sample[[
        "charger_id", "charger_type", "power_kw", "connector_type",
        "site_type", "installation_date", "latitude", "longitude",
        "postcode", "ward_name", "lsoa_code", "local_authority",
    ]].copy()

    log.info(f"DIM_CHARGER: {len(dim_charger)} rows")
    return dim_charger


def build_dim_location(dim_charger: pd.DataFrame) -> pd.DataFrame:
    """
    Build DIM_LOCATION dimension table.

    Derives unique locations from charger data + enrichment.
    """
    log.info("Building DIM_LOCATION")

    np.random.seed(99)

    locations = dim_charger[[
        "postcode", "ward_name", "lsoa_code", "local_authority",
        "latitude", "longitude",
    ]].drop_duplicates(subset=["postcode"]).copy()

    locations = locations.reset_index(drop=True)
    locations["location_id"] = [f"LOC{i:05d}" for i in range(len(locations))]

    locations["population_density"] = np.random.randint(500, 8000, size=len(locations))
    locations["ev_registrations_nearby"] = np.random.randint(50, 2000, size=len(locations))
    locations["nearest_competitor_km"] = np.round(
        np.random.uniform(0.1, 15.0, size=len(locations)), 2
    )
    locations["road_type"] = np.random.choice(
        ["motorway", "A_road", "B_road", "urban"], size=len(locations),
        p=[0.1, 0.3, 0.2, 0.4]
    )

    log.info(f"DIM_LOCATION: {len(locations)} rows")
    return locations


def build_dim_date(start_date: str = "2025-01-01", end_date: str = "2025-12-31") -> pd.DataFrame:
    """
    Build DIM_DATE dimension table.

    One row per day with calendar attributes.
    """
    log.info(f"Building DIM_DATE from {start_date} to {end_date}")

    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    dim_date = pd.DataFrame({"date": dates})

    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["day_of_week"] = dim_date["date"].dt.day_name()
    dim_date["day_number"] = dim_date["date"].dt.dayofweek   # 0=Mon
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5
    dim_date["is_peak_season"] = dim_date["month"].isin([11, 12, 1, 2])

    log.info(f"DIM_DATE: {len(dim_date)} rows")
    return dim_date


# ── Fact table builder ─────────────────────────────────────────────────────

def build_fact_sessions(
    dim_charger: pd.DataFrame,
    dim_date: pd.DataFrame,
    sessions_per_charger_per_day: float = 3.5,
) -> pd.DataFrame:
    """
    Build FACT_SESSIONS — the core analytical fact table.

    Simulates realistic charging sessions with:
      - Peak hour weighting (morning/evening rush)
      - Charger-type-appropriate duration and energy
      - Seasonal demand variation
      - Random faults (uptime ~92%)
      - Revenue calculation (£0.30-£0.45/kWh)
    """
    log.info("Building FACT_SESSIONS (this may take 30-60 seconds)...")

    np.random.seed(123)
    random.seed(123)

    sessions = []
    session_id = 1

    charger_ids = dim_charger["charger_id"].tolist()
    charger_type_map = dim_charger.set_index("charger_id")["charger_type"].to_dict()
    charger_location_map = dim_charger.set_index("charger_id")["postcode"].to_dict()

    dates = pd.to_datetime(dim_date["date"].values)
    date_keys = dim_date.set_index(
        dim_date["date"].dt.strftime("%Y-%m-%d")
    )["date_key"].to_dict()

    for date in dates:
        month_idx = date.month - 1
        month_mult = MONTHLY_WEIGHTS[month_idx]
        is_weekend = date.weekday() >= 5

        for charger_id in charger_ids:
            # Is this charger in fault today? (~8% fault rate)
            in_fault = np.random.random() < 0.08

            # Daily sessions for this charger
            daily_sessions = int(np.random.poisson(
                sessions_per_charger_per_day * month_mult * (1.2 if is_weekend else 1.0)
            ))

            if in_fault:
                # Charger in fault — log availability record, skip sessions
                sessions.append({
                    "session_id": f"S{session_id:08d}",
                    "charger_id": charger_id,
                    "postcode": charger_location_map[charger_id],
                    "date_key": date_keys[date.strftime("%Y-%m-%d")],
                    "start_hour": 0,
                    "duration_min": 0,
                    "energy_kwh": 0.0,
                    "revenue_gbp": 0.0,
                    "status": "fault",
                    "fault_type": random.choice(FAULT_TYPES),
                })
                session_id += 1
                continue

            for _ in range(daily_sessions):
                # Pick hour weighted by peak hours
                hour = np.random.choice(24, p=np.array(HOUR_WEIGHTS) / sum(HOUR_WEIGHTS))

                charger_type = charger_type_map[charger_id]
                type_params = CHARGER_TYPES[charger_type]

                # Duration: normal distribution around type average
                duration = max(5, int(np.random.normal(
                    type_params["avg_duration_min"],
                    type_params["avg_duration_min"] * 0.25
                )))

                # Energy: power * time (with charging efficiency ~85%)
                energy = round(
                    type_params["power_kw"] * (duration / 60) * np.random.uniform(0.75, 0.95),
                    2
                )

                # Revenue: £0.30–0.45/kWh depending on charger type
                rate = 0.30 if "slow" in charger_type else (
                    0.35 if "fast" in charger_type else 0.45
                )
                revenue = round(energy * rate * np.random.uniform(0.95, 1.05), 2)

                sessions.append({
                    "session_id": f"S{session_id:08d}",
                    "charger_id": charger_id,
                    "postcode": charger_location_map[charger_id],
                    "date_key": date_keys[date.strftime("%Y-%m-%d")],
                    "start_hour": int(hour),
                    "duration_min": duration,
                    "energy_kwh": energy,
                    "revenue_gbp": revenue,
                    "status": "completed",
                    "fault_type": None,
                })
                session_id += 1

    fact_sessions = pd.DataFrame(sessions)
    log.info(f"FACT_SESSIONS: {len(fact_sessions):,} rows")
    return fact_sessions


# ── Availability fact builder ──────────────────────────────────────────────

def build_fact_availability(
    fact_sessions: pd.DataFrame,
    dim_charger: pd.DataFrame,
    dim_date: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build FACT_AVAILABILITY — daily charger uptime summary.

    Aggregates session data to compute:
      - hours_available per day
      - hours_in_fault per day
      - uptime_pct
      - fault_type (if applicable)
    """
    log.info("Building FACT_AVAILABILITY")

    charger_ids = dim_charger["charger_id"].tolist()
    date_keys = dim_date["date_key"].tolist()

    # Fault sessions
    fault_sessions = fact_sessions[fact_sessions["status"] == "fault"][[
        "charger_id", "date_key", "fault_type"
    ]]

    avail_records = []
    fault_lookup = fault_sessions.set_index(["charger_id", "date_key"])["fault_type"].to_dict()

    for date_key in date_keys:
        for charger_id in charger_ids:
            in_fault = (charger_id, date_key) in fault_lookup
            hours_in_fault = 24 if in_fault else 0
            hours_available = 24 - hours_in_fault
            uptime_pct = round(hours_available / 24 * 100, 1)

            avail_records.append({
                "charger_id": charger_id,
                "date_key": date_key,
                "hours_available": hours_available,
                "hours_in_fault": hours_in_fault,
                "uptime_pct": uptime_pct,
                "fault_type": fault_lookup.get((charger_id, date_key)),
            })

    fact_availability = pd.DataFrame(avail_records)
    log.info(f"FACT_AVAILABILITY: {len(fact_availability):,} rows")
    return fact_availability
