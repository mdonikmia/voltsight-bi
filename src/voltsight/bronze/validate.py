"""
Bronze layer validation.

Quality checks applied to each Bronze data source. The principle is
fail-fast: catch obvious data issues here, before they propagate
to Silver and then to the dashboard where they become much harder
to diagnose.

Each source has a dedicated validator function. Each validator returns
a list of (check_name, passed, detail) tuples. A source passes overall
if every check passes.

Industry parallel: this is a lightweight version of the same pattern used
by `Great Expectations` and `dbt tests`. Showing this pattern in a portfolio
project signals you understand modern data quality engineering.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from voltsight.config import VoltSightConfig
from voltsight.logger import get_logger
from voltsight.manifest import read_manifest

log = get_logger(__name__)


@dataclass
class CheckResult:
    """Outcome of a single validation check."""

    name: str
    passed: bool
    detail: str = ""


@dataclass
class ValidationReport:
    """Validation report for a single source."""

    source_key: str
    checks: list[CheckResult]

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)


def _latest_data_file(folder: Path, extension: str = ".parquet") -> Path | None:
    """Return the most recent file with the given extension, or None."""
    files = sorted(folder.glob(f"*{extension}"))
    return files[-1] if files else None


def _check(name: str, condition: bool, detail: str = "") -> CheckResult:
    """Helper to construct a CheckResult."""
    return CheckResult(name=name, passed=condition, detail=detail)


def validate_ncr_chargers(folder: Path) -> ValidationReport:
    """
    Validation checks for the UK National Chargepoint Registry source.

    Checks:
      - Manifest exists and is readable
      - Data file exists
      - Row count above 30,000 (sanity check — the UK has ~50k chargers)
      - Required columns present
      - Latitude values in UK range (49.0 to 61.0)
      - Longitude values in UK range (-8.5 to 2.0)
      - At least 90% of records have postcodes
      - No completely duplicated rows
    """
    checks: list[CheckResult] = []

    manifest = read_manifest(folder)
    checks.append(_check(
        "manifest_exists",
        manifest is not None,
        f"Looked in {folder}",
    ))

    if manifest is None:
        return ValidationReport(source_key="ncr_chargers", checks=checks)

    data_file = _latest_data_file(folder, ".parquet")
    if data_file is None:
        # Fall back to CSV if parquet not present
        data_file = _latest_data_file(folder, ".csv")

    checks.append(_check(
        "data_file_exists",
        data_file is not None,
    ))

    if data_file is None:
        return ValidationReport(source_key="ncr_chargers", checks=checks)

    # Read once for all subsequent checks
    if data_file.suffix == ".parquet":
        df = pd.read_parquet(data_file)
    else:
        df = pd.read_csv(data_file, low_memory=False)

    checks.append(_check(
        "row_count_above_30k",
        len(df) > 30_000,
        f"Got {len(df):,} rows",
    ))

    required_cols = ["chargeDeviceID", "latitude", "longitude", "postcode"]
    missing = [c for c in required_cols if c not in df.columns]
    checks.append(_check(
        "required_columns_present",
        len(missing) == 0,
        f"Missing: {missing}" if missing else "All present",
    ))

    if "latitude" in df.columns:
        # Coerce to numeric — sometimes lat/lng arrive as strings
        lat = pd.to_numeric(df["latitude"], errors="coerce")
        in_uk_lat = lat.between(49.0, 61.0).mean()
        checks.append(_check(
            "latitudes_in_uk_range",
            in_uk_lat > 0.95,
            f"{in_uk_lat:.1%} of latitudes in UK range",
        ))

    if "longitude" in df.columns:
        lng = pd.to_numeric(df["longitude"], errors="coerce")
        in_uk_lng = lng.between(-8.5, 2.0).mean()
        checks.append(_check(
            "longitudes_in_uk_range",
            in_uk_lng > 0.95,
            f"{in_uk_lng:.1%} of longitudes in UK range",
        ))

    if "postcode" in df.columns:
        postcode_present = df["postcode"].notna().mean()
        checks.append(_check(
            "postcodes_present",
            postcode_present > 0.85,
            f"{postcode_present:.1%} of records have postcodes",
        ))

    duplicates = df.duplicated().sum()
    checks.append(_check(
        "no_complete_duplicates",
        duplicates == 0,
        f"{duplicates:,} duplicate rows" if duplicates else "0 duplicates",
    ))

    return ValidationReport(source_key="ncr_chargers", checks=checks)


def validate_all(config: VoltSightConfig) -> dict[str, ValidationReport]:
    """
    Run validators for all sources that have one defined.

    Returns:
        Dict mapping source_key to ValidationReport.
    """
    reports: dict[str, ValidationReport] = {}

    # Map source keys to validator functions
    # Add new validators here as new sources gain dedicated checks
    validators = {
        "ncr_chargers": validate_ncr_chargers,
        # Future: "ons_postcode_directory": validate_ons_postcodes, etc.
    }

    for source_key, validator in validators.items():
        folder = config.pipeline.bronze_dir / source_key
        if not folder.exists():
            log.warning(f"Folder {folder} does not exist. Skipping validation.")
            continue
        log.info(f"Validating {source_key}...")
        reports[source_key] = validator(folder)

    return reports


def print_report(report: ValidationReport) -> None:
    """Pretty-print a validation report to stdout."""
    print(f"\n[{report.source_key}]")
    for check in report.checks:
        icon = "✓" if check.passed else "✗"
        line = f"  {icon} {check.name}"
        if check.detail:
            line += f"  ({check.detail})"
        print(line)
    summary = (
        f"  {report.passed_count}/{len(report.checks)} checks passed"
    )
    print(f"  {'─' * 40}")
    print(f"  {summary}")
