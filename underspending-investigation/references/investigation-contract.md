# Investigation Contract — what `investigate_underspend.py` actually prints

> **Source of truth:** `scripts/investigate_underspend.py` wins wherever this
> file and the script disagree — the contract documents shipped behavior, it
> doesn't define it. The diagnostic frameworks belong to the companion skills
> (`portfolio-pacing-rules`, `impression-share-diagnostics`,
> `budget-recommendation-calculator`); this file covers only what the script
> emits. Revised 2026-07-24; update this file and the CHANGELOG together
> whenever the script changes.

Read-only: the script queries and prints. It never writes to Google Ads and
never writes to disk — console output is the entire product (see "Reading a
run cold").

## Account resolution

- `--cid` accepts digits or dashed form — dashes are stripped before use.
- A positional account name resolves through **`accounts.md` first** (default
  `./accounts.md`, override with `--accounts`): case-insensitive substring
  match in BOTH directions (`query in name` or `name in query`), against
  every name listed under a CID — the first line under a CID is its display
  name, further lines are aliases.
- **The MCC walk only happens when the registry file is absent.** If
  `accounts.md` exists but contains no match, the script errors out
  (`Error: Could not find customer ID for '…'`, exit 1) — it does not fall
  through to the MCC. Fix the registry entry or pass `--cid`.
- MCC fallback (no registry file): reads `login_customer_id` from
  `google-ads.yaml` and walks `customer_client` for **ENABLED non-manager**
  accounts. Canceled or suspended accounts can't be resolved by name — only
  by `--cid`. No `login_customer_id` either → resolution error, exit 1.
- More than one match → every candidate prints, then
  `Re-run with --cid to disambiguate.`, exit 1. A failed MCC walk prints
  `Warning: MCC traversal failed: …` and falls through to not-found.

## STEP 1 — Campaign Spend Analysis (Last 7 Days)

- Window: GAQL `LAST_7_DAYS` — the seven days **before today**. Today's
  partial data is excluded here (unlike STEP 3).
- No status filter: PAUSED and REMOVED campaigns appear if they have activity
  rows in the window. A campaign with zero activity all window is absent
  entirely — from the blocks AND the totals.
- **Display gate vs totals:** per-campaign blocks print only when 7-day spend
  is above $0, but the `OVERALL 7-DAY SUMMARY` totals include EVERY returned
  campaign — a zero-spend campaign with impressions is invisible above the
  line and still counted in the denominator below it.
- **Shared budgets are double-counted in the totals.** Each campaign row
  carries the full shared-budget amount, so two campaigns sharing one
  $100/day budget put $1,400 into the 7-day budget total, not $700 — and
  each row's own utilization divides by the full shared amount too.
  `Budget Type: SHARED` marks the rows. On shared-budget accounts, recompute
  by hand: Σ spend across the sharing campaigns ÷ the ONE budget.
- Utilization = 7-day spend ÷ (**current** daily budget × 7). The budget is
  read as of run time — a budget changed mid-window distorts utilization in
  the direction of the change (raised yesterday → utilization reads low).
- Campaigns sort by 7-day spend, highest first. `Conversions (CPA: …)` prints
  only when conversions > 0; `Conv Value (ROAS: …)` only when value > 0 — a
  missing line means zero, not missing data. Dollar formatting nuance: budget
  and spend lines use thousands separators; the `Conv Value` line does not
  (`Conv Value: $3240.00`).
- **A STEP 1 query failure aborts the whole run** (`Error querying
  campaigns: …` + traceback, then return — STEPS 2 and 3 never print).
  STEP 2 and STEP 3 failures print the same way but the script continues.
  Partial output → check which step died before trusting what's there.

## STEP 2 — Impression Share Analysis (Last 7 Days)

- Scope: `SEARCH` and `PERFORMANCE_MAX` channels only. Display, Video, and
  Demand Gen campaigns never appear in this section — an empty STEP 2 on a
  Display-only account prints `No Search or Performance Max campaigns found.`
  and means scope, not failure.
- Per-campaign figures are the **unweighted average of daily values** across
  days that returned rows — a 10-impression day counts exactly as much as a
  10,000-impression day. Campaigns print only when window impressions > 0.
- The per-campaign `ROOT CAUSE ANALYSIS` readout is a fixed precedence ladder
  — first match wins:

  | Order | Condition | Readout |
  |---|---|---|
  | 1 | channel = PERFORMANCE_MAX | `[i]` Search IS metrics not meaningful — diagnose via STEP 1 utilization + performance |
  | 2 | Budget Lost IS > 30 | `[!] SEVERE BUDGET CONSTRAINT` |
  | 3 | Budget Lost IS > 10 | `[!] MODERATE BUDGET CONSTRAINT` |
  | 4 | Budget Lost IS < 10 and Rank Lost IS > 50 | `[!] SEVERE BID/QUALITY ISSUES` |
  | 5 | Budget Lost IS < 10 and Rank Lost IS > 30 | `[!] MODERATE BID/QUALITY ISSUES` |
  | 6 | Search IS > 80, Budget Lost IS < 10, Rank Lost IS < 10 | `[OK] LOW DEMAND / HIGH CAPTURE RATE` |
  | 7 | anything else | `[?] MIXED FACTORS` |

  A Budget Lost IS of exactly 10.00 matches neither the budget branches nor
  the quality branches and falls to `[?] MIXED FACTORS`. The ladder is the
  script's per-campaign readout; the account-level diagnosis framework you
  apply across campaigns is `impression-share-diagnostics` — same metric
  vocabulary, richer decision tree.
- `OVERALL IMPRESSION SHARE SUMMARY` averages **Search campaigns only** —
  Pmax is excluded from the averages by design, and the block doesn't print
  at all when no Search campaign had impressions.

## STEP 3 — Month-to-Date Pacing

- Window: GAQL `THIS_MONTH` — **includes today's partial data**. Only
  campaigns with activity rows this month contribute; a campaign dark all
  month is missing from both the spend total and the budget estimate.
- Default monthly budget = Σ (current daily budget × days in month) across
  those campaigns, flagged by `[Monthly budget estimated from current daily
  budgets x days in month]`. The same two distortions as STEP 1 apply:
  shared budgets are double-counted, and a mid-month budget edit rewrites
  the whole month's estimate at the new rate. A campaign paused mid-month
  still contributes its full-month budget.
- `--monthly-budget` replaces the estimate entirely (`[Monthly budget
  supplied via --monthly-budget]`). When a contracted monthly budget exists,
  use it — the estimate is a fallback, not the truth.
- Expected spend = (monthly budget ÷ days in month) × day-of-month — **today
  counts as a fully elapsed day while MTD spend holds only today's partial**.
  Morning runs read artificially underspent; the distortion is worst early
  in the day and early in the month (day 4 at 8am can show ~20 points of
  phantom underspend on an on-pace account).
- Sign convention: **negative variance = underspending**. The script prints
  `Variance: $-958.10 (-18.93%)` then `STATUS: UNDERSPENDING by 18.93%`
  (absolute value). Pacing dashboards often quote underspend as a positive
  magnitude — flip signs consciously when comparing.

## Reading a run cold

Nothing lands on disk. The console output — timestamped in its header — is
the whole record, and the investigation report you write from it is the
durable artifact. If a run wasn't captured, re-run it: the data will have
moved on since, and that's fine, because you want current state anyway.

## Adapting the script (extension hooks)

The shipped script is Google Ads API only — no sheet or database
dependencies. Any replacement must keep the three output sections above for
the skill's diagnostic steps to keep working. Designed adaptation points:

- **Pacing dashboard:** replace the STEP 3 budget estimate with a read
  against your dashboard's contracted budgets — the highest-value swap,
  because contracted budgets and daily-budget math diverge whenever budgets
  change mid-month. Until then, `--monthly-budget` carries that function.
- **Optimization log:** if you keep a budget-change log, print recent
  entries as an extra section — the protocol's Step 1 consumes it directly.
  `change-history-checker` (this repo) answers the same question from the
  API when you don't keep a log.
- **Account registry:** swap `accounts.md` for your own registry (JSON,
  sheet, database) inside `resolve_account_name()`.
