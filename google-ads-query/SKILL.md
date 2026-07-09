---
name: google-ads-query
description: |
  Query Google Ads data and save to CSV. AUTO-ACTIVATE for: search terms, campaigns, keywords, ad groups, conversions, budgets, assets, geo performance. Also triggered by account names or "get/pull/show me" + Google Ads resource.
allowed-tools: [Read, Bash, Glob]
---

# Google Ads Query Skill

Query Google Ads API data, save to CSV, and return minimal output (file path + row count only).

## Purpose

This skill implements the **CSV-first pattern** for context-efficient analysis:
1. Query API data
2. Save to CSV file (data stays outside context)
3. Return only file path + row count
4. Use `csv-analyzer` skill for analysis (separate step)

## CRITICAL: Profile Lock Required

**Before ANY query execution, verify profile is locked.**

If no profile locked, respond:
```
Profile lock required. Say "agency_1" or "agency_2" to select profile.
```

## Command Format

```
Get [resource] for [account] [days]d
```

**Examples:**
- `Get search terms for Example Account` → 30 days (default)
- `Get campaigns for Example Account 60d` → 60 days
- `Get keywords for Example Account 90d sort:clicks`

**Defaults:**
- Days: 30
- Sort: cost DESC

## Process

### Step 1: Verify Profile Lock

Check if profile is locked. If not, ask user to lock profile first.

### Step 2: Parse Request

Extract:
1. **Resource** - Short name (see `references/resources.md`)
2. **Account** - Name or alias
3. **Days** - Time period (default 30)

### Step 3: Resolve Account

Read `credentials/[profile]/accounts.json`:
- Match by key, name, or alias (case-insensitive)
- If no match, list similar accounts and ask

### Step 4: Execute Query

```bash
python scripts/query.py \
  --profile [profile] \
  --account [account-key] \
  --resource [resource] \
  --days [days] \
  --output ./data/[profile]/[YYYYMMDD]-[account]-[resource].csv
```

### Step 5: Return Minimal Output

**Only return:**
```
[PROFILE: agency_1]

Query complete.
File: data/google-ads/agency_1/20260109-example-account-search-terms.csv
Rows: 3,847

Say "analyze it" to run insights, or ask another query.
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
data/google-ads/[profile]/[YYYYMMDD]-[account-slug]-[resource].csv
```

Examples:
- `data/google-ads/agency_1/20260109-example-account-search-terms.csv`
- `data/google-ads/agency_1/20260109-example-campaigns.csv`
- `data/google-ads/agency_2/20260109-example-keywords.csv`

## Error Handling

**Account not found:**
```
Account "example-search" not found.

Similar matches:
- example-account (Example Account) - Portfolio 1

Did you mean example-account?
```

**Query fails:**
- Show error message
- Suggest common fixes (invalid date range, permissions)

## Integration

After query completes, user can:
1. Say "analyze it" → triggers `csv-analyzer` skill
2. Ask for different resource/account
3. Re-query with different date range

## Files

```
.claude/skills/google-ads-query/
├── SKILL.md                    ← This file
├── scripts/
│   └── query.py                ← Unified query→CSV script
└── references/
    ├── resources.md            ← Resource mappings
    └── *.gaql                  ← 8 query templates
```
