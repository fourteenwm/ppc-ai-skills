# GA4 Cross-Analysis

A cross-platform data collection protocol that structures GA4 conversion data alongside Google Ads campaign settings — landing pages, geo segments, device patterns, and timing. One script ships (Google Ads campaign settings); the other collection queries are documented as a contract you implement against your own infrastructure.

**The pain point:** Investigating lead quality or campaign performance requires pulling data from both GA4 and Google Ads, then manually cross-referencing them. This skill standardizes the collection process into a structured JSON output that agents and analysts can consume directly.

---

## What's Inside

- Shipped script: `scripts/query_campaign_settings.py` — Google Ads campaign configuration (bidding strategy + targets, geographic targeting type, device bid adjustments, network settings, URL expansion) for cross-referencing against GA4 behavior
- A Script Contract for the four environment-specific collection scripts you implement (campaign performance + three GA4 Data API queries), with implementation notes down to the `runReport` dimensions and metrics to request
- Structured JSON output contract with metadata, Google Ads settings, and GA4 behavioral data
- Three output formats: structured JSON (for agents), markdown tables (for review), or summary only (for quick checks)
- Error handling for missing properties, campaigns, or empty date ranges
- Data collection layer for the [ga4-lead-quality-investigation](../ga4-lead-quality-investigation/) skill in this repo

---

## Installation

```bash
mkdir -p .claude/skills/ga4-cross-analysis/scripts
curl -o .claude/skills/ga4-cross-analysis/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ga4-cross-analysis/SKILL.md
curl -o .claude/skills/ga4-cross-analysis/README.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ga4-cross-analysis/README.md
curl -o .claude/skills/ga4-cross-analysis/scripts/query_campaign_settings.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ga4-cross-analysis/scripts/query_campaign_settings.py
```

First run (with `google-ads.yaml` in your working directory):

```bash
python .claude/skills/ga4-cross-analysis/scripts/query_campaign_settings.py 1234567890 "Campaign Name"
```

---

## Script Contract (You Provide)

The shipped script covers the Google Ads campaign-settings side. Four collection scripts are environment-specific — they depend on your GA4 property, event names, and where your credentials and registries live — so the SKILL.md documents the contract each must satisfy and you implement them yourself:

1. `query_campaign_performance.py` — campaign spend, conversions, conversion value, ROAS (the [google-ads-query](../google-ads-query/) skill in this repo ships a template that covers this)
2. `query_ga4_campaign_conversions.py` — GA4 conversion summary for the campaign
3. `query_ga4_user_segments.py` — cities, devices, browsers, hourly distribution
4. `query_ga4_landing_pages.py` — landing pages with conversion counts and intent categorization

Implementation notes (GA4 Data API `runReport` dimensions and metrics, OAuth scope reuse) are in the SKILL.md.

---

## Prerequisites

- Google Ads API credentials (`google-ads.yaml` in the working directory you run the script from) — see [google-ads-api-setup](../google-ads-api-setup/) if you don't have one; querying client accounts through a manager account requires `login_customer_id` in the yaml
- Python with the `google-ads` package (`pip install google-ads`)
- For the GA4-side scripts you implement: the `google-analytics-data` package plus GA4 Data API access (property ID + credentials)

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
