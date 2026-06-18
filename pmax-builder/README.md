# PMax Builder

Generates Performance Max campaign CSV files importable via Google Ads Editor — complete with asset groups, search themes, location targeting, negative country exclusions, and audience signals.

**The pain point:** Building a PMax campaign in Google Ads Editor requires a 115-column CSV with exact formatting (UTF-16LE, tab-delimited), 238 country exclusions, proper search theme rows, and audience signal configuration. Getting one field wrong means a failed import. This skill generates the entire CSV from structured inputs.

---

## What's Inside

- Full PMax campaign CSV generation (115 columns, ~255 rows per campaign)
- Google Ads Editor import format: UTF-16LE with BOM, tab-delimited, CRLF line endings
- Location targeting from existing GEO campaigns or website address geocoding
- 14 search theme templates (8 generic + 6 location-specific)
- 238 negative country exclusions pre-configured
- Ad copy ingestion from Google Sheets API or manual paste
- Remarketing audience signal configuration
- YouTube video ID extraction from URLs
- Standard settings: Maximize Conversion Value bidding, Final URL expansion disabled, asset automation disabled

---

## Installation

```bash
mkdir -p .claude/skills/pmax-builder
curl -o .claude/skills/pmax-builder/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-builder/SKILL.md
```

---

## Prerequisites

- Google Ads API credentials (for querying existing campaign location data and remarketing audiences)
- Google Sheets API credentials (if reading ad copy from sheets)
- Firecrawl API key (if scraping website for address/geocoding)
- Python 3.x

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
