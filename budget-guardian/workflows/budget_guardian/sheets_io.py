"""Google Sheets I/O for Budget Guardian.

Reads per-account budgets from the Budgets tab (columns A:C — Name, CID, Budget),
checks/sets the kill switch on the Guardian Config tab, and manages alert
state on the Guardian State tab to prevent duplicate alerts within a month.
"""

import logging
import os
from datetime import datetime, timezone

from workflows._shared.sheets_retry import execute_with_retry as _execute_with_retry

logger = logging.getLogger(__name__)


def _sheet_id() -> str:
    sheet_id = os.environ.get("GUARDIAN_SHEET_ID", "")
    if not sheet_id:
        raise RuntimeError("GUARDIAN_SHEET_ID environment variable not set")
    return sheet_id


def _budget_tab() -> str:
    return os.environ.get("GUARDIAN_BUDGET_TAB", "Budgets")


TAB_CONFIG = "Guardian Config"
TAB_STATE = "Guardian State"


def check_kill_switch(service) -> bool:
    """Return True if guardian is ENABLED, False if DISABLED."""
    result = _execute_with_retry(
        service.spreadsheets()
        .values()
        .get(spreadsheetId=_sheet_id(), range=f"'{TAB_CONFIG}'!A2")
    )
    values = result.get("values", [])
    if not values or not values[0]:
        logger.warning("Kill switch cell empty — treating as DISABLED")
        return False
    status = values[0][0].strip().upper()
    return status == "ENABLED"


def build_account_budget_map(service) -> list[dict]:
    """Read the Budgets tab (A:C) and return a list of per-account budgets.

    Expected columns:
        A — Account Name (label, used in Slack alerts)
        B — CID (digits only, no dashes)
        C — Monthly Budget (dollar amount, no currency symbol)

    Returns:
        [{cid, name, budget}, ...] — one entry per non-empty row.
        If a CID appears multiple times, budgets are summed.
    """
    result = _execute_with_retry(
        service.spreadsheets()
        .values()
        .get(spreadsheetId=_sheet_id(), range=f"'{_budget_tab()}'!A2:C200")
    )
    rows = result.get("values", [])

    budget_map: dict[str, dict] = {}

    for row in rows:
        if not row or len(row) < 3:
            continue

        name = row[0].strip()
        cid = row[1].strip().replace("-", "")
        budget_str = row[2].strip()

        if not name or not cid or not budget_str:
            continue

        # Parse budget: "$6,000.21" or "6000.21" -> 6000.21
        try:
            budget = float(budget_str.replace("$", "").replace(",", ""))
        except ValueError:
            logger.warning(f"Could not parse budget '{budget_str}' for '{name}' — skipping")
            continue

        if budget <= 0:
            continue

        if cid not in budget_map:
            budget_map[cid] = {"cid": cid, "name": name, "budget": budget}
        else:
            budget_map[cid]["budget"] += budget

    return list(budget_map.values())


def read_state(service) -> list[dict]:
    """Read the Guardian State tab.

    Columns: Month | CID | Account Name | Threshold | Action | Timestamp
    """
    result = _execute_with_retry(
        service.spreadsheets()
        .values()
        .get(spreadsheetId=_sheet_id(), range=f"'{TAB_STATE}'!A2:F")
    )
    rows = result.get("values", [])
    state = []
    for row in rows:
        while len(row) < 6:
            row.append("")
        state.append({
            "month": row[0].strip(),
            "cid": row[1].strip(),
            "name": row[2].strip(),
            "threshold": row[3].strip(),
            "action": row[4].strip(),
            "timestamp": row[5].strip(),
        })
    return state


def has_been_alerted(state: list[dict], cid: str, threshold: str, current_month: str) -> bool:
    """Check if we've already alerted for this CID + threshold this month."""
    for row in state:
        if row["month"] == current_month and row["cid"] == cid and row["threshold"] == threshold:
            return True
    return False


def write_state_row(
    service,
    current_month: str,
    cid: str,
    name: str,
    threshold: str,
    action: str,
):
    """Append a row to Guardian State tab."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    _execute_with_retry(
        service.spreadsheets().values().append(
            spreadsheetId=_sheet_id(),
            range=f"'{TAB_STATE}'!A:F",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={
                "values": [[current_month, cid, name, threshold, action, timestamp]]
            },
        )
    )


def clear_stale_state(service, current_month: str):
    """Remove state rows from previous months to keep the State tab small."""
    state = read_state(service)
    current_rows = [s for s in state if s["month"] == current_month]

    _execute_with_retry(
        service.spreadsheets().values().clear(
            spreadsheetId=_sheet_id(),
            range=f"'{TAB_STATE}'!A2:F",
        )
    )

    if current_rows:
        values = []
        for row in current_rows:
            values.append([
                row["month"], row["cid"], row["name"],
                row["threshold"], row["action"], row["timestamp"],
            ])
        _execute_with_retry(
            service.spreadsheets().values().update(
                spreadsheetId=_sheet_id(),
                range=f"'{TAB_STATE}'!A2:F",
                valueInputOption="RAW",
                body={"values": values},
            )
        )
