# Alert Contract — exactly what fires, when, and what gets recorded

The precise thresholds, alert shapes, state semantics, ingestion rules, and
failure behavior of the Guardian. Use this to answer "why did (or didn't)
this alert fire?" without reading the engine.

> **Source of truth:** the workflow code — `workflows/budget_guardian/main.py`
> (thresholds, run order), `sheets_io.py` (ingestion, kill switch, state),
> `slack.py` (alert shapes), `ads_api.py` (spend query). This document
> mirrors the code as of its 2026-07-22 revision. If you change the workflow,
> update the matching section here and add a CHANGELOG entry.

---

## Thresholds — the exact math

Two constants, hardcoded in `main.py` (not environment variables):

| Constant | Value | Fires |
|----------|-------|-------|
| `THRESHOLD_WARNING` | `1.0` | **Warning** at MTD spend ≥ 100% of monthly budget |
| `THRESHOLD_CRITICAL` | `1.2` | **Critical** at MTD spend ≥ 120% of monthly budget |

Comparison is `>=` on `ratio = MTD spend / monthly budget`. Tuning them means
editing your copy of `main.py` — the decision logic for when that's the right
move (versus fixing a budget number) is in [`rules.md`](../rules.md).

**The two checks are if/elif — critical wins.** An account crossing both
thresholds in one run gets only the Critical alert. Because state is keyed
per threshold, an account that jumps straight past 120% **never receives a
100% Warning that month** — on later runs the ratio still lands in the
critical branch (already alerted → skip) and the warning branch is never
reached. One Slack message for that account that month, not two.

**Checked before either threshold:**

- Accounts with **zero MTD spend are skipped** — no ratio computed, no alert
  ever. (This is why silence on a dark account proves nothing; see the
  Silence row in `rules.md`.)
- A budget of zero or less never reaches the comparison — those rows are
  dropped at ingestion (below).

## MTD spend — what's being measured

One query per account per run:

```sql
SELECT metrics.cost_micros FROM customer
WHERE segments.date DURING THIS_MONTH
```

Calendar month-to-date, account level, summed across everything the account
spent (all campaign types). Resets to zero at the month boundary. Micros are
converted to dollars before comparison. Read-only — the Guardian holds no
mutate scope anywhere.

## The three alert shapes

All alerts are Slack Block Kit messages. If `SLACK_USER_MENTION` is set, the
mention is prepended to the context line (Warning/Critical) or header line
(Script Error).

| Alert | Header (exact) | Body | Context line |
|-------|----------------|------|--------------|
| Warning | `Warning: Budget Hit 100%` | Account, CID, Monthly Budget, MTD Spend (with %) | `No action taken. Monitor closely.` |
| Critical | `CRITICAL: Budget Exceeded 120%` | Same four fields | `Investigate immediately. No campaigns were paused.` |
| Script Error | `Budget Guardian: Script Error` | The traceback, truncated to 2,900 characters | — |

The headers always say "100%"/"120%" — they are literal strings in
`slack.py`, independent of the threshold constants. Tune a constant without
updating the labels and the alerts will mislabel themselves.

A Script Error means the **run itself** crashed (auth, code, fatal API
failure) — it is not tied to any account. Per-account query failures do NOT
produce a Slack alert; they are logged and counted (see Failure contract).

## State & dedupe — one alert per account per threshold per month

Alert history lives in the `Guardian State` tab (layout and column reference:
[`sheet-template.md`](../sheet-template.md) — auto-created by
`setup_tabs.py`). What the workflow guarantees:

- **Dedupe key = Month + CID + Threshold**, exact string match. Month is
  `YYYY-MM` (UTC); Threshold is the literal string `100%` or `120%` (these
  strings are independent of the constants — tuning a constant does not
  invalidate existing state rows).
- **Action** records `warned` (100%) or `alerted` (120%); **Timestamp** is
  UTC, `YYYY-MM-DD HH:MM UTC`.
- A state row is appended **immediately after each successful send** — so a
  run that crashes mid-loop has recorded every alert it actually sent, and
  the next run resumes without duplicating them.
- **Stale-month clear:** at the start of every run, rows from previous
  months are removed (the tab is wiped and current-month rows rewritten).
  The State tab therefore only ever shows the current month.
- **Deleting a current-month row re-arms that alert** — the next run sees no
  prior alert for that key and fires fresh. This is the intended manual
  reset (e.g. after raising a budget mid-month).

## Budgets-tab ingestion — what makes a row count

The Guardian reads `A2:C200` of the budget tab (name from
`GUARDIAN_BUDGET_TAB`, default `Budgets`; layout:
[`sheet-template.md`](../sheet-template.md)). **The tab is the entire
roster** — there is no MCC discovery; an account not listed is not watched.

