---
name: google-ads-query
description: |
  Query Google Ads data and save to CSV. AUTO-ACTIVATE for: search terms, campaigns, keywords, ad groups, conversions, budgets, assets, geo performance. Also triggered by account names or "get/pull/show me" + Google Ads resource.
allowed-tools: [Read, Bash, Glob]
---

# Google Ads Query Skill

Query Google Ads API data, save to CSV, and return minimal output (file path + row count only). Read-only — SELECT queries, never mutations.

## Purpose

This skill implements the **CSV-first pattern** for context-efficient analysis:
1. Query API data
2. Save to CSV file (data stays outside context)
3. Return only file path + row count
4. Analyze the CSV as a separate step, only when asked (read the file then, not before)

## Command Format

```
Get [resource] for [account] [days]d
```

**Examples:**
- `Get search terms for Riverside Flats` → 30 days (default)
- `Get campaigns for Riverside Flats 60d` → 60 days
- `Get keywords for 1234567890 90d` → bare CID works too

**Defaults:**
- Days: 30
- Sort: cost DESC (built into each template)

## Prerequisites

- **`google-ads.yaml`** at project root (or `--config <path>`) — see the [google-ads-api-setup](../google-ads-api-setup/) skill for creating it. Querying client accounts through a manager account requires `login_customer_id` in the yaml.
- Python with the `google-ads` package (`pip install google-ads`)
- Optional: an `accounts.json` registry so requests can use account names instead of CIDs — copy `accounts.example.json` and edit. Without it, bare CIDs work fine.

## Process

### Step 1: Parse Request

Extract:
1. **Resource** — short name (see `references/resources.md`)
2. **Account** — a CID, or a name/alias if a registry exists
3. **Days** — time period (default 30)

### Step 2: Resolve Account

- Request contains a CID → use `--cid` directly; no registry needed.
- Request names an account → resolve via `accounts.json` (`--account` matches key, name, or alias, case-insensitively; partial matches suggest candidates).
- Name given but no `accounts.json` present → ask for the CID, or offer to set up the registry from `accounts.example.json`.

### Step 3: Execute Query

```bash
# By CID
python scripts/query.py --cid 1234567890 --resource search-terms --days 30

# By registry name/alias
python scripts/query.py --account "riverside flats" --resource campaigns --days 60
```

Useful flags: `--config <path>` (default `./google-ads.yaml`), `--accounts <path>` (default `./accounts.json`), `--output <path>` (default `data/[YYYYMMDD]-[account]-[resource].csv`).

### Step 4: Return Minimal Output

**Only return:**
```
Query complete.
File: data/20260109-riverside-flats-search-terms.csv
Rows: 3,847

Ask for analysis to dig in, or run another query.
```

**DO NOT:**
- Display raw data in conversation
- Show sample rows
- Auto-analyze (wait for user to request)

## Resources

See `references/resources.md` for resource mappings.

| Short Name | Description | GAQL Template |
|------------|-------------|---------------|
| `search-terms` | Search query report | `search-terms.gaql` |
| `campaigns` | Campaign performance | `campaigns.gaql` |
| `keywords` | Keyword performance | `keywords.gaql` |
| `ad-groups` | Ad group performance | `ad-groups.gaql` |
| `conversions` | Conversion tracking | `conversions.gaql` |
| `budgets` | Budget utilization | `budgets.gaql` |
| `assets` | Asset performance (PMAX) | `assets.gaql` |
| `geo` | Geographic performance | `geo.gaql` |

## File Naming Convention

```
data/[YYYYMMDD]-[account-slug]-[resource].csv
```

The slug is the registry key for `--account` runs, or the CID for `--cid` runs:
- `data/20260109-riverside-flats-search-terms.csv`
- `data/20260109-1234567890-campaigns.csv`

## Error Handling

**Account not found (registry present):**
```
Account "riverside" is ambiguous. Did you mean:
  - riverside-flats (Riverside Flats)
```
Relay the script's suggestions and let the user pick.

**Registry missing but a name was used:**
The script explains both fixes (copy `accounts.example.json`, or pass `--cid`). Offer the CID route first — it needs no setup.

**Query fails:**
- Show the API error message
- Common fixes: wrong CID, missing `login_customer_id` for manager-account access, longer `--days` window when a report is empty

## Integration

After a query completes, the user can:
1. Ask for analysis → read the CSV and dig in (separate step, keeps raw data out of context until needed)
2. Ask for a different resource/account
3. Re-query with a different date range

To go beyond the 8 shipped templates, see the [gaql-query-patterns](../gaql-query-patterns/) skill — GAQL templates for custom queries; drop a new `.gaql` file in `references/` (with a `{DATE_RANGE}` placeholder) and it's immediately queryable by filename.

## Files

```
google-ads-query/
├── SKILL.md                    ← This file
├── accounts.example.json       ← Registry template (copy to accounts.json)
├── scripts/
│   └── query.py                ← Unified query→CSV script
└── references/
    ├── resources.md            ← Resource mappings
    └── *.gaql                  ← 8 query templates
```
