#!/usr/bin/env python3
"""
VoltSight BI — Bronze layer ingestion entry point.

Run this to download all configured external data sources into the
Bronze layer. Safe to re-run; idempotent on the same day.

Usage:
    python scripts/ingest_bronze.py
    python scripts/ingest_bronze.py --source ncr_chargers   # single source
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the `src/` directory importable when running this script directly
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from voltsight.bronze.ingest import ingest_all, ingest_source  # noqa: E402
from voltsight.config import load_config  # noqa: E402
from voltsight.logger import get_logger  # noqa: E402

log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest external data sources into the Bronze layer.",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Optional source key to ingest (default: all sources).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to config YAML (default: config/sources.yaml).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)

    log.info("=" * 60)
    log.info("VoltSight BI — Bronze Layer Ingestion")
    log.info("=" * 60)
    log.info(f"Bronze directory: {config.pipeline.bronze_dir}")
    log.info(f"Sources defined: {len(config.sources)}")

    if args.source:
        source = config.source(args.source)
        results = [ingest_source(source, config)]
    else:
        results = ingest_all(config)

    # Summary report
    log.info("=" * 60)
    log.info("Ingestion summary:")
    log.info("=" * 60)

    successes = sum(1 for r in results if r.success and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    failures = sum(1 for r in results if not r.success and not r.skipped)

    for r in results:
        if r.skipped and r.success:
            status = "SKIPPED (already pulled today)"
        elif r.skipped:
            status = f"SKIPPED ({r.error})"
        elif r.success:
            status = f"OK — {r.rows:,} rows, {r.bytes_downloaded:,} bytes"
        else:
            status = f"FAILED — {r.error}"
        log.info(f"  {r.source_key}: {status}")

    log.info("=" * 60)
    log.info(
        f"Total: {successes} succeeded, {skipped} skipped, {failures} failed"
    )

    # Exit code: 0 if no actual failures, 1 otherwise
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
