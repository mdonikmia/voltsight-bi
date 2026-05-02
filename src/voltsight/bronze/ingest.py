"""
Bronze layer ingestion logic.

This module orchestrates the download, storage, and manifest creation
for each external data source. It is called by `scripts/ingest_bronze.py`.

Design principles:
  - Idempotent: re-running on the same day is a no-op (won't re-download).
  - Fail-soft: one source failing doesn't stop the others.
  - Defensive: validates row counts, file sizes, and writes provenance.
  - Convertible: CSVs are also written to parquet for fast downstream reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from voltsight.config import SourceConfig, VoltSightConfig
from voltsight.http_client import HTTPError, download
from voltsight.logger import get_logger
from voltsight.manifest import (
    Manifest,
    compute_sha256,
    read_manifest,
    utc_now_iso,
    write_manifest,
)

log = get_logger(__name__)


@dataclass
class IngestionResult:
    """Outcome of attempting to ingest one source."""

    source_key: str
    success: bool
    skipped: bool = False
    rows: int = 0
    bytes_downloaded: int = 0
    error: str | None = None


def _today_string(date_format: str) -> str:
    """Return today's UTC date as a string in the configured format."""
    return datetime.now(timezone.utc).strftime(date_format)


def _output_filename(source: SourceConfig, date_str: str) -> str:
    """Construct the date-prefixed output filename for a source."""
    return f"{date_str}_{source.filename}"


def _already_ingested_today(folder: Path, expected_filename: str) -> bool:
    """
    Check if the source has already been pulled today.

    Read the existing manifest and compare its filename. If today's file
    exists and the manifest matches, skip the download.
    """
    manifest = read_manifest(folder)
    if manifest is None:
        return False
    expected_file = folder / expected_filename
    return manifest.filename == expected_filename and expected_file.exists()


def _count_rows(file_path: Path, file_format: str) -> int:
    """Count rows in a downloaded file (excluding header for CSV)."""
    if file_format == "csv":
        # Use a fast row count without loading the full file into memory
        with file_path.open("r", encoding="utf-8", errors="replace") as f:
            # Subtract 1 for the header line
            count = sum(1 for _ in f) - 1
        return max(count, 0)
    elif file_format == "geojson":
        # GeoJSON: count features
        import json
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return len(data.get("features", []))
    return 0


def _convert_csv_to_parquet(csv_path: Path) -> Path:
    """
    Save a parquet copy of a CSV for fast downstream reads.

    Why parquet?
      - 5–10x faster reads than CSV in pandas
      - Smaller on disk (compressed columnar storage)
      - Preserves dtypes — no inference needed on every load
      - The de facto standard for analytics in production
    """
    parquet_path = csv_path.with_suffix(".parquet")
    df = pd.read_csv(csv_path, low_memory=False)
    df.to_parquet(parquet_path, index=False, engine="pyarrow")
    log.info(f"Converted {csv_path.name} to parquet ({len(df):,} rows)")
    return parquet_path


def ingest_source(
    source: SourceConfig,
    config: VoltSightConfig,
) -> IngestionResult:
    """
    Ingest one external source into the Bronze layer.

    Steps:
      1. Skip if today's pull already exists (idempotent).
      2. Skip if format is 'manual_download' (DVLA — needs human action).
      3. Download to date-prefixed CSV/JSON file.
      4. Convert CSV to parquet copy for downstream speed.
      5. Compute SHA256 hash for integrity.
      6. Count rows and validate against expected minimum.
      7. Write manifest with full lineage record.

    Args:
        source: Single SourceConfig.
        config: Full VoltSightConfig (for pipeline settings).

    Returns:
        IngestionResult describing the outcome.
    """
    log.info(f"--- Ingesting source: {source.key} ---")

    # Manual download sources can't be auto-fetched
    if source.format == "manual_download":
        log.warning(
            f"Source '{source.key}' is manual_download. "
            f"Place the file at: {config.pipeline.bronze_dir / source.key}/"
        )
        return IngestionResult(
            source_key=source.key,
            success=False,
            skipped=True,
            error="Manual download required",
        )

    today = _today_string(config.pipeline.date_format)
    folder = config.pipeline.bronze_dir / source.key
    output_filename = _output_filename(source, today)
    output_path = folder / output_filename

    # Idempotency check
    if _already_ingested_today(folder, output_filename):
        log.info(f"Already ingested today: {output_path}. Skipping.")
        return IngestionResult(
            source_key=source.key,
            success=True,
            skipped=True,
        )

    # Download with retry
    try:
        bytes_downloaded = download(
            url=source.url,
            destination=output_path,
            user_agent=source.user_agent,
            timeout=config.pipeline.http_timeout_seconds,
            retry_attempts=config.pipeline.retry_attempts,
            retry_initial_wait=config.pipeline.retry_initial_wait_seconds,
            retry_max_wait=config.pipeline.retry_max_wait_seconds,
        )
    except HTTPError as e:
        log.error(f"Download failed for {source.key}: {e}")
        return IngestionResult(
            source_key=source.key,
            success=False,
            error=str(e),
        )

    # Convert CSV → parquet for faster downstream reads
    if source.format == "csv":
        try:
            _convert_csv_to_parquet(output_path)
        except Exception as e:
            log.warning(
                f"CSV-to-parquet conversion failed for {source.key}: {e}. "
                "CSV is still saved; downstream code will use it."
            )

    # Row count + validation
    row_count = _count_rows(output_path, source.format)
    log.info(f"Row count: {row_count:,}")

    if row_count < source.expected_min_rows:
        log.warning(
            f"Row count {row_count:,} below expected minimum "
            f"{source.expected_min_rows:,} for {source.key}. "
            "File still saved — investigate before promoting to Silver."
        )

    # Write manifest with provenance
    manifest = Manifest(
        source_key=source.key,
        source_name=source.description,
        source_url=source.url,
        pull_timestamp_utc=utc_now_iso(),
        filename=output_filename,
        file_size_bytes=bytes_downloaded,
        file_sha256=compute_sha256(output_path),
        row_count=row_count,
        license=source.license,
        notes=source.notes,
    )
    write_manifest(folder, manifest)

    return IngestionResult(
        source_key=source.key,
        success=True,
        rows=row_count,
        bytes_downloaded=bytes_downloaded,
    )


def ingest_all(config: VoltSightConfig) -> list[IngestionResult]:
    """
    Ingest every source defined in config. One source failing does not
    stop the others — each is independent.

    Returns:
        List of IngestionResult — one per source.
    """
    results: list[IngestionResult] = []
    for source in config.sources.values():
        try:
            result = ingest_source(source, config)
        except Exception as e:
            # Final safety net — should never happen, but if it does,
            # log and continue with remaining sources.
            log.exception(f"Unexpected error ingesting {source.key}: {e}")
            result = IngestionResult(
                source_key=source.key,
                success=False,
                error=f"Unexpected error: {e}",
            )
        results.append(result)
    return results
