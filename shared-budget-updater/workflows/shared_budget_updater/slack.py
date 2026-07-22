"""Slack webhook notifications for the Shared Budget Updater.

Consolidated row-failure alerts. All @-mentions go through the
SLACK_USER_MENTION env var so this file contains no identity-bearing values.
"""

import json
import logging
import os

import requests

from workflows._shared.mutate_error_hints import hint_for

logger = logging.getLogger(__name__)


def _mention() -> str:
    """Optional @-mention to prepend to context lines. Empty string if not set."""
    return os.environ.get("SLACK_USER_MENTION", "").strip()


def _post(webhook_url: str, blocks: list, text: str):
    """Send a Block Kit message to Slack."""
    payload = {"text": text, "blocks": blocks}
    resp = requests.post(
        webhook_url,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    if resp.status_code != 200:
        logger.error(f"Slack error {resp.status_code}: {resp.text}")
    return resp


def send_row_failures(webhook_url: str, failed: list[dict], processed_count: int):
    """Alert when one or more rows failed. Other rows continue processing.

    failed: list of dicts with keys row_num, cid, budget_id, amount, error_code, message, trigger.
    processed_count: number of rows that succeeded in the same run.
    """
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping Slack alert")
        return

    lines = []
    for f in failed:
        trig = f" _(trigger: `{f['trigger']}`)_" if f.get("trigger") else ""
        lines.append(
            f"• *Row {f['row_num']}* — CID `{f['cid']}`, Budget `{f['budget_id']}`, "
            f"`${f['amount']}`\n"
            f"   `{f['error_code']}`: {f['message']}{trig}"
        )
        hint = hint_for(f.get("error_code", ""))
        if hint:
            lines.append(f"   :point_right: {hint}")
    body = "\n".join(lines)

    mention = _mention()
    context_text = (
        f"{mention + ' ' if mention else ''}{processed_count} other row(s) processed OK. "
        "Skipped rows still have empty Col D — they'll retry on the next run."
    )

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Shared Budget Updater: {len(failed)} row(s) skipped",
            },
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": body[:2900]},
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": context_text,
                },
            ],
        },
    ]
    _post(webhook_url, blocks, f"Shared Budget Updater: {len(failed)} row(s) skipped")
