---
name: conversion-tracking-health
description: "Audits conversion tracking health across Google Ads portfolios. Auto-invoke when user says 'conversion tracking audit', 'check conversion health', or 'audit conversions for [portfolio]'. Only analyzes accounts with spend in last 7 days. Identifies conversion actions that haven't fired or are stale."
allowed-tools: [Bash, Read]
---

# Conversion Tracking Health Audit

**Purpose:** Find conversion actions that have gone quiet before someone
asks "why did conversions drop?" — a portfolio-wide scan of which primary
website conversion actions haven't fired recently, spend-gated so you only
audit accounts that are actively running.

**Type:** Read-only audit. Two shipped scripts: a portfolio scan and a
single-account deep-dive. Console-only — neither writes a file.

This skill deliberately does NOT:

- **Fix anything** — no tag edits, no action pauses, no re-promotion. It
  finds the quiet actions; the fix runs through your own change process.
- **Detect missing tracking setup** — an account with no conversion actions
  configured passes silently. Absent-setup detection is
  [`account-diagnostic`](../account-diagnostic/)'s job (contract, "the
  zero-actions blind spot").
- **Audit store-visit, app, or Google-hosted call conversions** — ten
  non-website action types are filtered out by design (contract).
- **Judge WHY an action is quiet** — the output is a table of hypotheses;
  [`rules.md`](rules.md) owns the triage that separates broken tags from
  seasonality, low volume, and deliberate config.
- **Track observation-only actions in the portfolio scan** — that's the
  deep-dive's job (contract, cross-script asymmetry).

## Prerequisites

- **`google-ads.yaml`** at project root — see
  [`google-ads-api-setup`](../google-ads-api-setup/). The portfolio scan
  accepts `--config <path>`; **the deep-dive reads `./google-ads.yaml`
  only** — run it from the project root.
- Python with the `google-ads` package (`pip install google-ads`)

## Workflow

### Step 1: Choose accounts

- Single account: `--cid 1234567890`
- Several: `--cids 1234567890,2345678901`
- A book: `--accounts-file portfolio.csv` (`cid,name` per row, no header)

The three flags combine; duplicates run twice (contract, account list).

### Step 2: Run the portfolio scan

```bash
python scripts/portfolio_conversion_audit.py --accounts-file portfolio.csv
```

Useful variants: `--days 180` (wider lookback — the no-data bucket is
window-relative), `--include-no-spend` (audit idle accounts too),
`--config <path>`. Runtime ~1-2 seconds per account (three sequential API
queries each).

### Step 3: Read the output

Accounts print as `[ok]` / `[skipped] … (no spend in last 7 days)`,
followed by three severity sections, worst first:

```
NO RECENT CONVERSIONS (90+ days) - 2 issues
STALE (30+ days) - 1 issues
WARNING (15-30 days) - 1 issues
```

Healthy actions (fired within 14 days) are suppressed; a clean run prints
`NO ISSUES FOUND - All conversion actions are healthy.` Exact bucket
definitions, console shapes, the meaning of `Never fired`
(window-relative!), and the three error paths that can make `[ok]` or
`[skipped]` lie are in
[`references/audit-contract.md`](references/audit-contract.md) — **scan for
error lines before trusting any verdict** (contract, error isolation).

### Step 4: Triage per rules.md

Work [`rules.md`](rules.md) top to bottom: error lines → no-data on
spending accounts → stale main actions → warnings against cadence. The
"when stale is expected" table keeps seasonal businesses, low-volume
actions, and migration leftovers from becoming tickets; the escalation
ladder (widen the window → observation view → change history → live tag
test) runs BEFORE any "tracking is broken" verdict.

### Deep-dive (single account, all actions)

```bash
python scripts/last_conversion_dates_by_action.py --cid 1234567890 --days 180
```

Shows ALL actions including healthy ones, with `(in)`/`(obs)` markers —
observation-only actions appear here and nowhere else. Pass `--cid`; name
lookup only sees directly-accessible accounts, not your MCC's clients
(contract, deep-dive resolution).

## Pairing with scheduled monitoring

If you run a scheduled Google Ads Script or dashboard that tracks
zero-conversion accounts continuously, keep both: the scheduled layer for
always-on breadth, this skill for on-demand depth (per-action dates,
severity buckets, spend-gating, and the deep-dive's observation view). They
answer at different granularities — accounts vs. individual actions.

## Files in This Skill

| File | Role |
|---|---|
| `SKILL.md` | This workflow — run, read, triage, route |
| `rules.md` | Judgment layer: triage order, when-stale-is-expected, escalation ladder, false-alarm table, cadence |
| `examples.md` | Three worked reads — the routine portfolio pass, the error masquerade, the "Never fired" that fired for years |
| `references/audit-contract.md` | Exact per-script mechanics: buckets, windows, console shapes, error isolation, the cross-script asymmetry table (source of truth: the scripts) |
| `scripts/portfolio_conversion_audit.py` | Portfolio scan — primary actions, spend-gated, problems only |
| `scripts/last_conversion_dates_by_action.py` | Single-account deep-dive — all actions incl. observation, healthy shown |
| `README.md` | Zero-context install and orientation |

Runtime artifacts: **none** — both scripts are console-only.

## After a Run

Nothing lands on disk: copy findings out of the console before they
scroll (the analysis-date line in the header timestamps the run). Re-runs
are always safe. If a row was fixed, the confirmation is the row clearing
on the NEXT scan a few days later — schedule that follow-up when you ship
the fix.

## When to Load Something Else

| Trigger | Load |
|---|---|
| A quiet action needs a "who changed what" answer | [`change-history-checker`](../change-history-checker/) — inside 30 days it names the actor on conversion-setting changes |
| An account never shows findings and you suspect no tracking exists | [`account-diagnostic`](../account-diagnostic/) — setup checks, not just activity checks |
| Findings need prioritizing across a big book | [`portfolio-health-prioritization`](../portfolio-health-prioritization/) — which account gets attention first |
| Findings go to a client | [`client-communication-standards`](../client-communication-standards/) — report framing |
| No working `google-ads.yaml` yet | [`google-ads-api-setup`](../google-ads-api-setup/) — one-time credential setup |
