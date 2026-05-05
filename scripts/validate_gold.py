"""
Validate Gold layer tables.

Checks that all star schema tables exist and meet quality standards.
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

EXPECTED_TABLES = [
    "dim_charger",
    "dim_location",
    "dim_date",
    "fact_sessions",
    "fact_availability",
    "gold_priority_scores",
]


def validate_gold() -> bool:
    config = load_config()
    gold_dir = config.pipeline.bronze_dir.parent / "gold"

    if not gold_dir.exists():
        log.error(f"Gold directory not found: {gold_dir}")
        return False

    log.info("=" * 60)
    log.info("Gold Layer Validation Results")
    log.info("=" * 60)

    all_passed = True

    for table_name in EXPECTED_TABLES:
        parquet_path = gold_dir / f"{table_name}.parquet"

        if not parquet_path.exists():
            log.warning(f"  ✗ {table_name}: FILE MISSING")
            all_passed = False
            continue

        df = pd.read_parquet(parquet_path)
        row_count = len(df)

        checks = {
            "dim_charger":          row_count >= 100,
            "dim_location":         row_count >= 10,
            "dim_date":             row_count == 365,
            "fact_sessions":        row_count >= 1000,
            "fact_availability":    row_count >= 1000,
            "gold_priority_scores": row_count >= 10,
        }

        passed = checks.get(table_name, True)
        status = "✓" if passed else "✗"
        log.info(f"  {status} {table_name}: {row_count:,} rows")

        if not passed:
            all_passed = False

    # Extra checks on priority scores
    priority_path = gold_dir / "gold_priority_scores.parquet"
    if priority_path.exists():
        priority_df = pd.read_parquet(priority_path)
        score_check = priority_df["priority_score"].between(0, 100).all()
        rank_check = "priority_rank" in priority_df.columns
        log.info(f"  {'✓' if score_check else '✗'} priority_score in range 0-100")
        log.info(f"  {'✓' if rank_check else '✗'} priority_rank column exists")
        if not score_check or not rank_check:
            all_passed = False

    log.info("=" * 60)
    if all_passed:
        log.info("✓ All Gold layer checks passed. Ready for Power BI!")
    else:
        log.warning("✗ Some checks failed. Review above.")

    return all_passed


if __name__ == "__main__":
    success = validate_gold()
    sys.exit(0 if success else 1)
