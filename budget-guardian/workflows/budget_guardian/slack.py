"""Slack webhook notifications for Budget Guardian (alert-only).

Uses Block Kit formatting. All @-mentions go through SLACK_USER_MENTION env var
so this file contains no identity-bearing values.
"""

import json
import logging
import os

import requests

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


def send_warning(webhook_url: str, name: str, cid: str, budget: float, spend: float):
    """100% threshold — warning only."""
    pct = (spend / budget * 100) if budget else 0
    mention = _mention()
    context_text = f"{mention + ' ' if mention else ''}No action taken. Monitor closely."
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Warning: Budget Hit 100%"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Account:*\n{name}"},
                {"type": "mrkdwn", "text": f"*CID:*\n{cid}"},
                {"type": "mrkdwn", "text": f"*Monthly Budget:*\n${budget:,.2f}"},
                {"type": "mrkdwn", "text": f"*MTD Spend:*\n${spend:,.2f} ({pct:.0f}%)"},
            ],
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": context_text}],
        },
    ]
    _post(webhook_url, blocks, f"Warning: {name} hit {pct:.0f}% of budget")


def send_critical(webhook_url: str, name: str, cid: str, budget: float, spend: float):
    """120% threshold — critical alert, investigate immediately."""
    pct = (spend / budget * 100) if budget else 0
    mention = _mention()
    context_text = f"{mention + ' ' if mention else ''}Investigate immediately. No campaigns were paused."
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "CRITICAL: Budget Exceeded 120%"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Account:*\n{name}"},
                {"type": "mrkdwn", "text": f"*CID:*\n{cid}"},
                {"type": "mrkdwn", "text": f"*Monthly Budget:*\n${budget:,.2f}"},
                {"type": "mrkdwn", "text": f"*MTD Spend:*\n${spend:,.2f} ({pct:.0f}%)"},
            ],
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": context_text}],
        },
    ]
    _post(webhook_url, blocks, f"CRITICAL: {name} at {pct:.0f}% of budget — investigate immediately")


def send_error(webhook_url: str, error_message: str):
    """Script failure notification."""
    mention = _mention()
    header_text = f"{mention + ' ' if mention else ''}Budget Guardian: Script Error"
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Budget Guardian: Script Error"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"```{error_message[:2900]}```",
            },
        },
    ]
    _post(webhook_url, blocks, header_text + " — " + error_message[:200])
