---
name: ga4-cross-analysis
description: Collect and structure GA4 + Google Ads data for cross-platform analysis. Reusable data collection engine for lead quality investigations, conversion analysis, and audience insights. Auto-invoke when user asks "what landing pages are converting from [campaign]", "show me GA4 data for [campaign]", "what user segments are converting", or wants to cross-reference GA4 with Google Ads.
allowed-tools: [Bash, Read]
---

# GA4 Cross-Analysis Skill

**Purpose:** Collect and structure GA4 + Google Ads data for cross-platform analysis. Reusable data collection engine for lead quality investigations, conversion analysis, and audience insights.

**Type:** Data collection skill (no autonomous decision-making)

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

## Required Inputs

1. **Customer ID** - Google Ads customer ID (e.g., `[CUSTOMER_ID]`)
2. **Campaign Name** - Exact campaign name (e.g., `"Pmax: Example Campaign"`)
3. **GA4 Property ID** - GA4 property number (e.g., `[GA4_PROPERTY_ID]`)
4. **Conversion Event Name** - GA4 event to analyze (e.g., `"contact_form_submission"`)
5. **Date Range** (optional) - Defaults to last 14 days

**Where to find these:**
- Customer ID: from your accounts mapping (provide your own `accounts.md`)
- GA4 Property ID: from your GA4 properties reference (provide your own list)
- Campaign Name: Query Google Ads or ask user
- Event Name: Query GA4 events or ask user

---

## What This Skill Does

### Step 1: Verify Inputs
- Check that GA4 property exists in `ga4_properties.md`
- Verify customer ID is valid
- Confirm campaign exists in Google Ads account

### Step 2: Collect Google Ads Data
Run these queries:
```bash
# Campaign performance
python query_campaign_performance.py <customer_id> "<campaign_name>"

# Campaign settings (geo, bid strategy, device, budget)
python query_campaign_settings.py <customer_id> "<campaign_name>"
```

### Step 3: Collect GA4 Data
Run these queries:
```bash
# Overall conversion events for the campaign
python query_ga4_campaign_conversions.py <ga4_property_id> "<campaign_name>" "<event_name>"

# User segments (geo, device, timing)
python query_ga4_user_segments.py <ga4_property_id> "<campaign_name>" "<event_name>"

# Landing pages
python query_ga4_landing_pages.py <ga4_property_id> "<campaign_name>" "<event_name>"
```

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

### From Python Script:
```python
# Future: Skills will be importable
from skills import ga4_cross_analysis

data = ga4_cross_analysis.run(
 customer_id="[CUSTOMER_ID]",
 campaign_name="Pmax: Example Campaign",
 ga4_property_id="[GA4_PROPERTY_ID]",
 event_name="contact_form_submission"
)
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

## Scripts Used by This Skill

**Location:** `scripts/`

**Included:**
- `query_campaign_settings.py` - Fetch Google Ads campaign configuration (bidding strategy, targeting, networks, etc.) for cross-referencing against GA4 behavior.

**Not included (protocol only):**

This skill is primarily a **protocol** for how to combine Google Ads campaign
settings with GA4 behavioral data. The GA4-side queries (landing pages, user
segments, conversion breakdowns) depend on which GA4 property ID, event names,
and dimensions your account uses, so they're documented as query patterns rather
than shipped as generic scripts.

To implement the GA4-side queries yourself:

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

## Error Handling

### If GA4 Property Not Found:
```
Error: GA4 property [GA4_PROPERTY_ID] not found in ga4_properties.md
Suggestion: Check property ID or add to ga4_properties.md
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

## Integration with Agents

Agents that use this skill:
- `ga4-lead-quality-investigation-agent` - Lead quality analysis
- (Future) `conversion-funnel-analysis-agent` - Funnel analysis
- (Future) `audience-insights-agent` - Audience optimization

**How agents use it:**
1. Agent identifies need for GA4 + Google Ads data
2. Agent invokes skill with required parameters
3. Agent receives structured JSON
4. Agent analyzes data and generates recommendations

---

## Maintenance Notes

### When to Update This Skill:
- New GA4 dimensions become available
- New campaign settings need verification
- Additional data sources added (e.g., Google Search Console)

### Future Enhancements:
- Add Google Search Console data integration
- Add historical comparison (period-over-period)
- Add anomaly detection (statistical outliers)
- Cache results for performance (15-minute TTL)

---

## Related Documentation

- Your own GA4 properties reference (a list of GA4 Property IDs by account)
- Your own accounts mapping (CID → account name)
- Your own scripts/ folder for query implementations
- Your own examples folder for sample analyses

---

**Created:** October 24, 2025
**Last Updated:** October 24, 2025
**Status:** Active
