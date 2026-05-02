"""
HTTP client with retry logic for VoltSight BI.

Real-world data APIs fail. Government APIs especially fail at peak times
or under load. A professional ingestion pipeline assumes transient
failures and retries them gracefully.

This module wraps `requests` with exponential backoff retry behaviour
using the `tenacity` library — a standard production pattern.

Why this matters in interviews:
  - Demonstrates you understand production reliability concerns
  - Shows familiarity with modern Python libraries (tenacity)
  - Avoids the "naive download script that crashes on first 503" anti-pattern
"""

from __future__ import annotations

from pathlib import Path

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from voltsight.logger import get_logger

log = get_logger(__name__)


# Errors worth retrying — transient failures, not bad URLs or auth issues
_RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
)


class HTTPError(Exception):
    """Raised when an HTTP request fails after all retries."""


def download(
    url: str,
    destination: Path,
    user_agent: str,
    timeout: int,
    retry_attempts: int,
    retry_initial_wait: int,
    retry_max_wait: int,
) -> int:
    """
    Download a URL to a file path with retry-on-transient-failure.

    Args:
        url: Source URL to download.
        destination: File path to write to.
        user_agent: User-Agent header string.
        timeout: HTTP request timeout in seconds.
        retry_attempts: Total number of attempts before giving up.
        retry_initial_wait: Seconds to wait before first retry.
        retry_max_wait: Maximum seconds between retries (cap on backoff).

    Returns:
        Number of bytes written to destination.

    Raises:
        HTTPError: If download fails after all retries, or returns 4xx/5xx.
    """

    @retry(
        stop=stop_after_attempt(retry_attempts),
        wait=wait_exponential(
            multiplier=retry_initial_wait,
            max=retry_max_wait,
        ),
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(log, 30),  # WARNING level on retry
        reraise=True,
    )
    def _do_request() -> requests.Response:
        log.info(f"GET {url}")
        response = requests.get(
            url,
            headers={"User-Agent": user_agent},
            timeout=timeout,
            stream=True,
        )
        response.raise_for_status()
        return response

    try:
        response = _do_request()
    except requests.exceptions.HTTPError as e:
        # 4xx/5xx — not retryable in most cases; surface clearly
        raise HTTPError(
            f"HTTP {e.response.status_code} from {url}: {e.response.reason}"
        ) from e
    except _RETRYABLE_EXCEPTIONS as e:
        raise HTTPError(
            f"Failed to download {url} after {retry_attempts} attempts: {e}"
        ) from e

    # Stream to disk to handle large files without loading into memory
    destination.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = 0
    with destination.open("wb") as f:
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if chunk:
                f.write(chunk)
                bytes_written += len(chunk)

    log.info(
        f"Downloaded {bytes_written:,} bytes to {destination.name}"
    )
    return bytes_written
