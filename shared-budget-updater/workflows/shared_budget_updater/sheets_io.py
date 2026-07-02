"""Google Sheets read/write for the Shared Budget Updater workflow."""

import logging
import os

from workflows._shared.sheets_retry import execute_with_retry

logger = logging.getLogger(__name__)

SHEET_ID = os.environ.get("UPDATER_SHEET_ID")
if not SHEET_ID:
    raise RuntimeError("UPDATER_SHEET_ID environment variable not set")
TAB = os.environ.get("SHEET_TAB") or "Shared Budget Uploader"


def read_unprocessed_rows(service) -> list[dict]:
    """Read rows where A/B/C exist and D is empty.

    Returns list of dicts: {row_num, customer_id, budget_id, budget_amount}
    """
    result = execute_with_retry(
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SHEET_ID, range=f"'{TAB}'!A:D")
    )

    rows = result.get("values", [])
    if not rows:
        return []

    unprocessed = []
    for i, row in enumerate(rows):
        if i == 0:
            continue

        # Pad to 4 columns
        while len(row) < 4:
            row.append("")

        col_a = row[0].strip()  # Customer ID (truncated CID)
        col_b = row[1].strip()  # Shared Budget ID
        col_c = row[2].strip()  # Budget amount
        col_d = row[3].strip()  # Done marker

        if col_a and col_b and col_c and not col_d:
            unprocessed.append(
                {
                    "row_num": i + 1,  # 1-indexed for Sheets API
                    "customer_id": col_a.replace("-", ""),  # Strip dashes
                    "budget_id": col_b,
                    "budget_amount": col_c,
                }
            )

    return unprocessed


def mark_rows_done(service, row_nums: list[int]):
    """Write 'x' to Col D for all processed rows in a single batch call."""
    if not row_nums:
        return

    data = [
        {"range": f"'{TAB}'!D{row_num}", "values": [["x"]]}
        for row_num in row_nums
    ]

    execute_with_retry(
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"valueInputOption": "RAW", "data": data},
        )
    )
