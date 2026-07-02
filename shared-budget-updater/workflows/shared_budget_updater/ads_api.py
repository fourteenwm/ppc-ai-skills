"""Google Ads REST API - shared budget mutation."""

import logging
import time

import requests

logger = logging.getLogger(__name__)

ADS_API_VERSION = "v23"
ADS_BASE_URL = f"https://googleads.googleapis.com/{ADS_API_VERSION}"

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds: 2, 4, 8
REQUEST_TIMEOUT = 90  # Google Ads API can be slow under load; 30s was too tight


class BudgetUpdateError(Exception):
    """Raised when a budget mutation fails. Carries structured detail for Slack/logging."""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        trigger: str = "",
        request_id: str = "",
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.trigger = trigger
        self.request_id = request_id
        super().__init__(f"[{error_code}] {message}")


def _parse_google_ads_error(resp: requests.Response) -> tuple[str, str, str, str]:
    """Extract (error_code, message, trigger, request_id) from a Google Ads API error response.

    Returns best-effort fields even if parsing partially fails.
    """
    try:
        body = resp.json()
    except ValueError:
        return ("UNKNOWN", resp.text[:500], "", "")

    err = body.get("error", {})
    top_message = err.get("message", "")
    details = err.get("details", [])

    error_code = "UNKNOWN"
    message = top_message
    trigger = ""
    request_id = ""

    for detail in details:
        request_id = detail.get("requestId", request_id)
        for sub in detail.get("errors", []):
            ec = sub.get("errorCode", {})
            if ec:
                # errorCode is a dict like {"mutateError": "FOO"} — take the value
                error_code = next(iter(ec.values()), error_code)
            if sub.get("message"):
                message = sub["message"]
            trig = sub.get("trigger", {})
            if trig.get("stringValue"):
                trigger = trig["stringValue"]

    return (error_code, message, trigger, request_id)


def update_shared_budget(
    customer_id: str,
    budget_id: str,
    amount_micros: int,
    access_token: str,
    developer_token: str,
    login_customer_id: str,
) -> dict:
    """Update a shared campaign budget's amountMicros via REST API.

    Retries up to 3 times on transient 500-level errors with exponential backoff.
    Returns the API response dict on success, raises BudgetUpdateError on failure.
    """
    url = f"{ADS_BASE_URL}/customers/{customer_id}/campaignBudgets:mutate"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": developer_token,
        "login-customer-id": login_customer_id,
        "Content-Type": "application/json",
    }

    body = {
        "operations": [
            {
                "update": {
                    "resourceName": f"customers/{customer_id}/campaignBudgets/{budget_id}",
                    "amountMicros": str(amount_micros),
                },
                "updateMask": "amount_micros",
            }
        ]
    }

    last_resp = None
    last_network_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=REQUEST_TIMEOUT)
            last_resp = resp
            last_network_error = None
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_network_error = e
            if attempt < MAX_RETRIES:
                wait = BACKOFF_BASE ** attempt
                logger.warning(
                    f"Network error ({type(e).__name__}) for CID {customer_id}, "
                    f"budget {budget_id} — retrying in {wait}s (attempt {attempt}/{MAX_RETRIES})"
                )
                time.sleep(wait)
                continue
            break

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code >= 500 and attempt < MAX_RETRIES:
            wait = BACKOFF_BASE ** attempt
            logger.warning(
                f"Transient error (HTTP {resp.status_code}) for CID {customer_id}, "
                f"budget {budget_id} — retrying in {wait}s (attempt {attempt}/{MAX_RETRIES})"
            )
            time.sleep(wait)
            continue

        break

    if last_network_error is not None:
        is_timeout = isinstance(last_network_error, requests.exceptions.Timeout)
        error_code = "TIMEOUT" if is_timeout else "CONNECTION_ERROR"
        message = f"{type(last_network_error).__name__}: {last_network_error}"
        logger.error(
            f"Network failure after {MAX_RETRIES} attempts for CID {customer_id}, "
            f"budget {budget_id}: [{error_code}] {message}"
        )
        raise BudgetUpdateError(
            status_code=0,
            error_code=error_code,
            message=message,
            trigger="",
            request_id="",
        )

    error_code, message, trigger, request_id = _parse_google_ads_error(last_resp)
    logger.error(
        f"API error {last_resp.status_code} for CID {customer_id}, "
        f"budget {budget_id}: [{error_code}] {message}"
    )
    raise BudgetUpdateError(
        status_code=last_resp.status_code,
        error_code=error_code,
        message=message,
        trigger=trigger,
        request_id=request_id,
    )
