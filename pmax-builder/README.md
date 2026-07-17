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

> **Vertical note:** the shipped search-theme and audience-signal templates are
> **multifamily/apartment defaults** (apartment search themes, Renters / Moving
> Soon audiences). Edit `templates/search_themes.json` and
> `templates/audience_signals.json` for your vertical before your first build —
> see the Vertical Note in SKILL.md.

---

## Installation

```bash
mkdir -p .claude/skills/pmax-builder/scripts .claude/skills/pmax-builder/templates
curl -o .claude/skills/pmax-builder/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-builder/SKILL.md
curl -o .claude/skills/pmax-builder/scripts/build_pmax_csv.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-builder/scripts/build_pmax_csv.py
curl -o .claude/skills/pmax-builder/scripts/scrape_website_firecrawl.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-builder/scripts/scrape_website_firecrawl.py
curl -o .claude/skills/pmax-builder/templates/campaign_settings.json \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-builder/templates/campaign_settings.json
curl -o .claude/skills/pmax-builder/templates/search_themes.json \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-builder/templates/search_themes.json
curl -o .claude/skills/pmax-builder/templates/audience_signals.json \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-builder/templates/audience_signals.json
curl -o .claude/skills/pmax-builder/templates/negative_locations.json \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-builder/templates/negative_locations.json
```

---

## Prerequisites

- Google Ads API credentials (`google-ads.yaml` at project root) — see [google-ads-api-setup](../google-ads-api-setup/) if you don't have one; used for querying existing campaign location data and remarketing audiences
- The Sheets ad-copy mode reuses that same `google-ads.yaml` OAuth token — its refresh token needs the `spreadsheets` + `drive.readonly` scopes, which the setup skill's generator grants by default (token predates that? re-run the generator once)
- Firecrawl API key (if scraping website for address/geocoding)
- Python 3.x (`gspread`, `google-auth`, `pyyaml` for the Sheets mode)

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