Per-row parse ladder, in order:

| Row condition | Result | Visible where? |
|---------------|--------|----------------|
| Empty row, or fewer than 3 cells | Skipped | Nowhere — silent |
| Any of Name / CID / Budget blank after trimming | Skipped | Nowhere — silent |
| Budget cell unparseable as a number | Skipped | Run log only: `Could not parse budget '<value>' for '<name>' — skipping` |
| Budget parses to zero or negative | Skipped | Nowhere — silent |
| Row past 200 | Never read | Nowhere — widen the range in `sheets_io.py` if your book is bigger |

Tolerated formats: CIDs may contain dashes (stripped); budgets may contain
`$` and commas (stripped). **Duplicate CIDs are summed** into one entry —
multiple rows for one account is a supported way to split a budget.

No skip of any kind produces a Slack alert. The judgment layer for what this
model means for coverage — and the deliberate-unwatch idiom — is in
[`rules.md`](../rules.md).

## Kill switch — read semantics

Checked first thing every run, from `'Guardian Config'!A2`:

- Only the exact word `ENABLED` (case-insensitive, trimmed) enables.
- **Anything else — including an empty cell, a missing tab, or a typo —
  reads as DISABLED** (fail-closed), with a run-log warning when the cell is
  empty.
- A disabled run exits **immediately and successfully**: no budgets read, no
  accounts queried, no alerts — and the Actions run shows green. A healthy
  Actions history is NOT proof monitoring is on; the switch cell is.

## Run & failure contract

- **Schedule:** GitHub Actions cron `0 */2 * * *` (every 2 hours, UTC) plus
  manual `workflow_dispatch`; 10-minute job timeout.
- **Startup guard:** missing `SLACK_WEBHOOK_URL` or `GUARDIAN_SHEET_ID`
  exits 1 before any work.
- **Per-account isolation:** a failed spend query logs the traceback, counts
  in the summary's `Errors:` line, and the run continues with the next
  account. No Slack alert per se — watch the summary count.
- **Fatal failure:** any crash outside the per-account loop sends the Script
  Error alert and exits 1 (red run in Actions).
- **Sheets resilience:** every Sheets call retries transient errors (HTTP
  5xx and 429 rate-limit) up to 4 attempts with exponential backoff
  (2/4/8/16s) before failing.
- **Credentials hygiene:** secrets are written to runner-local temp files at
  step start and deleted in an `always()` cleanup step, success or failure.

## Reading run state cold

Two surfaces tell a fresh session everything, without Slack history:

1. **The Actions run log** (Actions → Budget Guardian → latest run) — what
   ran and when, every account checked with its `$MTD / $budget = %` line,
   parse-skip warnings, and the closing `SUMMARY` block (checked / warnings /
   critical / errors counts).
2. **The `Guardian State` tab** — every alert actually sent this month, with
   threshold and timestamp. Empty state + green runs + `ENABLED` switch =
   genuinely quiet month.

Slack shows alerts only once per key per month — absence of a Slack message
is never evidence by itself.

## Environment variables

All identity-bearing configuration. The GitHub-secrets mapping (what to
paste where) is `README.md` Step 5; this is what the code reads at runtime:

| Env var | Required | Purpose |
|---------|----------|---------|
| `GUARDIAN_SHEET_ID` | Yes | Google Sheet ID where budgets and state live |
| `GUARDIAN_BUDGET_TAB` | No (default `Budgets`) | Tab name with per-account budgets |
| `GOOGLE_TOKEN_PATH` | Yes | Path to the Google Sheets OAuth user token JSON |
| `GOOGLE_ADS_YAML_PATH` | Yes | Path to the Google Ads API YAML config |
| `SLACK_WEBHOOK_URL` | Yes | Incoming webhook for the alerts channel |
| `SLACK_USER_MENTION` | No | Slack user/group to @-mention on alerts (e.g. `<@U12345>`) |

## Parity with the production twin

This bundle is the generic replica of a production automation running the
same architecture. The two stay in **behavioral sync** on the parity set,
which is exactly the contract above:

- Thresholds and comparison semantics (§ Thresholds)
- Kill-switch fail-closed semantics (§ Kill switch)
- State schema, dedupe key, and stale-month clear (§ State & dedupe)
- Alert shapes (§ The three alert shapes)

**Different by design — never synced:** the ingestion halves (this bundle
reads a direct-CID `Budgets` tab; the production twin discovers accounts via
an MCC label and reads a pre-aggregated budget export), environment-variable
names, and branding. Drift between the twins is reviewed against the parity
set, hunk by hunk — never byte-synced.

**If you deploy this:** the parity set binds the author's twin relationship,
not your install. Your copy is yours to tune — see the threshold-tuning
rules in [`rules.md`](../rules.md).
