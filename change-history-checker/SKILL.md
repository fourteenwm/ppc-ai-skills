---
name: change-history-checker
description: Query Google Ads account change history up to 90 days back using the `change_status` resource (vs the 30-day limit of `change_event`). Auto-invoke when user says "what changed in [account]", "change history for [account]", "what did I do in [month]", "audit account changes", or "review optimization history".
allowed-tools: [Bash, Read]
---

# Change History Checker

Owns one workflow: answer "what changed in this account?" from the API —
grouped what-changed-when counts up to 90 days back (the API's hard cap for
`change_status`), with an explicit escalation ladder for the questions the
counts can't answer (who did it, what the old values were, anything older).

The judgment layer — routine vs investigate, the attribution ladder, flag
decisions — is [`rules.md`](rules.md). The two-resource window semantics,
API-enforced query rules, and standalone patterns are
[`references/history-windows.md`](references/history-windows.md).

## Prerequisites

- **`google-ads.yaml`** at project root — see the [google-ads-api-setup](../google-ads-api-setup/) skill for creating it. The script loads it by that literal filename from the directory you run in (no `--config` flag), and `--list-accounts` additionally needs `login_customer_id` set in it.
- Python with the `google-ads` package (`pip install google-ads pyyaml`)

## When to Use

Auto-invoke when:
- User asks "what changes were made to [account]"
- User asks "what did I do in [month]"
- User wants to see optimization history
- User needs to audit account changes
- Reviewing past work on accounts

## Deliberately does NOT do

- **No actor attribution** — the script queries `change_status`, which
  carries no user email. "Who did this?" is the attribution ladder in
  `rules.md` (`change_event` inside 30 days, the web UI beyond).
- **No old/new values** — counts and types only. Value-level forensics is
  `change_event` (≤ 30 days) or the UI export.
- **No history past 90 days** — the API rejects older start dates. The web
  UI's Change History goes back 2 years and exports CSV; route there.
- **No mutations** — read-only, always.
- **Nothing written to disk** — console output is the whole artifact
  (status-leg note below).
- **No scheduling or watchdog mode** — one manual run per invocation.

## Two resources, one script

Google Ads has TWO change-history resources: `change_event` (30 days, full
detail including who) and `change_status` (90 days, counts only). **The
shipped script queries `change_status`** — wider window, thinner payload.
The full table, the API's enforced query rules (finite range + `LIMIT`
required), and copy-ready patterns for both resources live in
[`references/history-windows.md`](references/history-windows.md).

## Shipped Script

`scripts/check_change_history.py` (the README install block fetches it)
groups results by date and resource type with change counts and statuses:

- `--types` — filter to specific resource types (when to narrow: `rules.md`)
- `--detailed` / `-d` — show asset details (sitelink text, callout text,
  snippet headers) for extension changes; scope nuances in `rules.md`
- `--list-accounts` — list ENABLED client accounts under your MCC (uses
  `login_customer_id` from `google-ads.yaml`)
- Run with no arguments (or with a CID but missing `--start`/`--end`) and it
  prints usage help instead of a traceback

## Usage

```bash
# A month, bounded with the day after (date bounds read as midnight — reference)
python scripts/check_change_history.py 1234567890 --start 2026-06-01 --end 2026-07-01

# Extension changes only
python scripts/check_change_history.py 1234567890 --start 2026-06-01 --end 2026-07-01 --types ASSET CUSTOMER_ASSET

# With asset text (sitelinks, callouts, snippets)
python scripts/check_change_history.py 1234567890 --start 2026-06-01 --end 2026-07-01 --detailed

# Find a CID by account name first
python scripts/check_change_history.py --list-accounts
```

The CID is passed through as-is — **10 digits, no dashes** (the script does
not strip them; a dashed CID fails at the API).

## After a Run (status leg)

Nothing lands on disk — the console output IS the run record, so paste the
relevant groups into whatever you're working in before they scroll away.
The durable record is the account's change history itself: a re-run
reproduces any read inside the 90-day window, shifted by whatever changed
since. Findings route onward per the table below; triage every surprise
against the false-alarm table in [`rules.md`](rules.md) first.

## Files in this skill

| File | Role |
|---|---|
| `SKILL.md` | This file — workflow + routing |
| `rules.md` | Judgment: routine-vs-investigate, attribution ladder, flag decisions, false alarms |
| `examples.md` | Three worked reads (routine month, the Saturday cluster, the 90-day wall) |
| `references/history-windows.md` | Window semantics, API-enforced query rules, resource/status tables, standalone patterns |
| `scripts/check_change_history.py` | The change_status query + grouping engine |

Runtime artifacts: none — console only (your `google-ads.yaml` stays outside
the skill).

## When to load sibling skills

| Load | When |
|---|---|
| [`mcc-hack-audit`](../mcc-hack-audit/) | Changes attribute to an actor you can't identify, or access itself is the question — that's the "who has access" map; this skill is the "what changed" log |
| [`google-ads-query`](../google-ads-query/) | The question is performance ("how did it do"), not history ("what changed") |
| [`account-diagnostic`](../account-diagnostic/) | "What changed?" was really "why did it break?" — run the inspection instead of archaeology |
| [`google-ads-api-setup`](../google-ads-api-setup/) | First run, or any credentials error |
