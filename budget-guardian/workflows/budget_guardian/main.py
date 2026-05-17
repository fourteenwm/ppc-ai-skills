"""Budget Guardian — main entry point.

Monitors a Google Ads MCC's monthly spend against per-account budgets stored
in a Google Sheet. Sends Slack alerts at 100% (warning) and 120% (critical)
of monthly budget. Alert-only — never pauses campaigns.

Runs every 2 hours via GitHub Actions cron.

Environment variables:
    SLACK_WEBHOOK_URL       — required, incoming webhook for alerts
    GUARDIAN_SHEET_ID       — required, Sheet ID for budgets + state
    GUARDIAN_BUDGET_TAB     — optional, tab name (default: "Budgets")
    SLACK_USER_MENTION      — optional, e.g. "<@U01ABC23DEF>"
    GOOGLE_TOKEN_PATH       — required, path to Sheets OAuth token JSON
    GOOGLE_ADS_YAML_PATH    — required, path to Google Ads YAML
"""

import logging
import os
import sys
import traceback
from datetime import datetime, timezone

from workflows._shared.google_ads_auth import get_ads_credentials
from workflows._shared.google_auth import get_sheets_service

from .ads_api import get_mtd_spend
from .sheets_io import (
    build_account_budget_map,
    check_kill_switch,
    clear_stale_state,
    has_been_alerted,
    read_state,
    write_state_row,
)
from .slack import send_critical, send_error, send_warning

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

THRESHOLD_WARNING = 1.0   # 100%
THRESHOLD_CRITICAL = 1.2  # 120%


def main():
    logger.info("=" * 60)
    logger.info("BUDGET GUARDIAN")
    logger.info("=" * 60)

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        logger.error("SLACK_WEBHOOK_URL not set — exiting")
        sys.exit(1)

    if not os.environ.get("GUARDIAN_SHEET_ID"):
        logger.error("GUARDIAN_SHEET_ID not set — exiting")
        sys.exit(1)

    try:
        _run(webhook_url)
    except Exception:
        error_msg = traceback.format_exc()
        logger.error(f"Fatal error:\n{error_msg}")
        try:
            send_error(webhook_url, error_msg)
        except Exception:
            logger.error("Failed to send error to Slack")
        sys.exit(1)


def _run(webhook_url: str):
    now_utc = datetime.now(timezone.utc)
    current_month = now_utc.strftime("%Y-%m")

    # --- Sheets setup ---
    sheets = get_sheets_service()

    # Kill switch check
    if not check_kill_switch(sheets):
        logger.info("Kill switch is DISABLED — exiting")
        return

    # Clean up stale state from previous months
    clear_stale_state(sheets, current_month)

    # Read current state (alerts already fired this month)
    state = read_state(sheets)

    # --- Budget data ---
    budget_map = build_account_budget_map(sheets)
    logger.info(f"Loaded {len(budget_map)} account budgets from sheet")

    # --- Google Ads setup ---
    ads_creds = get_ads_credentials()

    stats = {"checked": 0, "warnings": 0, "critical": 0, "errors": 0}

    for acct in budget_map:
        cid = acct["cid"]
        name = acct["name"]
        budget = acct["budget"]

        try:
            spend = get_mtd_spend(cid, ads_creds)
        except Exception:
            logger.error(f"Failed to get spend for {name} ({cid}):")
            logger.error(traceback.format_exc())
            stats["errors"] += 1
            continue

        stats["checked"] += 1

        if spend == 0:
            continue

        ratio = spend / budget if budget > 0 else 0

        logger.info(f"{name} ({cid}): ${spend:,.2f} / ${budget:,.2f} = {ratio:.0%}")

        # Critical threshold (120%) — alert only, no pause
        if ratio >= THRESHOLD_CRITICAL:
            if not has_been_alerted(state, cid, "120%", current_month):
                logger.warning(f"CRITICAL: {name} at {ratio:.0%}")
                send_critical(webhook_url, name, cid, budget, spend)
                write_state_row(sheets, current_month, cid, name, "120%", "alerted")
                stats["critical"] += 1
            else:
                logger.info(f"  Already alerted for {name} at 120% this month — skipping")

        # Warning threshold (100%)
        elif ratio >= THRESHOLD_WARNING:
            if not has_been_alerted(state, cid, "100%", current_month):
                logger.warning(f"WARNING: {name} at {ratio:.0%}")
                send_warning(webhook_url, name, cid, budget, spend)
                write_state_row(sheets, current_month, cid, name, "100%", "warned")
                stats["warnings"] += 1
            else:
                logger.info(f"  Already alerted for {name} at 100% this month — skipping")

    # --- Summary ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info(f"  Accounts checked: {stats['checked']}")
    logger.info(f"  Warnings (100%):  {stats['warnings']}")
    logger.info(f"  Critical (120%):  {stats['critical']}")
    logger.info(f"  Errors:           {stats['errors']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
