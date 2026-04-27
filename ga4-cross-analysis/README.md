# GA4 Cross-Analysis

A data collection engine that pulls and structures GA4 conversion data alongside Google Ads campaign settings for cross-platform analysis — landing pages, geo segments, device patterns, and timing.

**The pain point:** Investigating lead quality or campaign performance requires pulling data from both GA4 and Google Ads, then manually cross-referencing them. This skill standardizes the collection process into a structured JSON output that agents and analysts can consume directly.

---

## What's Inside

- Collects Google Ads campaign performance and settings (geo targeting, bid strategy, budget, URL exclusions)
- Collects GA4 conversion data (landing pages, city/device/browser segments, hourly patterns)
- Outputs structured JSON with metadata, Google Ads settings, and GA4 behavioral data
- Three output formats: structured JSON (for agents), markdown tables (for review), or summary only (for quick checks)
- Error handling for missing properties, campaigns, or empty date ranges
- Integration point for lead quality investigation agents

---

## Installation

```bash
mkdir -p .claude/skills/ga4-cross-analysis
curl -o .claude/skills/ga4-cross-analysis/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ga4-cross-analysis/SKILL.md
```

---

## Prerequisites

- Google Ads API credentials (YAML config)
- GA4 API access (GA4 property ID and credentials)
- Python with `google-ads` and `google-analytics-data` packages

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
