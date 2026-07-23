---
name: google-ads-query
description: |
  Query Google Ads data and save to CSV. AUTO-ACTIVATE for: search terms, campaigns, keywords, ad groups, conversions, budgets, assets, geo performance. Also triggered by account names or "get/pull/show me" + Google Ads resource.
allowed-tools: [Read, Bash, Glob]
---

# Google Ads Query Skill

Owns one workflow: turn a natural-language data request into a template-driven
GAQL pull whose results land in a CSV file — returning only the file path and
row count to the conversation. Read-only — SELECT queries, never mutations.

## Purpose

This skill implements the **CSV-first pattern** for context-efficient analysis:
1. Query API data
2. Save to CSV file (data stays outside context)
3. Return only file path + row count
4. Analyze the CSV as a separate step, only when asked (read the file then, not before)

The judgment layer — template vs custom GAQL, registry vs bare CID, when the
CSV actually gets read — is [`rules.md`](rules.md). The exact resolution,
date, and CSV mechanics are
[`references/query-contract.md`](references/query-contract.md).

## Deliberately does NOT do

- **No mutations, ever** — there is no code path that writes to Google Ads.
- **No auto-analysis** — a completed query reports path + row count and stops;
  reading the file waits for an analysis question.
- **No raw data in conversation** — no sample rows, no previews, no pastes.
- **No portfolio sweeps by default** — one account per run; a multi-account
  pull is an explicit loop, not an assumption.
- **No alias/fuzzy matching inside the script** — name resolution vocabulary
  is the agent's parsing job (see `references/resources.md`); the script takes
  exact resource names and exact/partial registry matches only.

## Command Format

```
Get [resource] for [account] [days]d
```

**Examples:**
- `Get search terms for Riverside Flats` → 30 days (default)
- `Get campaigns for Riverside Flats 60d` → 60 days
- `Get keywords for 1234567890 90d` → bare CID works too

**Defaults:** 30 days; sort built into each template (cost DESC on seven,
conversions DESC on `conversions`). Note the contract's date semantics:
`--days 30` spans 31 calendar dates including today's partial data, and
`conversions` ignores `--days` entirely (all-time template).

## Prerequisites

- **`google-ads.yaml`** at project root (or `--config <path>`) — see the [google-ads-api-setup](../google-ads-api-setup/) skill for creating it. Querying client accounts through a manager account requires `login_customer_id` in the yaml.
- Python with the `google-ads` package (`pip install google-ads`)
- Optional: an `accounts.json` registry so requests can use account names instead of CIDs — copy `accounts.example.json` and edit. Without it, bare CIDs work fine. The registry-or-CID call is in `rules.md`.

## Process

### Step 1: Parse Request

Extract:
1. **Resource** — short name. Eight ship: `search-terms`, `campaigns`,
   `keywords`, `ad-groups`, `conversions`, `budgets`, `assets`, `geo` —
   mappings, aliases, and the template format live in
   [`references/resources.md`](references/resources.md). Map user phrasing
   ("sqr", "kw") to the exact short name here — the script won't.
2. **Account** — a CID, or a name/alias if a registry exists
3. **Days** — time period (default 30)

If the ask doesn't map cleanly to one of the eight (different segment, grain,
or filter), stop and make the template-vs-custom call per `rules.md` before
running anything.

### Step 2: Resolve Account

- Request contains a CID → use `--cid` directly; no registry needed.
- Request names an account → resolve via `accounts.json` (`--account` matches
  key, name, or alias; partial matches suggest candidates — full ladder in the
  contract).
- Name given but no `accounts.json` present → ask for the CID, or offer to set
  up the registry from `accounts.example.json`. CID route first — it needs no
  setup.

### Step 3: Execute Query

```bash
# By CID
python scripts/query.py --cid 1234567890 --resource search-terms --days 30

# By registry name/alias
python scripts/query.py --account "riverside flats" --resource campaigns --days 60
```

Useful flags: `--config <path>` (default `./google-ads.yaml`), `--accounts <path>` (default `./accounts.json`), `--output <path>` (default `data/[YYYYMMDD]-[account]-[resource].csv`).

### Step 4: Return Minimal Output

The script prints exactly two lines on success:

```
File: data/20260723-riverside-flats-search-terms.csv
Rows: 4127
```

Relay them (row count prints plain — no thousands separator) and close with
the standing offer: *"Ask for analysis to dig in, or run another query."*

**DO NOT:**
- Display raw data in conversation
- Show sample rows
- Auto-analyze (wait for user to request)

## Error Handling

Every failure prints `ERROR: <detail>` to stderr and exits 1 — resolution
errors carry their own suggestions (ambiguous-name candidates, the first
registry keys, the both-fixes message when a name is used with no registry).
Relay the script's suggestions and let the user pick; never auto-pick. A
zero-row run is **not** an error: `Rows: 0 (no file written - …)`, exit 0.
Before re-running any surprise, check the false-alarm table in
[`rules.md`](rules.md) — most surprises are per-template scope filters doing
their documented job (contract table).

## After a Query (status leg)

- `data/` is the run record: `<YYYYMMDD>-<slug>-<resource>.csv` names tell a
  cold session what was pulled and when. Same-day same-target re-pulls
  overwrite; zero-row runs leave no file (contract, "Reading run state cold").
- Findings that turn into work route onward — table below.

## Files in this skill

| File | Role |
|---|---|
| `SKILL.md` | This file — workflow + routing |
| `rules.md` | Judgment: template-vs-custom, registry-vs-CID, CSV reading, false alarms |
| `examples.md` | Three worked reads (routine pull, the PMax-scope zero, the ninth template) |
| `references/query-contract.md` | Exact resolution/date/CSV mechanics + per-template scope table |
| `references/resources.md` | Resource → template mappings + parse-time aliases |
| `references/*.gaql` | The 8 query templates — each file is the source of truth for its fields |
| `accounts.example.json` | Registry starter — copy to `accounts.json` and edit |
| `scripts/query.py` | The query → CSV engine |

Runtime artifacts (never committed): `data/*.csv` outputs, your
`accounts.json`, your `google-ads.yaml`.

## When to load sibling skills

| Load | When |
|---|---|
| [`gaql-query-patterns`](../gaql-query-patterns/) | The ask doesn't map to the 8 templates — write custom GAQL there; promote repeat queries to a ninth template per the contract |
| [`google-ads-api-setup`](../google-ads-api-setup/) | First run, or any credentials error |
| [`sqr-pipeline`](../sqr-pipeline/) | The search-terms pull is step one of negatives work — classification and upload live there, not here |
| [`change-history-checker`](../change-history-checker/) | The question is "what changed," not "how did it perform" |
| [`account-diagnostic`](../account-diagnostic/) | The question is really "how healthy is this account" — run the inspection, not ad-hoc pulls |
| [`markdown-to-sheets-presenter`](../markdown-to-sheets-presenter/) | CSV findings need to become a client-facing formatted Sheet |
