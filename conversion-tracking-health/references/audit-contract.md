# Audit Contract — what the two scripts actually check and print

> **Source of truth:** the scripts win wherever this file and the code
> disagree — `scripts/portfolio_conversion_audit.py` (portfolio scan) and
> `scripts/last_conversion_dates_by_action.py` (single-account deep-dive).
> Revised 2026-07-24; update this file and the CHANGELOG together whenever
> either script changes.

Both scripts are read-only and **console-only — nothing is ever written to
disk**. Copy findings out before the terminal scrolls; the console output is
the entire record.

## Shared: which conversion actions are even looked at

- Query: all `conversion_action` rows where status ≠ `REMOVED` — so both
  `ENABLED` and `HIDDEN` actions are in scope.
- Ten action types are filtered out before any analysis: `STORE_VISITS`,
  `GOOGLE_HOSTED` (local actions, clicks-to-call), and the eight
  Android/iOS/Firebase app types. The skill audits **website** conversion
  tracking.
- Actions are keyed by **name**. Two conversion actions sharing one name
  collapse into a single entry (the later row wins) — duplicate-named
  actions are indistinguishable in this audit.

## Portfolio scan (`portfolio_conversion_audit.py`)

**Account list.** `--cid`, `--cids`, and `--accounts-file` **combine** —
all three append to one list, in that file-then-cids-then-cid order.
Duplicates are not deduped (a CID listed twice is audited twice and its
findings print twice). CSV format: `cid,name` per row, no header, BOM
tolerated, dashes stripped from CIDs, missing name defaults to `CID
<number>`. A missing CSV file prints an error and continues with whatever
the other flags provided; an empty final list exits 1.

**The spend gate.** Before auditing, each account is checked for any spend
in the **last 7 days** (fixed window — `--days` does not change it; the
window spans 8 calendar dates including today's partial). No spend →
`  [skipped] {name} (no spend in last 7 days)` and the account is never
queried further. `--include-no-spend` bypasses the gate entirely.

**What counts as fired.** The conversion query pulls
`metrics.conversions > 0` segmented by action name and date, over `--days`
(default 90; the window spans days+1 dates including today's partial).
`metrics.conversions` is the **primary-only** measure — and the evaluation
loop additionally skips any action with
`include_in_conversions_metric = false`. Observation-only (secondary)
actions are invisible to this script in both directions: they're never
listed, healthy or broken.

**Severity buckets** (from `days_ago` = calendar days since the last date
with primary conversions; today = 0):

| Bucket | Condition | Shown |
|---|---|---|
| Healthy | ≤ 14 days | Never — healthy rows are suppressed |
| Warning | 15-30 days | Yes, sorted oldest-first |
| Stale | 31+ days | Yes, sorted oldest-first |
| No recent conversions | zero primary conversions **in the window**, and the action's status is `ENABLED` | Yes, in scan order |

Two consequences worth reading twice:

- **"Never fired" means "not in the last `--days` days".** With the default
  90-day lookback, an action that last fired 91+ days ago prints `Never
  fired` — it may have a long healthy history. Widen `--days` (or run the
  deep-dive) to date the actual last fire before concluding the tag never
  worked.
- A `HIDDEN` action that stopped firing disappears entirely (the no-data
  bucket requires `ENABLED`), while a `HIDDEN` action still firing can
  appear as Warning/Stale.

**Console shapes** (what the emitting code prints — no emoji, no portfolio
name in the header):

```
PORTFOLIO CONVERSION AUDIT
====================================================================================================
Accounts to audit: 12
Lookback period: 90 days
...
  [ok] Halstead Dental
  [skipped] Kingsbury Storage (no spend in last 7 days)

Audit complete. Checked 11 accounts, skipped 1 (no spend).
...
NO RECENT CONVERSIONS (90+ days) - 4 issues
STALE (30+ days) - 2 issues
WARNING (15-30 days) - 3 issues
```

The no-data header interpolates your `--days` value. Table columns are 50 |
40 | 15 wide with account names truncated at 48 characters and action names
at 38. A clean run prints `NO ISSUES FOUND - All conversion actions are
healthy.` The summary block repeats the three counts with aligned labels
(`  No recent data:       4`).

**Error isolation — the trap set.** Per-account failures never stop the
batch, and they never get their own summary line. Three distinct error paths
produce three misleadable outputs:

| Error print (above the account line) | The account then shows as | Why that's a trap |
|---|---|---|
| `Error checking spend for {cid}: …` | `[skipped] … (no spend in last 7 days)` | An auth/access failure masquerades as a paused account |
| `Error querying conversion actions: …` | `[ok]` with zero findings | A failed account masquerades as a healthy one |
| `Error auditing {name}: …` | `[ok]`, possibly with partial findings | Late failure; whatever was bucketed before it still counts |

The error lines are the ONLY trace — always scan for them before trusting
`[ok]`, `[skipped]`, or the summary arithmetic.

**The zero-actions blind spot.** An account with NO website conversion
actions configured prints `[ok]` with zero findings — this audit reports on
configured-but-quiet actions and never flags absent tracking. Missing-
conversion-setup detection belongs to
[`account-diagnostic`](../../account-diagnostic/).

## Single-account deep-dive (`last_conversion_dates_by_action.py`)

The complement to the portfolio scan: **every** action including healthy
ones, and **both** primary and observation actions.

- **Measure:** `metrics.all_conversions > 0` — observation-only actions
  count here. Every listed action carries an `(in)` (in the Conversions
  column) or `(obs)` (observation-only) marker. Same 15/30-day thresholds;
  the healthy bucket is *shown* here (sorted most-recent-first, `today`
  rendered at 0 days); never-fired-in-window includes non-`ENABLED` actions
  with their status printed (the `INVESTIGATE` nudge appears only on
  `ENABLED` rows).
- **No `--config` flag.** Credentials are read from `./google-ads.yaml` in
  the working directory, full stop — run it from the project root.
- **Name resolution is NOT an MCC walk.** The positional account name is
  matched against `CustomerService.list_accessible_customers()` — the
  accounts your OAuth user can access *directly*. Under a typical MCC
  login that list is the manager account itself, not the client accounts —
  so name lookup usually finds nothing and exits 1 (`Error: Could not find
  account matching '…'`). **Pass `--cid` — it's the reliable path** (dashes
  are stripped).
- **Two early exits, both exit 0:**
  - Zero website actions configured (and none filtered) → `WARNING: No
    conversion actions found in account!` — nothing else prints. (If
    actions existed but ALL were filtered types, the run continues and
    reports `Found 0 website conversion actions configured` with empty
    analysis — an account running only call-and-store-type tracking looks
    empty here by design.)
  - Zero conversions of any kind in the window → `WARNING: No conversions
    found in the lookback period!` plus a suggestion to raise `--days`,
    **before the per-action analysis** — the completely-quiet account
    produces the least-detailed output exactly when things look worst. Read
    the STEP 1 configured-actions list, then re-run with a wider `--days`.

## Cross-script asymmetry (same account, different answers — by design)

| | Portfolio scan | Deep-dive |
|---|---|---|
| Actions covered | Primary only | Primary + observation |
| Metric | `metrics.conversions` | `metrics.all_conversions` |
| Healthy actions | Suppressed | Listed |
| Accounts per run | Many (spend-gated) | One |
| Credentials | `--config` supported | `./google-ads.yaml` only |

An observation-only action can show STALE in the deep-dive while the
portfolio scan never mentions it; an action recently demoted from primary to
secondary *vanishes* from the portfolio scan without being fixed or broken.
When the two outputs disagree, this table is usually why.
