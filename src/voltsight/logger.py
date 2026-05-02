"""
Structured logging for VoltSight BI.

Why this module exists:
  - Print statements are not professional. They can't be filtered, redirected,
    or parsed in production environments.
  - Using Python's standard `logging` module shows you understand
    real engineering practices.
  - One consistent log format across the project improves debuggability.

Usage:
    from voltsight.logger import get_logger
    log = get_logger(__name__)
    log.info("Starting ingestion", extra={"source": "ncr_chargers"})
"""

from __future__ import annotations

import logging
import sys
from typing import Any


_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _configure_root_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger once. Called automatically on first
    `get_logger` invocation.
    """
    root = logging.getLogger()
    if root.handlers:
        # Already configured by something else (e.g. pytest, jupyter)
        return

    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(fmt=_FORMAT, datefmt=_DATE_FORMAT)
    handler.setFormatter(formatter)
    root.addHandler(handler)


def get_logger(name: str, level: int | None = None) -> logging.Logger:
    """
    Get a configured logger for a module.

    Args:
        name: Logger name, typically `__name__` from the calling module.
        level: Optional override for this specific logger's level.

    Returns:
        Configured logging.Logger instance.
    """
    _configure_root_logger()
    log = logging.getLogger(name)
    if level is not None:
        log.setLevel(level)
    return log
