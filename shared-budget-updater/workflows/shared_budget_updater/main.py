"""Shared Budget Updater - Main entry point.

Reads shared budget update requests from a Google Sheet tab,
pushes them to Google Ads via REST API, and marks rows as done.
"""

import logging
import os
import sys
import traceback
from decimal import ROUND_HALF_UP, Decimal

from workflows._shared.google_ads_auth import get_ads_credentials
from workflows._shared.google_auth import get_sheets_service

from .ads_api import BudgetUpdateError, update_shared_budget
from .sheets_io import mark_rows_done, read_unprocessed_rows
from .slack import send_row_failures

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def dollars_to_micros(amount_str: str) -> int:
    """Convert dollar string to micros using Decimal to avoid float precision errors."""
    cleaned = amount_str.replace(",", "").replace("$", "")
    d = Decimal(cleaned).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(d * 1_000_000)


def process_row(row: dict, ads_creds: dict) -> dict:
    """Process a single budget update row (Ads API only, no Sheets write)."""
    row_num = row["row_num"]
    cid = row["customer_id"]
    budget_id = row["budget_id"]
    budget_amount = row["budget_amount"]

    logger.info(
        f"Row {row_num}: CID={cid}, Budget={budget_id}, Amount=${budget_amount}"
    )

    amount_micros = dollars_to_micros(budget_amount)

    if amount_micros <= 0:
        raise BudgetUpdateError(
            status_code=0,
            error_code="INVALID_AMOUNT",
            message="Budget amount must be greater than $0 — row skipped before any API call",
            trigger=budget_amount,
        )

    update_shared_budget(
        customer_id=cid,
        budget_id=budget_id,
        amount_micros=amount_micros,
        access_token=ads_creds["access_token"],
        developer_token=ads_creds["developer_token"],
        login_customer_id=ads_creds["login_customer_id"],
    )

    logger.info(f"  -> Budget updated: ${budget_amount} ({amount_micros} micros)")

    return {"row": row_num, "action": "updated", "cid": cid, "amount": budget_amount}


def main():
    """Main entry point - process ALL unprocessed rows."""
    logger.info("=" * 60)
    logger.info("SHARED BUDGET UPDATER")
    logger.info("=" * 60)

    sheets_service = get_sheets_service()
    ads_creds = get_ads_credentials()

    unprocessed = read_unprocessed_rows(sheets_service)
    logger.info(f"Found {len(unprocessed)} unprocessed row(s)")

    if not unprocessed:
        logger.info("Nothing to process. Exiting.")
        return

    results = {"processed": 0, "errors": 0}
    done_rows = []
    failed_rows: list[dict] = []

    for row in unprocessed:
        try:
            result = process_row(row, ads_creds)
            results["processed"] += 1
            done_rows.append(row["row_num"])
            logger.info(f"  -> OK: {result}")
        except BudgetUpdateError as e:
            results["errors"] += 1
            failed_rows.append(
                {
                    "row_num": row["row_num"],
                    "cid": row["customer_id"],
                    "budget_id": row["budget_id"],
                    "amount": row["budget_amount"],
                    "error_code": e.error_code,
                    "message": e.message,
                    "trigger": e.trigger,
                }
            )
            logger.error(
                f"  SKIPPED row {row['row_num']} (CID {row['customer_id']}): "
                f"[{e.error_code}] {e.message}"
            )
            continue
        except Exception as e:
            results["errors"] += 1
            failed_rows.append(
                {
                    "row_num": row["row_num"],
                    "cid": row["customer_id"],
                    "budget_id": row["budget_id"],
                    "amount": row["budget_amount"],
                    "error_code": "UNEXPECTED",
                    "message": str(e)[:500],
                    "trigger": "",
                }
            )
            logger.error(f"  ERROR on row {row['row_num']}:")
            logger.error(traceback.format_exc())
            continue

    # Batch-write all "done" markers in a single Sheets API call
    if done_rows:
        mark_rows_done(sheets_service, done_rows)
        logger.info(f"Marked {len(done_rows)} row(s) done in sheet")

    # Send a single consolidated Slack alert for all failed rows
    if failed_rows:
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
        try:
            send_row_failures(webhook_url, failed_rows, results["processed"])
        except Exception:
            logger.error("Slack notification failed:")
            logger.error(traceback.format_exc())

    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info(f"  Total rows:   {len(unprocessed)}")
    logger.info(f"  Processed:    {results['processed']}")
    logger.info(f"  Errors:       {results['errors']}")
    logger.info("=" * 60)

    # Exit 0 on partial failures — the Slack alert already carries the details.
    # The YAML failure() alert stays as a safety net for catastrophic errors
    # (auth failure, sheet read failure, etc.) that crash before this point.
    if results["errors"] > 0:
        logger.warning(f"{results['errors']} row(s) skipped — see Slack for details")


if __name__ == "__main__":
    main()
