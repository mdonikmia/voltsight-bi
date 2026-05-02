"""
Configuration loader for VoltSight BI.

Single responsibility: read config/sources.yaml and expose typed access
to its contents. All other modules go through this — never read YAML
directly elsewhere.

Why a dedicated module?
  - Centralises the schema of the config file
  - Easy to swap YAML for env vars or AWS Parameter Store later
  - Makes config errors fail loudly on import, not deep in a pipeline run
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# Resolve config relative to repo root, regardless of where Python is invoked
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "config" / "sources.yaml"


@dataclass(frozen=True)
class SourceConfig:
    """Configuration for a single external data source."""

    key: str
    url: str
    format: str
    filename: str
    description: str
    license: str
    user_agent: str = "VoltSight-BI/1.0"
    expected_min_rows: int = 0
    primary_key: str | None = None
    notes: str = ""


@dataclass(frozen=True)
class PipelineConfig:
    """Pipeline-level operational settings."""

    bronze_dir: Path
    retry_attempts: int
    retry_initial_wait_seconds: int
    retry_max_wait_seconds: int
    http_timeout_seconds: int
    date_format: str


@dataclass(frozen=True)
class VoltSightConfig:
    """Root configuration container."""

    sources: dict[str, SourceConfig]
    pipeline: PipelineConfig

    def source(self, key: str) -> SourceConfig:
        """Get a source by key, with a clear error if it doesn't exist."""
        if key not in self.sources:
            available = ", ".join(self.sources.keys())
            raise KeyError(
                f"Unknown source '{key}'. Available sources: {available}"
            )
        return self.sources[key]


def load_config(path: Path | None = None) -> VoltSightConfig:
    """
    Load configuration from YAML.

    Args:
        path: Optional path to config file. Defaults to config/sources.yaml
              relative to the repo root.

    Returns:
        Fully validated VoltSightConfig.

    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If config structure is invalid.
    """
    config_path = path or _DEFAULT_CONFIG_PATH

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Expected location: {_DEFAULT_CONFIG_PATH}"
        )

    with config_path.open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    if "sources" not in raw or "pipeline" not in raw:
        raise ValueError(
            "Configuration must have 'sources' and 'pipeline' top-level keys."
        )

    # Build typed source configs
    sources: dict[str, SourceConfig] = {}
    for key, src in raw["sources"].items():
        sources[key] = SourceConfig(
            key=key,
            url=src["url"],
            format=src["format"],
            filename=src["filename"],
            description=src["description"],
            license=src["license"],
            user_agent=src.get("user_agent", "VoltSight-BI/1.0"),
            expected_min_rows=src.get("expected_min_rows", 0),
            primary_key=src.get("primary_key"),
            notes=src.get("notes", ""),
        )

    # Build pipeline config — bronze_dir resolved relative to repo root
    pipeline_raw = raw["pipeline"]
    bronze_dir_raw = pipeline_raw["bronze_dir"]
    bronze_dir = Path(bronze_dir_raw)
    if not bronze_dir.is_absolute():
        bronze_dir = _REPO_ROOT / bronze_dir

    pipeline = PipelineConfig(
        bronze_dir=bronze_dir,
        retry_attempts=pipeline_raw["retry_attempts"],
        retry_initial_wait_seconds=pipeline_raw["retry_initial_wait_seconds"],
        retry_max_wait_seconds=pipeline_raw["retry_max_wait_seconds"],
        http_timeout_seconds=pipeline_raw["http_timeout_seconds"],
        date_format=pipeline_raw["date_format"],
    )

    return VoltSightConfig(sources=sources, pipeline=pipeline)
