# History Windows — the two change resources, their limits, and query patterns

> **Source of truth:** for script behavior, `scripts/check_change_history.py`
> wins over this document. The window and query-requirement semantics below
> are Google Ads API enforcement, stated from the API's own error definitions
> (`ChangeStatusError` / `ChangeEventError` in the google-ads client library)
> and observed rejections. Mirrors the shipped revision as of 2026-07-23; an
> API version change that moves these limits must update this file and the
> CHANGELOG.

## The two resources

Google Ads exposes change history through two GAQL resources with different
windows and different payloads:

| Resource | Window | What each row carries |
|---|---|---|
| `change_event` | **30 days** | Full detail: old/new values, changed fields, **`user_email` (who)**, `client_type` (what tool) |
| `change_status` | **90 days** | Resource type, status (ADDED/CHANGED/REMOVED), last-change datetime — **no actor, no old/new values** |

The shipped script queries `change_status` only — the wider window, the
thinner payload. The trade: it can tell you *what kind of thing changed and
when* for three months back, but never *who changed it* or *what the values
were*. Attribution questions escalate per the ladder in
[`rules.md`](../rules.md).

**Beyond 90 days the API has nothing.** The Google Ads web UI (Tools → Change
History) goes back **2 years** and exports CSV — that's the escalation path
for older forensics, not a longer API query.

## What the API enforces (both resources)

Queries that break these rules are rejected — the library defines a named
error for each:

- **A finite date range is required** on the datetime field
  (`CHANGE_DATE_RANGE_INFINITE`): both a lower and an upper bound, and not
  reversed (`CHANGE_DATE_RANGE_NEGATIVE`).
- **A `LIMIT` clause is required** (`LIMIT_NOT_SPECIFIED`), and it must be
  **≤ 10,000** (`INVALID_LIMIT_CLAUSE`). A pattern without `LIMIT` doesn't
  run at all.
- **The start date must be inside the window** (`START_DATE_TOO_OLD`).
  `change_status` rejects starts older than 90 days — the live error reads
  "The requested start date is too old. It cannot be older than 90 days." —
  and `change_event` rejects starts older than 30.

Date-only bounds (`'2026-06-30'`) are read as **midnight** of that day. So
`<= '2026-06-30'` keeps almost nothing from June 30 itself — to include a full
last day, bound with the day after (`<= '2026-07-01'`).

## How `change_status` counts — one row per resource, dated by its LAST change

`change_status` is keyed by resource: a keyword edited three times in your
window appears **once**, dated at its most recent change. Two consequences
that read like missing data but aren't:

- Counts are *resources changed*, not *edits made*. A heavy revision session
  on one campaign is one `CAMPAIGN` row.
- **A resource touched again after your window leaves your window.** Work you
  did June 5 disappears from a June query if the same resource was edited
  July 2 — its `last_change_date_time` moved past your end bound. Recent-work
  queries are reliable; archaeology on frequently-touched resources is not.

The script adds its own cap on top: `LIMIT 500`, ordered newest-first — in a
busy window the oldest rows fall off silently (rules false-alarm table).

## Script query shapes

The shipped script builds one of two `change_status` queries (both
`ORDER BY last_change_date_time DESC LIMIT 500`, both with your `--start` /
`--end` as the range):

- **Basic:** `resource_name`, `resource_type`, `resource_status`,
  `last_change_date_time` (+ your `--types` filter if given).
- **Detailed** (`--detailed`, only when the run could include
  `ASSET` / `CUSTOMER_ASSET` / `AD_GROUP_ASSET`): adds the asset join —
  `asset.type`, `asset.name`, sitelink link text, callout text, structured
  snippet header + values. Note `CAMPAIGN_ASSET` is **not** in the script's
  detailed gate: `--types CAMPAIGN_ASSET --detailed` runs the basic query.

## Standalone patterns (inline use, beyond the script)

All patterns carry the required `LIMIT`. Basic window scan:

```sql
SELECT
    change_status.resource_name,
    change_status.resource_type,
    change_status.resource_status,
    change_status.last_change_date_time
FROM change_status
WHERE change_status.last_change_date_time >= '2026-06-01'
  AND change_status.last_change_date_time <= '2026-07-01'
ORDER BY change_status.last_change_date_time DESC
LIMIT 500
```

Narrowed to one surface (swap the type list per the table below):

```sql
AND change_status.resource_type IN ('ASSET', 'CUSTOMER_ASSET', 'AD_GROUP_ASSET')
```

**The "who did this" query — `change_event`, inside 30 days only.** This is
the attribution escalation from `rules.md`: actor email and tool per change,
plus old→new values:

```sql
SELECT
    change_event.change_date_time,
    change_event.change_resource_type,
    change_event.user_email,
    change_event.client_type,
    change_event.changed_fields
FROM change_event
WHERE change_event.change_date_time >= '2026-07-01'
  AND change_event.change_date_time <= '2026-07-23'
ORDER BY change_event.change_date_time DESC
LIMIT 500
```

`client_type` names the tool: `GOOGLE_ADS_WEB_CLIENT` (a human in the UI),
`GOOGLE_ADS_EDITOR`, `GOOGLE_ADS_BULK_UPLOAD`, `GOOGLE_ADS_API`,
`GOOGLE_ADS_SCRIPTS`, `GOOGLE_ADS_AUTOMATED_RULE`,
`GOOGLE_ADS_RECOMMENDATIONS` (auto-applied recommendations), among others —
often enough by itself to separate "our automation" from "a person I don't
recognize."

## Resource types (`change_status.resource_type` values worth filtering)

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

Common filters: extensions → `('ASSET', 'CUSTOMER_ASSET', 'AD_GROUP_ASSET')`;
keywords/audiences → `AD_GROUP_CRITERION`; settings →
`('CAMPAIGN', 'CAMPAIGN_BUDGET', 'BIDDING_STRATEGY')`; ads → `AD_GROUP_AD`.

## Status values (`change_status.resource_status`)

| Status | Meaning |
|--------|---------|
| ADDED | New resource created |
| CHANGED | Existing resource modified |
| REMOVED | Resource deleted |

## What neither resource shows

- **Manager-link acceptances.** When an external MCC's invite is accepted,
  `change_event` records no event for the link itself — you'll see the
  post-link mutations, never the acceptance. The access map is
  [`mcc-hack-audit`](../../mcc-hack-audit/)'s job; "who clicked accept" is UI
  Change History or Google Support territory.
- **Anything older than its window** — 30 days (`change_event`) / 90 days
  (`change_status`) / 2 years (web UI export). Past two years, nothing exists
  to query.
