"""
Unit tests for Bronze layer logic.

Tests focus on the pure logic — manifest handling, file operations,
validation logic — that doesn't require network access. The actual
download is integration-tested by running the script.

Why include tests in a portfolio project?
  - Most graduate projects have zero tests. This stands out.
  - Demonstrates understanding of testable code structure.
  - Acts as living documentation of expected behaviour.

Run with:
    pytest tests/
    pytest tests/ -v --cov=src/voltsight    # with coverage
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import sys
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from voltsight.bronze.validate import (  # noqa: E402
    ValidationReport,
    validate_ncr_chargers,
)
from voltsight.manifest import (  # noqa: E402
    Manifest,
    compute_sha256,
    read_manifest,
    write_manifest,
)


# === Manifest tests ===

class TestManifest:
    """Tests for the manifest writer/reader."""

    def test_write_and_read_round_trip(self, tmp_path: Path) -> None:
        manifest = Manifest(
            source_key="test_source",
            source_name="Test Source",
            source_url="https://example.com/data",
            pull_timestamp_utc="2026-05-02T12:00:00Z",
            filename="2026-05-02_test.csv",
            file_size_bytes=1024,
            file_sha256="a" * 64,
            row_count=100,
            license="Test License",
        )

        write_manifest(tmp_path, manifest)
        loaded = read_manifest(tmp_path)

        assert loaded is not None
        assert loaded.source_key == manifest.source_key
        assert loaded.row_count == manifest.row_count
        assert loaded.file_sha256 == manifest.file_sha256

    def test_read_returns_none_when_missing(self, tmp_path: Path) -> None:
        assert read_manifest(tmp_path) is None

    def test_manifest_writes_valid_json(self, tmp_path: Path) -> None:
        manifest = Manifest(
            source_key="x",
            source_name="x",
            source_url="x",
            pull_timestamp_utc="x",
            filename="x",
            file_size_bytes=0,
            file_sha256="x",
            row_count=0,
            license="x",
        )
        path = write_manifest(tmp_path, manifest)
        # Should be valid JSON
        loaded = json.loads(path.read_text())
        assert loaded["source_key"] == "x"


class TestSHA256:
    """Tests for the SHA256 computation."""

    def test_known_hash(self, tmp_path: Path) -> None:
        # SHA256 of empty string is well-known
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")
        expected = (
            "e3b0c44298fc1c149afbf4c8996fb924"
            "27ae41e4649b934ca495991b7852b855"
        )
        assert compute_sha256(empty_file) == expected

    def test_hash_is_deterministic(self, tmp_path: Path) -> None:
        file = tmp_path / "data.txt"
        file.write_bytes(b"voltsight")
        assert compute_sha256(file) == compute_sha256(file)


# === Validator tests ===

class TestNCRValidator:
    """Tests for the NCR validation logic."""

    def _make_valid_ncr_dataframe(self, n_rows: int = 35_000) -> pd.DataFrame:
        """Create a synthetic NCR-shaped DataFrame that passes all checks."""
        return pd.DataFrame({
            "chargeDeviceID": [f"CD{i:06d}" for i in range(n_rows)],
            "latitude": [51.5 + (i % 100) * 0.001 for i in range(n_rows)],
            "longitude": [-0.1 + (i % 100) * 0.001 for i in range(n_rows)],
            "postcode": [f"BS{i % 99} {i % 9}AA" for i in range(n_rows)],
        })

    def test_passes_when_data_is_clean(self, tmp_path: Path) -> None:
        # Set up a folder with a valid manifest + parquet file
        df = self._make_valid_ncr_dataframe()
        parquet_path = tmp_path / "2026-05-02_ncr_chargers.parquet"
        df.to_parquet(parquet_path)

        manifest = Manifest(
            source_key="ncr_chargers",
            source_name="NCR",
            source_url="x",
            pull_timestamp_utc="x",
            filename="2026-05-02_ncr_chargers.parquet",
            file_size_bytes=parquet_path.stat().st_size,
            file_sha256="x",
            row_count=len(df),
            license="OGL v3.0",
        )
        write_manifest(tmp_path, manifest)

        report = validate_ncr_chargers(tmp_path)
        assert report.all_passed, (
            f"Expected all checks to pass, but got: "
            f"{[(c.name, c.passed, c.detail) for c in report.checks if not c.passed]}"
        )

    def test_fails_when_no_data_file(self, tmp_path: Path) -> None:
        # Folder with manifest but no actual data file
        manifest = Manifest(
            source_key="ncr_chargers",
            source_name="x", source_url="x", pull_timestamp_utc="x",
            filename="missing.csv", file_size_bytes=0, file_sha256="x",
            row_count=0, license="x",
        )
        write_manifest(tmp_path, manifest)
        report = validate_ncr_chargers(tmp_path)
        assert not report.all_passed
        assert any(
            c.name == "data_file_exists" and not c.passed
            for c in report.checks
        )

    def test_fails_on_low_row_count(self, tmp_path: Path) -> None:
        df = self._make_valid_ncr_dataframe(n_rows=100)  # way below threshold
        df.to_parquet(tmp_path / "2026-05-02_ncr_chargers.parquet")
        write_manifest(tmp_path, Manifest(
            source_key="ncr_chargers", source_name="x", source_url="x",
            pull_timestamp_utc="x", filename="2026-05-02_ncr_chargers.parquet",
            file_size_bytes=1, file_sha256="x", row_count=100, license="x",
        ))
        report = validate_ncr_chargers(tmp_path)
        assert not report.all_passed
        assert any(
            c.name == "row_count_above_30k" and not c.passed
            for c in report.checks
        )

    def test_fails_on_non_uk_coordinates(self, tmp_path: Path) -> None:
        # Build a dataset where coordinates are in the wrong country
        n_rows = 35_000
        df = pd.DataFrame({
            "chargeDeviceID": [f"CD{i:06d}" for i in range(n_rows)],
            "latitude": [40.0] * n_rows,    # New York-ish, not UK
            "longitude": [-74.0] * n_rows,
            "postcode": ["NY1 1AA"] * n_rows,
        })
        df.to_parquet(tmp_path / "2026-05-02_ncr_chargers.parquet")
        write_manifest(tmp_path, Manifest(
            source_key="ncr_chargers", source_name="x", source_url="x",
            pull_timestamp_utc="x", filename="2026-05-02_ncr_chargers.parquet",
            file_size_bytes=1, file_sha256="x", row_count=n_rows, license="x",
        ))
        report = validate_ncr_chargers(tmp_path)
        assert not report.all_passed
        # Either lat or lng range check should fail
        failed_names = {c.name for c in report.checks if not c.passed}
        assert (
            "latitudes_in_uk_range" in failed_names
            or "longitudes_in_uk_range" in failed_names
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
