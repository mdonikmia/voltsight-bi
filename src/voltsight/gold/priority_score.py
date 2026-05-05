"""
Site Priority Score — VoltSight BI core business logic.

Formula:
    Score = demand(0.30) + supply_gap(0.25) + road_access(0.20)
          + coverage_deficit(0.15) + utilization_signal(0.10)

Each component is normalized to 0–1 before weighting.
Final score is 0–100 (higher = higher priority for new charger).

This is what turns raw data into a business recommendation:
"Install the next charger HERE."
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from voltsight.logger import get_logger

log = get_logger(__name__)

# ── Weights ────────────────────────────────────────────────────────────────

WEIGHTS = {
    "demand":            0.30,
    "supply_gap":        0.25,
    "road_access":       0.20,
    "coverage_deficit":  0.15,
    "utilization":       0.10,
}


def _normalize(series: pd.Series) -> pd.Series:
    """Min-max normalize a series to 0–1."""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series(0.5, index=series.index)
    return (series - min_val) / (max_val - min_val)


def calculate_demand_score(dim_location: pd.DataFrame) -> pd.Series:
    """
    Demand score: how much EV charging demand exists here?

    Based on:
      - EV registrations nearby (primary)
      - Population density (secondary)
    """
    raw = (
        dim_location["ev_registrations_nearby"] * 0.7
        + dim_location["population_density"] * 0.3
    )
    return _normalize(raw)


def calculate_supply_gap_score(
    dim_location: pd.DataFrame,
    dim_charger: pd.DataFrame,
) -> pd.Series:
    """
    Supply gap: how underserved is this area?

    Fewer existing chargers per capita = higher supply gap score.
    """
    # Count chargers per postcode
    charger_counts = dim_charger.groupby("postcode").size().reset_index(name="charger_count")
    location_with_counts = dim_location.merge(charger_counts, on="postcode", how="left")
    location_with_counts["charger_count"] = location_with_counts["charger_count"].fillna(0)

    # Chargers per 1000 EVs (lower = bigger gap)
    ev_regs = location_with_counts["ev_registrations_nearby"].replace(0, 1)
    chargers_per_ev = location_with_counts["charger_count"] / ev_regs

    # Invert: low chargers per EV = high gap score
    return _normalize(1 - _normalize(chargers_per_ev))


def calculate_road_access_score(dim_location: pd.DataFrame) -> pd.Series:
    """
    Road access score: is this location easy to reach by car?

    Motorway/A-road locations score higher.
    Closer to motorway = better access.
    """
    road_type_score = dim_location["road_type"].map({
        "motorway": 1.0,
        "A_road":   0.75,
        "B_road":   0.5,
        "urban":    0.4,
    }).fillna(0.3)

    # Normalize nearest competitor distance (further = less competition = better)
    competition_score = _normalize(dim_location["nearest_competitor_km"])

    return (road_type_score * 0.6 + competition_score * 0.4)


def calculate_coverage_deficit_score(dim_location: pd.DataFrame) -> pd.Series:
    """
    Coverage deficit: how far is the nearest competitor charger?

    Farther = bigger coverage gap = higher priority.
    """
    return _normalize(dim_location["nearest_competitor_km"])


def calculate_utilization_score(
    dim_location: pd.DataFrame,
    fact_sessions: pd.DataFrame,
    dim_charger: pd.DataFrame,
) -> pd.Series:
    """
    Utilization signal: are existing chargers being heavily used?

    High utilization = demand is real, add more supply here.
    """
    # Average sessions per charger per day per postcode
    completed = fact_sessions[fact_sessions["status"] == "completed"]
    sessions_by_postcode = completed.groupby("postcode")["session_id"].count()
    chargers_by_postcode = dim_charger.groupby("postcode").size()
    utilization = (sessions_by_postcode / chargers_by_postcode).fillna(0)

    location_util = dim_location["postcode"].map(utilization).fillna(0)
    return _normalize(location_util)


def calculate_priority_scores(
    dim_location: pd.DataFrame,
    dim_charger: pd.DataFrame,
    fact_sessions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate the full Site Priority Score for each location.

    Returns DataFrame sorted by score descending (highest priority first).
    """
    log.info("Calculating Site Priority Scores")

    scores = dim_location.copy()

    scores["score_demand"] = calculate_demand_score(dim_location)
    scores["score_supply_gap"] = calculate_supply_gap_score(dim_location, dim_charger)
    scores["score_road_access"] = calculate_road_access_score(dim_location)
    scores["score_coverage"] = calculate_coverage_deficit_score(dim_location)
    scores["score_utilization"] = calculate_utilization_score(
        dim_location, fact_sessions, dim_charger
    )

    # Weighted sum → scale to 0–100
    scores["priority_score"] = round((
        scores["score_demand"]       * WEIGHTS["demand"]
        + scores["score_supply_gap"] * WEIGHTS["supply_gap"]
        + scores["score_road_access"] * WEIGHTS["road_access"]
        + scores["score_coverage"]   * WEIGHTS["coverage_deficit"]
        + scores["score_utilization"] * WEIGHTS["utilization"]
    ) * 100, 1)

    scores["priority_rank"] = scores["priority_score"].rank(
        ascending=False, method="min"
    ).astype(int)

    scores = scores.sort_values("priority_score", ascending=False)

    log.info(f"Top priority location: {scores.iloc[0]['postcode']} "
             f"(score: {scores.iloc[0]['priority_score']})")

    return scores
