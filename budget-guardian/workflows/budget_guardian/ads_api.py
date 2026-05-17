"""Google Ads REST API — month-to-date spend queries.

One query per account per run: SELECT metrics.cost_micros FROM customer
WHERE segments.date DURING THIS_MONTH.

Read-only. The Guardian never mutates anything in Google Ads.
"""

import logging

import requests

logger = logging.getLogger(__name__)

ADS_API_VERSION = "v23"
ADS_BASE_URL = f"https://googleads.googleapis.com/{ADS_API_VERSION}"


def _headers(access_token: str, developer_token: str, login_customer_id: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "developer-token": developer_token,
        "login-customer-id": login_customer_id,
        "Content-Type": "application/json",
    }


def _search(cid: str, query: str, headers: dict) -> list[dict]:
    """Execute a GAQL search query and return all rows."""
    url = f"{ADS_BASE_URL}/customers/{cid}/googleAds:search"
    body = {"query": query}
    resp = requests.post(url, json=body, headers=headers, timeout=60)
    if resp.status_code != 200:
        logger.error(f"API error {resp.status_code} for CID {cid}: {resp.text}")
        resp.raise_for_status()
    return resp.json().get("results", [])


def get_mtd_spend(cid: str, ads_creds: dict) -> float:
    """Get month-to-date spend in dollars for a single account.

    Args:
        cid: Customer ID (digits only, no dashes)
        ads_creds: Dict with access_token, developer_token, login_customer_id

    Returns:
        Month-to-date spend in dollars.
    """
    hdrs = _headers(
        ads_creds["access_token"],
        ads_creds["developer_token"],
        ads_creds["login_customer_id"],
    )
    query = (
        "SELECT metrics.cost_micros "
        "FROM customer "
        "WHERE segments.date DURING THIS_MONTH"
    )
    rows = _search(cid, query, hdrs)
    total_micros = 0
    for row in rows:
        total_micros += int(row.get("metrics", {}).get("costMicros", 0))
    return total_micros / 1_000_000
