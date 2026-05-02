#!/usr/bin/env python3
"""
VoltSight BI — Bronze layer validation entry point.

Run quality checks on all ingested Bronze data. Use this BEFORE promoting
data to the Silver layer.

Exit code:
    0 — all checks passed
    1 — one or more checks failed; investigate before proceeding

Usage:
    python scripts/validate_bronze.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from voltsight.bronze.validate import print_report, validate_all  # noqa: E402
from voltsight.config import load_config  # noqa: E402
from voltsight.logger import get_logger  # noqa: E402

log = get_logger(__name__)


def main() -> int:
    config = load_config()

    log.info("=" * 60)
    log.info("VoltSight BI — Bronze Layer Validation")
    log.info("=" * 60)

    reports = validate_all(config)

    if not reports:
        log.warning(
            "No validation reports generated. "
            "Have you run scripts/ingest_bronze.py yet?"
        )
        return 1

    # Print pretty reports
    for report in reports.values():
        print_report(report)

    # Summary
    print()
    print("=" * 60)
    all_passed = all(r.all_passed for r in reports.values())
    if all_passed:
        print("✓ All validations passed. Safe to proceed to Silver layer.")
        return 0
    else:
        print("✗ One or more validations failed.")
        print("  Investigate issues above before proceeding to Silver.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
