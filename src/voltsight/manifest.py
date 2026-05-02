"""
Manifest writer — records provenance for every Bronze layer ingestion.

A manifest answers: when was this data pulled, from where, how big was it,
and what was its checksum? This is data lineage — a core data engineering
concept that hiring managers look for in portfolio projects.

Every Bronze source folder gets a `_manifest.json` after each pull.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_FILENAME = "_manifest.json"


@dataclass
class Manifest:
    """Provenance record for a single ingestion event."""

    source_key: str
    source_name: str
    source_url: str
    pull_timestamp_utc: str
    filename: str
    file_size_bytes: int
    file_sha256: str
    row_count: int
    license: str
    schema_version: str = "1.0"
    notes: str = ""

    def to_json(self) -> str:
        """Serialise to pretty-printed JSON."""
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def compute_sha256(file_path: Path, chunk_size: int = 64 * 1024) -> str:
    """
    Compute SHA256 hash of a file, streaming for memory efficiency.

    Why SHA256? It's the industry standard for file integrity verification.
    If a file ever needs to be re-downloaded, the hash confirms whether
    the source data actually changed or just the timestamp.
    """
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def utc_now_iso() -> str:
    """Current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_manifest(folder: Path, manifest: Manifest) -> Path:
    """
    Write the manifest file inside the given folder.

    Args:
        folder: Folder where the manifest should be written.
        manifest: Manifest data to serialise.

    Returns:
        Path to the written manifest file.
    """
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / MANIFEST_FILENAME
    manifest_path.write_text(manifest.to_json(), encoding="utf-8")
    return manifest_path


def read_manifest(folder: Path) -> Manifest | None:
    """
    Read an existing manifest, if present.

    Returns None if no manifest exists in the folder.
    Used for idempotency checks — skip a download if the manifest
    indicates today's pull already succeeded.
    """
    manifest_path = folder / MANIFEST_FILENAME
    if not manifest_path.exists():
        return None
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return Manifest(**data)
