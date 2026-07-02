---
name: shared-budget-updater
description: Sheet-driven Google Ads shared budget automation. Approve a budget change by adding a row (CID, shared budget ID, amount) to a Google Sheet tab; a daily GitHub Actions cron pushes it via campaignBudgets:mutate (amount only), marks the row done, and sends one consolidated Slack alert for any failed rows. Failed rows retry next run; amounts of $0 or less never reach the API. Use this skill when the user asks to "set up shared budget updater", "push budget changes from a sheet", "bulk update shared budgets on a schedule", or wants a spreadsheet-approved budget pipeline.
allowed-tools: [Read, Write, Edit, Bash]
---

# Shared Budget Updater

A sheet-driven budget pusher for Google Ads. You (or your pacing process)
drop approved changes into a Google Sheet tab — customer ID, shared budget ID,
new amount. A daily GitHub Actions cron pushes each row to Google Ads and
marks it done. **This tool CHANGES live budgets** — the sheet is the approval
gate, so control who can edit the sheet.

## Why this exists

Budget pacing produces a daily list of "set budget X to $Y" decisions. Doing
them by hand in the Ads UI is slow and error-prone at portfolio scale; doing
them with ad-hoc scripts scatters mutation code everywhere. This gives the
decision list one narrow, auditable exit: a sheet row in, one
`campaignBudgets:mutate` (amount only) out, column D as the receipt.

Pairs with [Budget Guardian](../budget-guardian/) — the tripwire that watches
MTD spend against monthly budgets. This skill pushes the budgets; the Guardian
catches anything that then overspends them.

## Architecture

```
GitHub Actions (daily cron)
        |
        v
  Read uploader tab      ----->  Google Sheets API
  (rows where col D empty)       (your approved changes)
        |
        v
  For each row:
    amount <= $0?  -- yes -->  skip + alert (never reaches the API)
        |
        v
    campaignBudgets:mutate  -->  Google Ads API (REST)
    (updateMask: amount_micros)
        |
   ok?  +-- yes -->  mark col D "x"   -->  Google Sheets API
        |
        +-- no  -->  leave col D empty (retries next run)
                        |
                        v
             one consolidated Slack alert for all failed rows
```

## When Claude should invoke this skill

- User asks to "set up shared budget updater" or "deploy the budget updater"
- User wants to push budget changes from a spreadsheet on a schedule
- User asks to bulk-update shared budgets across accounts from a sheet
- User describes a pacing workflow that ends in manual budget edits and wants
  the execution automated behind a sheet-approval gate

## How Claude helps the user deploy this

1. Confirm prerequisites (Google Ads API access, Google Sheets OAuth token,
   Slack webhook, GitHub repo for the cron)
2. Walk through `README.md` setup — copying files, creating the sheet tab per
   `sheet-template.md`, setting GitHub secrets
3. Emphasize the safety model: whoever can edit the sheet can change spend —
   lock sheet sharing down before wiring credentials
4. Run the manual test from README Step 6 (one row, the user's OWN test
   account, $1 change, verify in Ads, revert)
5. Confirm the daily cron is firing in the Actions tab
6. For alert triage after deployment: `rules.md` (decision table) and
   `examples.md` (worked decisions)

## Files in this skill

| File | Purpose |
|------|---------|
| `SKILL.md` | This file |
| `README.md` | Full setup guide with step-by-step deployment |
| `rules.md` | Failure-alert triage rules + operating invariants |
| `examples.md` | Worked triage decisions, including edge cases |
| `requirements.txt` | Python dependencies |
| `sheet-template.md` | The uploader tab's column structure + semantics |
| `.github/workflows/shared-budget-updater.yml` | GitHub Actions daily cron config |
| `workflows/shared_budget_updater/main.py` | Entry point — row loop, $0 guard, exit-0 semantics |
| `workflows/shared_budget_updater/ads_api.py` | Google Ads REST mutate + retry + error taxonomy |
| `workflows/shared_budget_updater/sheets_io.py` | Sheet tab read/parse + column-D batch write |
| `workflows/shared_budget_updater/slack.py` | Consolidated failure alert formatting |
| `workflows/_shared/google_auth.py` | Google Sheets OAuth helper |
| `workflows/_shared/google_ads_auth.py` | Google Ads API OAuth helper |
| `workflows/_shared/sheets_retry.py` | Retry helper for transient Sheets errors |

## Configuration

All identity-bearing values are loaded from environment variables. Nothing is
hardcoded.

| Env var | Purpose |
|---------|---------|
| `UPDATER_SHEET_ID` | Google Sheet ID where the uploader tab lives (required) |
| `SHEET_TAB` | Tab name (default: `Shared Budget Uploader`) |
| `GOOGLE_TOKEN_PATH` | Path to your Google Sheets OAuth user token JSON |
| `GOOGLE_ADS_YAML_PATH` | Path to your Google Ads API YAML config |
| `SLACK_WEBHOOK_URL` | Incoming webhook for failure alerts |
| `SLACK_USER_MENTION` | Optional — Slack user/group to @-mention on alerts (e.g. `<@U12345>`) |

## Tested against

- Google Ads API v23 (REST)
- Python 3.12
- GitHub Actions (Ubuntu)
- Slack incoming webhooks (Block Kit)
- Google Sheets API v4 with OAuth user credentials

## What this skill deliberately does NOT do

- **No dry-run or approval prompt.** The sheet IS the approval surface — a row
  with column D empty is an approved change. Secure sheet access accordingly;
  that is the entire access model.
- **Never touches anything but the budget amount.** The mutation is
  `campaignBudgets:mutate` with `updateMask: amount_micros`. No statuses, no
  bidding, no campaign fields — and it should stay that way.
- **Exits 0 on partial failure by design.** Failed rows keep an empty column D
  and retry on the next run; the consolidated Slack alert is the failure
  signal. The yml `failure()` alert only fires on crashes.
- **No LLM in the loop.** Pure read-transform-mutate; Claude helps you deploy
  and triage, never executes budget changes itself.
