"""
Gold layer orchestrator — Silver → Gold transformation.

Builds:
  1. DIM_CHARGER        — charger attributes
  2. DIM_LOCATION       — location attributes + enrichment
  3. DIM_DATE           — calendar dimension
  4. FACT_SESSIONS      — simulated charging sessions (12 months)
  5. FACT_AVAILABILITY  — daily charger uptime
  6. GOLD_PRIORITY      — Site Priority Scores

All outputs saved to data/gold/ as Parquet + CSV.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from voltsight.config import load_config  # noqa: E402
from voltsight.logger import get_logger  # noqa: E402
from voltsight.gold.simulate import (  # noqa: E402
    build_dim_charger,
    build_dim_date,
    build_dim_location,
    build_fact_sessions,
    build_fact_availability,
)
from voltsight.gold.priority_score import calculate_priority_scores  # noqa: E402

log = get_logger(__name__)


def save(df: pd.DataFrame, gold_dir: Path, name: str) -> None:
    """Save a Gold table as both Parquet and CSV."""
    parquet_path = gold_dir / f"{name}.parquet"
    csv_path = gold_dir / f"{name}.csv"
    df.to_parquet(parquet_path, index=False, engine="pyarrow")
    df.to_csv(csv_path, index=False)
    log.info(f"Saved {name}: {len(df):,} rows → {parquet_path.name}")


def main() -> int:
    config = load_config()
    silver_dir = config.pipeline.bronze_dir.parent / "silver"
    gold_dir = config.pipeline.bronze_dir.parent / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)

    # ── Load Silver data ──────────────────────────────────────────────────
    silver_files = sorted(silver_dir.glob("*.parquet"))
    if not silver_files:
        log.error("No Silver parquet files found. Run transform_to_silver.py first.")
        return 1

    log.info("=" * 60)
    log.info("VoltSight BI — Silver → Gold Transformation")
    log.info("=" * 60)

    silver_df = pd.read_parquet(silver_files[-1])
    log.info(f"Loaded Silver data: {len(silver_df):,} rows")

    # ── Build dimensions ──────────────────────────────────────────────────
    dim_charger = build_dim_charger(silver_df, n_chargers=500)
    save(dim_charger, gold_dir, "dim_charger")

    dim_location = build_dim_location(dim_charger)
    save(dim_location, gold_dir, "dim_location")

    dim_date = build_dim_date("2025-01-01", "2025-12-31")
    save(dim_date, gold_dir, "dim_date")

    # ── Build facts ───────────────────────────────────────────────────────
    log.info("Building FACT_SESSIONS (takes ~60 seconds)...")
    fact_sessions = build_fact_sessions(dim_charger, dim_date)
    save(fact_sessions, gold_dir, "fact_sessions")

    log.info("Building FACT_AVAILABILITY...")
    fact_availability = build_fact_availability(fact_sessions, dim_charger, dim_date)
    save(fact_availability, gold_dir, "fact_availability")

    # ── Site Priority Score ───────────────────────────────────────────────
    log.info("Calculating Site Priority Scores...")
    gold_priority = calculate_priority_scores(dim_location, dim_charger, fact_sessions)
    save(gold_priority, gold_dir, "gold_priority_scores")

    # ── Summary ───────────────────────────────────────────────────────────
    log.info("=" * 60)
    log.info("Gold Layer Complete!")
    log.info(f"  DIM_CHARGER:       {len(dim_charger):>8,} rows")
    log.info(f"  DIM_LOCATION:      {len(dim_location):>8,} rows")
    log.info(f"  DIM_DATE:          {len(dim_date):>8,} rows")
    log.info(f"  FACT_SESSIONS:     {len(fact_sessions):>8,} rows")
    log.info(f"  FACT_AVAILABILITY: {len(fact_availability):>8,} rows")
    log.info(f"  PRIORITY_SCORES:   {len(gold_priority):>8,} rows")
    log.info(f"\n✓ All Gold tables saved to: {gold_dir}")
    log.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
