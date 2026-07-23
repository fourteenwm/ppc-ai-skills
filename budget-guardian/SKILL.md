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

Once deployed, the work shifts from setup to triage: every alert gets read
per [`rules.md`](rules.md) before anyone acts on it.

## When an alert fires — where it routes

Triage itself lives in [`rules.md`](rules.md) (read it before acting on any
alert; [`examples.md`](examples.md) shows worked reads). What triage
surfaces routes to siblings:

| Trigger | Load |
|---------|------|
| 120% incident — need who/what/when on recent changes | [`change-history-checker`](../change-history-checker/) |
| Change history shows actors or campaigns nobody authorized | [`mcc-hack-audit`](../mcc-hack-audit/) — sweep the whole MCC, not just the alerting account |
| "What should this account's budget actually be?" | [`budget-recommendation-calculator`](../budget-recommendation-calculator/) — its answer goes in the `Budgets` tab |
| "Is this spend pace normal?" — variance context for the book | [`portfolio-pacing-rules`](../portfolio-pacing-rules/) |
| A human approved a budget change and wants it executed via sheet | [`shared-budget-updater`](../shared-budget-updater/) — the execution arm; the Guardian never writes |
| "Why did/didn't this alert fire?" — exact thresholds, dedupe, parse rules | [`references/alert-contract.md`](references/alert-contract.md) |

## Files in this skill

| File | Purpose |
|------|---------|
| `SKILL.md` | This file |
| `README.md` | Full setup guide with step-by-step deployment |
| `rules.md` | Judgment layer: triage table, false-alarm classes, threshold tuning, kill-switch guidance, roster rules |
| `examples.md` | Worked triage decisions, including the edge cases |
| `references/alert-contract.md` | Exact thresholds, alert shapes, state/dedupe semantics, parse rules, env vars, parity set |
| `requirements.txt` | Python dependencies |
| `sheet-template.md` | Google Sheet tab structure — copy this to build your sheet |
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

All identity-bearing values are loaded from environment variables — nothing
identity-bearing is hardcoded. The full env-var table lives in
[`references/alert-contract.md`](references/alert-contract.md); `README.md`
Step 5 maps each one to a GitHub Actions secret. (The alert thresholds are
constants in the code, not env vars — tuning logic in [`rules.md`](rules.md).)

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
same architecture. The two stay in **behavioral sync** on the
parity set — the exact set, and the by-design divergences (ingestion halves,
env names, branding), are defined in
[`references/alert-contract.md`](references/alert-contract.md) § Parity with
the production twin. Drift between the two is reviewed against that set,
never byte-synced.
