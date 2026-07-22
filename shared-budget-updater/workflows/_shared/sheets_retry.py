"""Shared retry helper for Google Sheets API calls.

Retries on transient errors (5xx, 429 rate limit) with exponential backoff.
"""

import logging
import time

from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

MAX_RETRIES = 4
BACKOFF_BASE = 2  # seconds: 2, 4, 8, 16


def _is_transient(status: int) -> bool:
    return status >= 500 or status == 429


def execute_with_retry(request):
    """Execute a Sheets API request with retry on transient errors (5xx, 429)."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return request.execute()
        except HttpError as e:
            if _is_transient(e.resp.status) and attempt < MAX_RETRIES:
                wait = BACKOFF_BASE ** attempt
                logger.warning(
                    f"Sheets API {e.resp.status} error — retrying in {wait}s "
                    f"(attempt {attempt}/{MAX_RETRIES})"
                )
                time.sleep(wait)
                continue
            raise
