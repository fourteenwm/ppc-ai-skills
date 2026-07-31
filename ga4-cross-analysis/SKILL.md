---
name: ga4-cross-analysis
description: Collect and structure GA4 + Google Ads data for cross-platform analysis. Reusable data collection engine for lead quality investigations, conversion analysis, and audience insights. Auto-invoke when user asks "what landing pages are converting from [campaign]", "show me GA4 data for [campaign]", "what user segments are converting", or wants to cross-reference GA4 with Google Ads.
allowed-tools: [Bash, Read]
---

# GA4 Cross-Analysis Skill

**Purpose:** Collect and structure GA4 + Google Ads data for cross-platform analysis. Reusable data collection engine for lead quality investigations, conversion analysis, and audience insights.

**Type:** Data collection skill (no autonomous decision-making). Primarily a **protocol** — it defines what to collect from each platform and the structured JSON contract to return it in. One collection script ships with this skill; the rest you implement against the Script Contract below.

---

## When to Use This Skill

Use this skill when you need:
- GA4 conversion data cross-referenced with Google Ads campaigns
- User segment analysis (geo, device, landing pages, timing)
- Campaign settings verification before making recommendations
- Raw data for custom analysis or agent consumption

**Triggers:**
- User asks: "What landing pages are converting from [campaign]?"
- User asks: "Show me GA4 data for [campaign]"
- User asks: "What user segments are converting from [campaign]?"
- Agent needs: GA4 data as input for analysis

**Not sure this is the right skill?** The decision table in [`rules.md`](rules.md) routes
single-metric asks, interpretation asks, and full investigations to their owners.

## Deliberately Does NOT Do

- **No interpretation or recommendations** — the product is the dataset. "What does this
  discrepancy mean" routes to [ga4-campaign-cross-reference](../ga4-campaign-cross-reference/);
  "why are my leads bad" routes to [ga4-lead-quality-investigation](../ga4-lead-quality-investigation/).
- **No GA4-side scripts shipped** — the three GA4 pulls and the performance pull are
  you-implement contracts (environment-specific property IDs, events, registries).
- **No mutations** — every query in this skill is read-only on both platforms.
- **No location names, radius values, or URL exclusion lists from the shipped script** —
  it prints geo IDs, detects-but-doesn't-quantify proximity targets, and can't retrieve
  URL exclusions at all; those fields come from the UI or your own scripts (source map in
  the contract).
- **Not the investigation orchestrator** — ga4-lead-quality-investigation owns the full
  workflow and auto-loads this skill as its collection step.

---

## Prerequisites

- **`google-ads.yaml`** with valid OAuth credentials — see the [google-ads-api-setup](../google-ads-api-setup/) skill for creating it. The shipped script loads the yaml from the working directory you run it from; querying client accounts through a manager account requires `login_customer_id` in the yaml.
- Python with the `google-ads` package (`pip install google-ads`)
- For the GA4-side scripts you implement: the `google-analytics-data` package and GA4 Data API access to your property. Reusing the Ads OAuth client requires a refresh token minted with the GA4 read scope included — scopes are fixed at mint time and can't be added to an existing token; the re-mint steps are in the contract's GA4 implementation notes.

---

## Script Contract

One script ships in this skill's `scripts/` folder; four are yours to implement. Every collection step below names which side of that line it sits on — the only command you can run as-is is the shipped one.

### Shipped: `scripts/query_campaign_settings.py`

Given a customer ID and campaign name, prints the campaign configuration used for cross-referencing against GA4 behavior: status, budget, bidding strategy (with CPA/ROAS targets), geographic targeting, URL expansion setting, device bid adjustments, and network settings.

Usage: `python scripts/query_campaign_settings.py <customer_id> "<campaign_name>"` (run from a directory containing your `google-ads.yaml`).

### You Implement (Contract Provided)

Four scripts are environment-specific and documented as contracts: `query_campaign_performance.py` (spend, conversions, value, ROAS — the [google-ads-query](../google-ads-query/) skill ships a template that covers it), `query_ga4_campaign_conversions.py` (conversion summary), `query_ga4_user_segments.py` (cities, devices, browsers, hours), and `query_ga4_landing_pages.py` (landing pages with intent categorization).

**The full contract layer lives in [`references/collection-contract.md`](references/collection-contract.md):** the shipped script's exact mechanics (matching rules, exit codes, what each section prints and cannot print), the four you-implement contracts with GA4 Data API implementation notes (including the credential re-mint steps), and the field-by-field source map for the Step 4 JSON.

---

## Required Inputs

1. **Customer ID** - Google Ads customer ID (e.g., `[CUSTOMER_ID]`)
2. **Campaign Name** - Exact campaign name (e.g., `"Pmax: Example Campaign"`)
3. **GA4 Property ID** - GA4 property number (e.g., `[GA4_PROPERTY_ID]`)
4. **Conversion Event Name** - GA4 event to analyze (e.g., `"contact_form_submission"`)
5. **Date Range** (optional) - Defaults to last 14 days

**Where to find these:**
- Customer ID: from your account registry (your own CID → account name mapping)
- GA4 Property ID: from your GA4 property registry (your own list of property IDs by account)
- Campaign Name: Query Google Ads or ask user
- Event Name: Query GA4 events or ask user

---

## What This Skill Does

### Step 1: Verify Inputs
- Check the GA4 property ID against your GA4 property registry
- Verify customer ID is valid
- Confirm campaign exists in Google Ads account

### Step 2: Collect Google Ads Data

Campaign settings (geo, bid strategy, device, budget) — the shipped script:

```bash
python scripts/query_campaign_settings.py <customer_id> "<campaign_name>"
```

