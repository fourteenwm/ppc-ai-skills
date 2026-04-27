---
name: rsa-refresh
description: Refresh RSA ad copy by scraping the business website, identifying LOW-performing assets, and generating replacement headlines and descriptions using AI. Uses Firecrawl for scraping and Claude for copy generation.
---

# RSA Refresh Skill

Refreshes Responsive Search Ad copy by replacing LOW-performing assets with new AI-generated headlines and descriptions verified against the actual business website.

## Workflow

### Stage 1: Prepare Context
```bash
python scripts/rsa_refresh_generator.py \
  --cid YOUR_CID \
  --sheet-id YOUR_SHEET_ID \
  --prepare-for-claude
```

This will:
1. Query existing RSAs and asset performance labels (BEST/GOOD/LOW/LEARNING)
2. Scrape the business website using Firecrawl
3. Extract property/business features from the site
4. Output `rsa_context_{cid}.json` with all data Claude needs

### Stage 2: Generate Copy (Claude Code)
Read `rsa_context_{cid}.json` and generate replacement headlines + descriptions following the reference docs:
- `references/pm-headline-structure.md` -- 15 headline rules (1 customizer + 14 AI-generated)
- `references/description-voice-lifting.md` -- 3 descriptions with voice lifting technique
- `references/hallucination-filter.md` -- Defense-in-depth filter for unverified claims

Save output as `copy_{cid}.json` with format:
```json
{
  "headlines": {"AD_ID_1": ["H1", "H2", ...], "AD_ID_2": [...]},
  "descriptions": ["D1", "D2", "D3"]
}
```

### Stage 3: Resume and Write to Sheet
```bash
python scripts/rsa_refresh_generator.py \
  --cid YOUR_CID \
  --sheet-id YOUR_SHEET_ID \
  --copy-file copy_YOUR_CID.json
```

This merges AI copy with existing ad structure and writes to Google Sheets with "Original RSAs" and "Refreshed RSAs" tabs. Review in the sheet before importing to Google Ads Editor.

## Key Rules
- **Empty > Inaccurate** -- never include unverified claims
- Only use information explicitly found on the business website
- See `references/hallucination-filter.md` for forbidden terms
- LOW-performing assets are the primary replacement targets
- BEST and GOOD assets (and all customizer assets) are preserved

## Prerequisites
- `google-ads.yaml` at project root (Google Ads API credentials)
- `token-sheets.json` at project root **OR** a refresh token in `google-ads.yaml` with the spreadsheets scope
- `FIRECRAWL_API_KEY` environment variable (set in `.env` or shell — get a key at firecrawl.dev)
- `pip install google-ads gspread google-auth pyyaml python-dotenv firecrawl-py requests beautifulsoup4 playwright`

Override paths if needed:
```bash
--config path/to/google-ads.yaml --sheets-token path/to/token-sheets.json
```

## Optional: Pre-Refresh Baseline
```bash
python scripts/rsa_baseline_snapshot.py \
  --cid YOUR_CID \
  --account-name "Account Display Name" \
  --sheet-id YOUR_SHEET_ID
```
Captures IWQS, QS components, ad metrics, and impression share before making changes so you can measure improvement afterward. Writes to an "RSA Baseline" tab.

You can also have the generator capture the baseline automatically by adding `--baseline-sheet-id YOUR_SHEET_ID` to Stage 1.

## Vertical Note

The helpers in `scripts/rsa_refresh_generator.py` (`generate_keyword_headlines`, `generate_brand_headline`) and the reference docs under `references/` are tuned for **property management** (apartment / rental) accounts. To adapt for another vertical:

1. Replace the three files under `references/` with your own headline structure, voice guide, and hallucination filter
2. Update the `HALLUCINATION_PATTERNS` list in the generator to match your industry's unverifiable claims
3. Rewrite `generate_keyword_headlines` for your ad-group taxonomy

## Optional Enhancements

Set these env vars to enable additional context when generating copy:

- `COMPLIANCE_PATH` — directory containing a `compliance/ad_copy_validator.py` module to add geographic validation (checks headlines reference the correct city/state)
- `SERP_API_PATH` — directory containing `get_gmb_reviews.py` and `analyze_competitors_for_rsa.py` to add Google My Business social proof and competitor USP analysis to the context JSON

Both are optional. The script gracefully skips these features when the modules aren't available.

## Related Skills
- `ad-copy-verification-standard` -- Mandatory verification protocol
- `google-ads-creation` -- RSA validation rules
