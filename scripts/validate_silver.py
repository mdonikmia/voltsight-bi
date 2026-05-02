"""
Validate Silver layer data quality.

Run after transform_to_silver.py to verify the transformation succeeded.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from voltsight.config import load_config  # noqa: E402
from voltsight.logger import get_logger  # noqa: E402

log = get_logger(__name__)


def validate_silver() -> bool:
    """Run validation checks on Silver layer."""
    config = load_config()
    silver_dir = config.pipeline.bronze_dir.parent / "silver"

    if not silver_dir.exists():
        log.error(f"Silver directory not found: {silver_dir}")
        return False

    # Find latest parquet file
    parquet_files = sorted(silver_dir.glob("*.parquet"))
    if not parquet_files:
        log.error("No parquet files in Silver directory")
        return False

    latest = parquet_files[-1]
    log.info(f"Validating {latest.name}")

    df = pd.read_parquet(latest)
    log.info(f"Loaded {len(df):,} rows")

    checks = {
        "row_count_above_50k": len(df) > 50_000,
        "no_null_latitude": df["latitude"].notna().all(),
        "no_null_longitude": df["longitude"].notna().all(),
        "latitude_in_uk_range": df["latitude"].between(49, 61).all(),
        "longitude_in_uk_range": df["longitude"].between(-9, 2).all(),
        "ward_column_exists": "ward_name" in df.columns,
        "lsoa_column_exists": "lsoa_code" in df.columns,
        "population_column_exists": "population_nearby" in df.columns,
        "ev_adoption_column_exists": "ev_adoption_rate" in df.columns,
        "motorway_distance_column_exists": "distance_to_motorway_km" in df.columns,
    }

    log.info("=" * 60)
    log.info("Silver Layer Validation Results")
    log.info("=" * 60)

    all_passed = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        log.info(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    log.info("=" * 60)
    if all_passed:
        log.info("✓ All validation checks passed. Silver layer is ready!")
        return True
    else:
        log.warning("✗ Some checks failed. Review the output above.")
        return False


if __name__ == "__main__":
    success = validate_silver()
    sys.exit(0 if success else 1)
