---
name: change-history-checker
description: Query Google Ads account change history for any date range using the `change_status` resource (no 30-day limit, unlike `change_event`). Auto-invoke when user says "what changed in [account]", "change history for [account]", "what did I do in [month]", "audit account changes", or "review optimization history".
allowed-tools: [Bash, Read]
---

# Change History Checker

Check Google Ads account change history for any date range (not limited to 30 days).

## Prerequisites

- **`google-ads.yaml`** at project root — see the [google-ads-api-setup](../google-ads-api-setup/) skill for creating it
- Python with the `google-ads` package (`pip install google-ads pyyaml`)

## When to Use

Auto-invoke when:
- User asks "what changes were made to [account]"
- User asks "what did I do in [month]"
- User wants to see optimization history
- User needs to audit account changes
- Reviewing past work on accounts

## Key Insight: change_status vs change_event

Google Ads has TWO change history resources:

| Resource | Date Limit | Detail Level |
|----------|------------|--------------|
| `change_event` | **30 days only** | Full detail (old/new values, user email) |
| `change_status` | **No limit** | Resource type, status, date only |

**Always use `change_status` for historical queries beyond 30 days.**

## Query Pattern

### Basic Change History Query

```python
query = '''
    SELECT
        change_status.resource_name,
        change_status.resource_type,
        change_status.resource_status,
        change_status.last_change_date_time
    FROM change_status
    WHERE change_status.last_change_date_time >= '2025-11-01'
    AND change_status.last_change_date_time <= '2025-11-30'
    ORDER BY change_status.last_change_date_time DESC
    LIMIT 100
'''
```

### Filter by Resource Type

Common resource types to filter:
- `ASSET`, `CUSTOMER_ASSET`, `AD_GROUP_ASSET`, `CAMPAIGN_ASSET` - Extensions
- `AD_GROUP_CRITERION` - Keywords, audiences
- `CAMPAIGN` - Campaign settings
- `AD_GROUP_AD` - Ad changes
- `CAMPAIGN_BUDGET` - Budget changes

```python
# Extension changes only
query = '''
    SELECT
        change_status.resource_name,
        change_status.resource_type,
        change_status.resource_status,
        change_status.last_change_date_time,
        asset.type,
        asset.sitelink_asset.link_text,
        asset.callout_asset.callout_text,
        asset.structured_snippet_asset.header
    FROM change_status
    WHERE change_status.last_change_date_time >= '2025-11-01'
    AND change_status.last_change_date_time <= '2025-11-30'
    AND change_status.resource_type IN ('ASSET', 'CUSTOMER_ASSET', 'AD_GROUP_ASSET')
    ORDER BY change_status.last_change_date_time DESC
'''
```

### Keyword Changes

```python
query = '''
    SELECT
        change_status.resource_name,
        change_status.resource_status,
        change_status.last_change_date_time,
        ad_group_criterion.keyword.text,
        ad_group_criterion.keyword.match_type
    FROM change_status
    WHERE change_status.last_change_date_time >= '2025-11-01'
    AND change_status.last_change_date_time <= '2025-11-30'
    AND change_status.resource_type = 'AD_GROUP_CRITERION'
    ORDER BY change_status.last_change_date_time DESC
'''
```

## Shipped Script

`scripts/check_change_history.py` ships with this skill (the README install block fetches it) and implements the query patterns above, plus:

- `--types` — filter to specific resource types
- `--detailed` / `-d` — show asset details (sitelink text, callout text, snippet headers) for extension changes
- `--list-accounts` — list all client accounts under your MCC (uses `login_customer_id` from `google-ads.yaml`)
- Run with no arguments to print usage help instead of a traceback

Results are grouped by date and resource type with change counts and statuses.

## Usage Examples

### Command Line
```bash
python scripts/check_change_history.py 1234567890 --start 2025-11-01 --end 2025-11-30

# Filter to extension changes only
python scripts/check_change_history.py 1234567890 --start 2025-11-01 --end 2025-11-30 --types ASSET CUSTOMER_ASSET

# Show asset details (sitelinks, callouts, snippets) for extension changes
python scripts/check_change_history.py 1234567890 --start 2025-11-01 --end 2025-11-30 --detailed
```

### Inline Python
```python
python -c "
from google.ads.googleads.client import GoogleAdsClient

client = GoogleAdsClient.load_from_storage('google-ads.yaml')
ga_service = client.get_service('GoogleAdsService')

query = '''
    SELECT
        change_status.resource_type,
        change_status.last_change_date_time
    FROM change_status
    WHERE change_status.last_change_date_time >= '2025-11-01'
    AND change_status.last_change_date_time <= '2025-11-30'
    ORDER BY change_status.last_change_date_time DESC
'''

response = ga_service.search(customer_id='1234567890', query=query)
for row in response:
    print(f'{row.change_status.last_change_date_time[:10]} | {row.change_status.resource_type.name}')
"
```

## Resource Type Reference

| Resource Type | What It Tracks |
|---------------|----------------|
| CAMPAIGN | Campaign settings, status, bidding |
| CAMPAIGN_BUDGET | Budget changes |
| AD_GROUP | Ad group settings, status |
| AD_GROUP_AD | Ad changes (RSAs, etc.) |
| AD_GROUP_CRITERION | Keywords, negative keywords, audiences |
| ASSET | Extension content (callouts, sitelinks, snippets) |
| CUSTOMER_ASSET | Account-level extension assignments |
| AD_GROUP_ASSET | Ad group-level extension assignments |
| CAMPAIGN_ASSET | Campaign-level extension assignments |
| CAMPAIGN_CRITERION | Campaign-level targeting |
| BIDDING_STRATEGY | Bid strategy changes |

## Status Values

| Status | Meaning |
|--------|---------|
| ADDED | New resource created |
| CHANGED | Existing resource modified |
| REMOVED | Resource deleted |

## Finding Account IDs

If you need to find account IDs first, the shipped script does this for you:

```bash
python scripts/check_change_history.py --list-accounts
```

The underlying query pattern:

```python
# Query MCC for all client accounts
query = '''
    SELECT
        customer_client.id,
        customer_client.descriptive_name
    FROM customer_client
    WHERE customer_client.manager = FALSE
    AND customer_client.status = 'ENABLED'
'''
# Use login_customer_id (MCC ID) to run this query
```

## Common Queries

### "What extensions did I update last month?"
Filter: `resource_type IN ('ASSET', 'CUSTOMER_ASSET', 'AD_GROUP_ASSET')`

### "What keywords did I add/remove?"
Filter: `resource_type = 'AD_GROUP_CRITERION'`

### "What campaign settings changed?"
Filter: `resource_type IN ('CAMPAIGN', 'CAMPAIGN_BUDGET', 'BIDDING_STRATEGY')`

### "What ads did I update?"
Filter: `resource_type = 'AD_GROUP_AD'`