Campaign performance (spend, conversions, conversion value, ROAS) — your `query_campaign_performance.py` per the Script Contract above.

### Step 3: Collect GA4 Data

All three pulls use the GA4 scripts you implement per the Script Contract above:

- Overall conversion summary for the campaign — `query_ga4_campaign_conversions.py`
- User segments (geo, device, timing) — `query_ga4_user_segments.py`
- Landing pages — `query_ga4_landing_pages.py`

### Step 4: Structure Output

Return data in this format. Which field comes from which source — including the fields
only the UI can fill — is the contract's source map; fields with no legitimate source
stay `null` or absent, never invented (rules.md invariant 2).

```json
{
 "metadata": {
 "customer_id": "[CUSTOMER_ID]",
 "campaign_name": "Pmax: Example Campaign",
 "ga4_property_id": "[GA4_PROPERTY_ID]",
 "event_name": "contact_form_submission",
 "date_range": "last_14_days",
 "analysis_date": "2025-10-24"
 },
 "google_ads": {
 "campaign_performance": {
 "spend": 10256,
 "conversions": 270,
 "conversion_value": 398522,
 "roas": 38.6
 },
 "campaign_settings": {
 "geo_targeting": {
 "type": "PRESENCE",
 "radius_miles": 40,
 "locations": ["New York, NY"]
 },
 "bid_strategy": "MAXIMIZE_CONVERSION_VALUE",
 "budget_daily": 732.56,
 "url_exclusions": ["/community/", "events"]
 }
 },
 "ga4": {
 "conversion_summary": {
 "total_conversions": 84,
 "total_users": 45,
 "conversion_rate": 1.867
 },
 "landing_pages": [
 {
 "url": "/blog/how-to-choose-the-right-service",
 "conversions": 25,
 "users": 10,
 "category": "blog"
 },
 {
 "url": "/nyc-services-for-rent",
 "conversions": 6,
 "users": 3,
 "category": "property"
 }
 ],
 "user_segments": {
 "cities": [
 {"city": "New York", "conversions": 24, "users": 7},
 {"city": "Fresno", "conversions": 4, "users": 1}
 ],
 "devices": [
 {"device": "mobile", "conversions": 82, "users": 43},
 {"device": "desktop", "conversions": 0, "users": 0}
 ],
 "browsers": [
 {"browser": "Android Webview", "conversions": 70, "users": 40},
 {"browser": "Chrome", "conversions": 14, "users": 5}
 ],
 "hours": [
 {"hour": 1, "conversions": 16},
 {"hour": 4, "conversions": 14}
 ]
 }
 }
}
```

---

## How to Invoke This Skill

### From Chat (Direct Invocation):
```
User: "Run GA4 cross-analysis for Example PMAX"
Assistant: <invokes ga4-cross-analysis skill>
Assistant: "Here's the data: [presents structured output]"
```

### From Agent (Programmatic):
```markdown
Use the ga4-cross-analysis skill to collect data for Customer ID [CUSTOMER_ID],
campaign "Pmax: Example Campaign", GA4 property [GA4_PROPERTY_ID], event "contact_form_submission"
```

---

## Output Format Options

1. **Structured JSON** (default) — agents, scripts, programmatic consumption
2. **Markdown tables** — human review ("Show GA4 data for Acme Plumbing as tables")
3. **Summary only** — quick checks ("Quick summary of Acme Plumbing GA4 data")

---

## Error Handling

Protocol-level responses when collection can't proceed:

- **GA4 property not in your registry** → stop and confirm the property ID with the user; don't guess a property.
- **Campaign not found** → verify the exact name (case-sensitive) against a campaign-list pull before retrying. Note the shipped script prints `ERROR: … not found` but still **exits 0** — read the console, not the exit code.
- **No data in the date range** → widen the range or confirm the event name; an empty result is a finding worth reporting, not an error to hide.

Script-exact error shapes and exit codes: [`references/collection-contract.md`](references/collection-contract.md) § Exit codes.

---

## Files in This Skill

| File | Role |
|---|---|
| `SKILL.md` | This file — workflow, JSON output contract, routing |
| `README.md` | Zero-context install + what ships vs what you implement |
| `rules.md` | Collection judgment: tool selection, reading the settings output, false alarms, partial-data honesty |
| `examples.md` | 3 worked reads: full collection, the exit-0 not-found trap, the routed investigation ask |
| `references/collection-contract.md` | Shipped-script mechanics, the four you-implement contracts + GA4 implementation notes, JSON source map |
| `scripts/query_campaign_settings.py` | The one shipped collector — Google Ads campaign settings, console-only |

## After a Run

Nothing lands in this folder: the shipped script writes only to the console, and the
assembled JSON is agent-produced — returned in-chat unless the operator asks for a file.
`metadata.analysis_date` + `metadata.date_range` make a saved dataset self-describing.

## When to Load Other Skills

| Skill | When |
|---|---|
| [ga4-campaign-cross-reference](../ga4-campaign-cross-reference/) | The dataset is assembled and someone asks what a discrepancy means — hypothesis → verification → finding lives there |
| [ga4-lead-quality-investigation](../ga4-lead-quality-investigation/) | The ask is a full lead-quality investigation — it orchestrates and auto-loads this skill as its collection step (this skill's primary consumer) |
| [google-ads-query](../google-ads-query/) | Single-metric Ads pulls, campaign-name lookups, and the shipped template covering the campaign-performance contract |
| [google-ads-api-setup](../google-ads-api-setup/) | No `google-ads.yaml` yet, or the token needs re-minting to add the GA4 read scope |

---

**Created:** October 24, 2025
**Last Updated:** July 31, 2026
**Status:** Active
