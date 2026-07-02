---
name: budget-guardian
description: Monitors a Google Ads MCC for monthly budget overruns and sends Slack alerts at 100% and 120% of monthly budget per account. Designed to catch hijacked accounts, runaway PMax campaigns, and pacing-sheet formula errors within 2 hours instead of 24+. Alert-only — never pauses campaigns. Runs on GitHub Actions on a 2-hour cron. Use this skill when the user asks to "set up budget guardian", "install spend alerts", monitor MCC spend, or build a tripwire against unauthorized PMax campaigns.
allowed-tools: [Read, Write, Edit, Bash]
---

# Budget Guardian

A spend tripwire for your Google Ads MCC. Scans every enabled account in your MCC every 2 hours. If month-to-date spend crosses 100% or 120% of the monthly budget you set, it pings Slack. **Alert-only — never pauses campaigns.**

Pairs with [Shared Budget Updater](../shared-budget-updater/) — the execution arm: it pushes sheet-approved budgets; the Guardian is the tripwire watching what gets spent against them.

## Why this exists

Two threats with the same shape — a spend spike nobody noticed until the damage was done.

The first is fat-fingering: a wrong formula or stale value in a budget sheet quietly pushing the wrong number across multiple accounts. The second is the industry-wide trend of hijacked MCCs and malicious spend — unauthorized PMax campaigns at huge daily budgets, drained accounts, agency-level changes nobody approved.

Daily checks miss the first 23 hours of either one. A 2-hour cron with per-threshold dedupe gets detection to ~2 hours, with one alert per account per threshold per month so Slack doesn't get spammed.

## Architecture

```
GitHub Actions (every 2 hours)
        |
        v
  Read budget sheet     ----->  Google Sheets API
        |                       (your per-account monthly budgets)
        v
  For each account:
    Query MTD spend     ----->  Google Ads API v23
        |                       (segments.date DURING THIS_MONTH)
        v
    Compare to budget
        |
        v
    Cross threshold?    ----->  Slack webhook
        |                       (100% warning / 120% critical)
        v
    Record alert        ----->  Google Sheets API
                                (state tab — dedupe within month)
```

## When Claude should invoke this skill

- User asks to "set up budget guardian", "install spend alerts", or "deploy budget guardian"
- User asks how to monitor MCC spend or catch hijacked accounts
- User asks about per-account budget alerting via Slack
- User describes an MCC hijack scenario, runaway PMax, or fat-fingered budget concerns

## How Claude helps the user deploy this

1. Confirm prerequisites are in place (Google Ads API access, Google Sheets OAuth token, Slack workspace, GitHub repo for the cron)
2. Walk through `README.md` setup steps — copying files, setting GitHub secrets, creating the budget sheet
3. Run `setup_tabs.py` once to bootstrap the `Guardian Config` and `Guardian State` tabs
4. Trigger a manual test run via `workflow_dispatch` to confirm Slack receives the test message
5. Set the kill switch to `ENABLED` in the sheet
6. Confirm the 2-hour cron is firing in the Actions tab

## Files in this skill

| File | Purpose |
|------|---------|
| `SKILL.md` | This file |
| `README.md` | Full setup guide with step-by-step deployment |
| `rules.md` | Alert-triage decision logic (invariants + triage table) |
| `examples.md` | Worked triage decisions, including the edge cases |
| `requirements.txt` | Python dependencies |
| `sheet-template.md` | Google Sheet column structure |
| `.github/workflows/budget-guardian.yml` | GitHub Actions cron config (every 2 hours) |
| `workflows/budget_guardian/main.py` | Entry point — orchestrates checks |
| `workflows/budget_guardian/ads_api.py` | Google Ads API client (MCC scan + MTD spend) |
| `workflows/budget_guardian/sheets_io.py` | Sheet reads/writes for budgets + state |
| `workflows/budget_guardian/slack.py` | Slack alert formatting |
| `workflows/budget_guardian/setup_tabs.py` | One-time bootstrap of Config + State tabs |
| `workflows/_shared/google_auth.py` | Google Sheets OAuth helper |
| `workflows/_shared/google_ads_auth.py` | Google Ads API OAuth helper |
| `workflows/_shared/sheets_retry.py` | Retry helper for transient Sheets errors |

## Configuration

All identity-bearing values are loaded from environment variables. Nothing is hardcoded.

| Env var | Purpose |
|---------|---------|
| `GUARDIAN_SHEET_ID` | Google Sheet ID where budgets and state live |
| `GUARDIAN_BUDGET_TAB` | Tab name with per-account budgets (default: `Budgets`) |
| `GOOGLE_TOKEN_PATH` | Path to your Google Sheets OAuth user token JSON |
| `GOOGLE_ADS_YAML_PATH` | Path to your Google Ads API YAML config |
| `SLACK_WEBHOOK_URL` | Incoming webhook URL for the channel that should receive alerts |
| `SLACK_USER_MENTION` | Optional — Slack user/group to @-mention on alerts (e.g. `<@U12345>`) |

## Tested against

- Google Ads API v23
- Python 3.12
- GitHub Actions (Ubuntu)
- Slack incoming webhooks (Block Kit)
- Google Sheets API v4 with OAuth user credentials
- Portfolios of 20-90 accounts

## What this skill deliberately does NOT do

- **Does not pause campaigns.** Alert-only by design. Auto-pause has too many failure modes for a public-default skill.
- **Does not modify Google Ads.** Read-only access is sufficient.
- **Does not need Anthropic credentials.** No LLM call in the loop — pure threshold math.
- **Does not require a brain.** Runs standalone on GitHub Actions; the SKILL.md just helps Claude help you deploy it.

## Production twin & behavior parity

This bundle is the generic replica of a production automation running on the
same architecture every 2 hours. The two stay in **behavioral sync** on the
parity set: thresholds 1.0/1.2 · kill-switch fail-closed semantics · state
schema (`Month | CID | Account Name | Threshold | Action | Timestamp`) +
per-account/threshold/month dedupe + stale-month clear · alert shape.

Ingestion differs **BY DESIGN**: this bundle reads a direct-CID `Budgets` tab
(A:C — Name, CID, Monthly Budget); the production twin discovers accounts via
an MCC label and reads a pre-aggregated budget export. Env names + branding
also differ by design. Drift between the two is reviewed against the parity
set, never byte-synced.
