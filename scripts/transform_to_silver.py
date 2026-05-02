#!/usr/bin/env python3
"""
VoltSight BI — Transform Bronze → Silver layer

This script orchestrates the data cleaning and enrichment pipeline.

Run:
    python scripts/transform_to_silver.py

Output:
    Silver layer CSV and Parquet files in data/silver/
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from voltsight.config import load_config  # noqa: E402
from voltsight.logger import get_logger  # noqa: E402
from voltsight.silver.transform import transform_bronze_to_silver  # noqa: E402

log = get_logger(__name__)


def main() -> int:
    config = load_config()

    bronze_ncr_dir = config.pipeline.bronze_dir / "ncr_chargers"
    silver_dir = config.pipeline.bronze_dir.parent / "silver"

    if not bronze_ncr_dir.exists():
        log.error(f"Bronze directory not found: {bronze_ncr_dir}")
        log.error("Run 'python scripts/ingest_bronze.py' first")
        return 1

    try:
        outputs = transform_bronze_to_silver(bronze_ncr_dir, silver_dir)
        if outputs:
            log.info(f"\n✓ Success! Silver layer ready at: {silver_dir}")
            return 0
        else:
            log.error("Transformation failed — no output files created")
            return 1
    except Exception as e:
        log.exception(f"Transformation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
