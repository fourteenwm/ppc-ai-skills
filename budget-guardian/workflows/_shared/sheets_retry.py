"""Shared retry helper for Google Sheets API calls.

Retries on transient 5xx errors with exponential backoff.
"""

import logging
import time

from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds: 2, 4, 8


def execute_with_retry(request):
    """Execute a Sheets API request with retry on transient errors (5xx)."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return request.execute()
        except HttpError as e:
            if e.resp.status >= 500 and attempt < MAX_RETRIES:
                wait = BACKOFF_BASE ** attempt
                logger.warning(
                    f"Sheets API {e.resp.status} error — retrying in {wait}s "
                    f"(attempt {attempt}/{MAX_RETRIES})"
                )
                time.sleep(wait)
                continue
            raise
