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

---

## Prerequisites

- **`google-ads.yaml`** with valid OAuth credentials — see the [google-ads-api-setup](../google-ads-api-setup/) skill for creating it. The shipped script loads the yaml from the working directory you run it from; querying client accounts through a manager account requires `login_customer_id` in the yaml.
- Python with the `google-ads` package (`pip install google-ads`)
- For the GA4-side scripts you implement: the `google-analytics-data` package and GA4 Data API access to your property

---

## Script Contract

One script ships in this skill's `scripts/` folder; four are yours to implement. Every collection step below names which side of that line it sits on — the only command you can run as-is is the shipped one.

### Shipped: `scripts/query_campaign_settings.py`

Given a customer ID and campaign name, prints the campaign configuration used for cross-referencing against GA4 behavior: status, budget, bidding strategy (with CPA/ROAS targets), geographic targeting (locations, radius, presence vs interest), URL expansion setting, device bid adjustments, and network settings.

Usage: `python scripts/query_campaign_settings.py <customer_id> "<campaign_name>"` (run from a directory containing your `google-ads.yaml`).

### You Implement (Contract Provided)

These four are environment-specific — they depend on which GA4 property ID, event names, and dimensions your account uses, and on where your credentials and registries live — so they're documented as contracts rather than shipped as generic scripts:

1. **`query_campaign_performance.py`** — given a customer ID and campaign name, return campaign spend, conversions, conversion value, and ROAS for the date range. (The [google-ads-query](../google-ads-query/) skill in this repo ships a campaign-performance GAQL template that satisfies this contract.)
2. **`query_ga4_campaign_conversions.py`** — given a GA4 property ID, campaign name, and event name, return the conversion summary: total conversions, total users, conversion rate.
3. **`query_ga4_user_segments.py`** — given the same inputs, return user segments: cities, devices, browsers, hourly distribution.
4. **`query_ga4_landing_pages.py`** — given the same inputs, return landing pages with conversion counts, users, and a high-intent vs low-intent categorization.

**GA4-side implementation notes:**

1. Install `google-analytics-data` (`pip install google-analytics-data`)
2. Reuse the same OAuth credentials as the Google Ads API (just add the
   `https://www.googleapis.com/auth/analytics.readonly` scope to your refresh
   token).
3. Query the GA4 Data API (`runReport`) for:
   - `landing_pages`: dimensions `[sessionDefaultChannelGrouping, landingPage]`,
     metrics `[conversions, sessions, totalUsers]`, filter on the Google Ads
     campaign as source/medium or session campaign ID.
   - `user_segments`: dimensions like `[city, deviceCategory, browser, hour]`,
     metrics `[conversions, totalUsers]`, filter on your event of interest.
   - `conversion_summary`: metrics `[conversions, totalUsers, sessions]` filtered
     to the specific event name (e.g. `contact_form_submission`).

See GA4 Data API reference: https://developers.google.com/analytics/devguides/reporting/data/v1

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
Return data in this format:

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

### 1. Structured JSON (default)
Best for: Agents, scripts, programmatic consumption

### 2. Markdown Tables
Best for: Human readability, quick review
```
User: "Show GA4 data for Acme Plumbing as tables"
```

### 3. Summary Only
Best for: Quick checks
```
User: "Quick summary of Acme Plumbing GA4 data"
```

---

## Example Usage Scenarios

### Scenario 1: Quick Data Lookup
```
User: "What landing pages are converting from Best HVAC PMAX?"
Assistant: <invokes skill, returns landing_pages section only>
```

### Scenario 2: Campaign Settings Verification
```
User: "Check if City Dental PMAX has correct geo targeting"
Assistant: <invokes skill, returns campaign_settings.geo_targeting>
```

### Scenario 3: Full Data Collection (for Agent)
```
Agent needs full dataset for analysis
<invokes skill with all parameters>
<receives complete JSON structure>
```

---

## Error Handling

### If GA4 Property Not Found:
```
Error: GA4 property [GA4_PROPERTY_ID] not found in your property registry
Suggestion: Check the property ID or add it to your registry
```

### If Campaign Not Found:
```
Error: Campaign "Pmax: Example Campaign" not found in account [CUSTOMER_ID]
Suggestion: Check campaign name spelling (case-sensitive)
```

### If No Data in Date Range:
```
Warning: No conversions found for event "contact_form_submission" in last 14 days
Suggestion: Try longer date range or check event name
```

---

## Used By

- [ga4-lead-quality-investigation](../ga4-lead-quality-investigation/) — the lead quality investigation skill in this repo auto-invokes this skill as its data collection step.

**How a consuming skill or agent uses it:**
1. Identifies the need for GA4 + Google Ads data
2. Invokes this skill with the required inputs
3. Receives structured JSON per the Step 4 contract
4. Analyzes the data and generates recommendations

---

## Related Documentation

- [google-ads-api-setup](../google-ads-api-setup/) — create the `google-ads.yaml` credentials file
- [google-ads-query](../google-ads-query/) — general-purpose GAQL pulls (covers the campaign-performance contract)
- GA4 Data API reference: https://developers.google.com/analytics/devguides/reporting/data/v1

---

**Created:** October 24, 2025
**Last Updated:** July 21, 2026
**Status:** Active
