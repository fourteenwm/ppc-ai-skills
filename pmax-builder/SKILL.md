---
name: pmax-builder
description: Build Performance Max campaigns and output Google Ads Editor-importable CSV (115 columns, UTF-16LE). Auto-invoke when user says "build pmax", "pmax build", "new pmax campaign", "pmax csv", or references a todo file with `pmax-build` in the name. Generates CSV from a campaign brief plus YouTube videos and ad copy.
allowed-tools: [Bash, Read]
---

# PMax Campaign Builder

Build Performance Max campaigns for accounts and output Google Ads Editor-importable CSV.

## Triggers

Auto-invoke when user says "build pmax", "pmax build", "new pmax campaign", "pmax csv", or references a todo file with `pmax-build` in the name.

## Prerequisites

- **Credentials:** `google-ads.yaml` at project root — see the [google-ads-api-setup](../google-ads-api-setup/) skill if you don't have one. The Sheets ad-copy mode (Step 4) reuses this same file's OAuth credentials for the Sheets API — its refresh token must carry the `spreadsheets` + `drive.readonly` scopes, which the setup skill's generator grants by default (token predates that? re-run the generator once)
- **Account:** Know the CID of the account you're building for (or maintain
  your own local `accounts.json` lookup — keep it out of source control)
- **Ad Copy:** Either read from a Google Sheet (`--sheet-id`, preferred) or pasted by the user (manual fallback, no Google credentials needed)

## Workflow

### Step 1: Parse the Todo File

Read the build request (e.g., `todo/todo-20260319-acme-plumbing-pmax-build.md`) to extract:
- Account name
- YouTube video URLs
- Ad copy source (Google Sheet link or pasted text)
- Budget info
- Additional instructions (pause GDN, add retargeting, etc.)

### Step 2: Lookup Account CID

If you keep a local `accounts.json` (list of `{name, id}` objects):

```bash
python3 -c "
import json
with open('accounts.json') as f:
    accounts = json.load(f)
for acc in accounts:
    if 'acme' in acc.get('name', '').lower():
        print(f'{acc[\"name\"]}: {acc[\"id\"]}')
"
```

Or pass the CID directly to the build script — no lookup needed.

### Step 3: Get Business Location Data

**Option A: From existing GEO campaign (preferred)**
```bash
python3 -c "
from google.ads.googleads.client import GoogleAdsClient
client = GoogleAdsClient.load_from_storage('google-ads.yaml')
ga = client.get_service('GoogleAdsService')
query = '''
    SELECT campaign.name,
           campaign_criterion.location.geo_target_constant,
           campaign_criterion.proximity.geo_point.latitude_in_micro_degrees,
           campaign_criterion.proximity.geo_point.longitude_in_micro_degrees,
           campaign_criterion.proximity.radius,
           campaign_criterion.proximity.radius_units
    FROM campaign_criterion
    WHERE campaign.name LIKE '%GEO%'
    AND campaign_criterion.type = 'PROXIMITY'
    AND campaign.status != 'REMOVED'
'''
for row in ga.search(customer_id='[CUSTOMER_ID]', query=query):
    lat = row.campaign_criterion.proximity.geo_point.latitude_in_micro_degrees / 1e6
    lon = row.campaign_criterion.proximity.geo_point.longitude_in_micro_degrees / 1e6
    radius = row.campaign_criterion.proximity.radius
    print(f'Lat: {lat}, Lon: {lon}, Radius: {radius}mi')
"
```

**Option B: Scrape from website + geocode**
```bash
# Scrape the business website for its address
python scripts/scrape_website_firecrawl.py --url "BUSINESS_URL"
# Then geocode the address using Nominatim
```

### Step 4: Get Ad Copy

**From Google Sheet (preferred):** pass `--sheet-id` to the build script in Step 7 —
it reads the ad copy rows directly, authenticating with the OAuth credentials from
`google-ads.yaml` (project root by default; override with `--config <path>`). No
separate Sheets token: the refresh token minted by
[google-ads-api-setup](../google-ads-api-setup/) already carries the required
`spreadsheets` + `drive.readonly` scopes.

**Sheet format (confirmed, first tab, column A):**
- Row 1: Business name; Row 2: "PMax Ad Copy" title
- Rows 4-18: 15 headlines (30 chars each, label in row 3) -> CSV cols 38-52
- Row 20: Short headline (60 chars, label in row 19) -> IGNORED
- Rows 22-26: 5 long headlines (90 chars each, label in row 21) -> CSV cols 53-57
- Rows 28-32: 5 descriptions (90 chars each, label in row 27) -> CSV cols 58-62

**Manual fallback:** User pastes headlines/descriptions into conversation; pass them
via `--headlines` / `--long-headlines` / `--descriptions` (no Google credentials needed).

### Step 5: Extract Video IDs

Parse YouTube URLs from the todo file:
```
https://youtu.be/a8Nr45dNL50 -> a8Nr45dNL50
https://youtu.be/GFIOY7vdf4k -> GFIOY7vdf4k
```

### Step 6: Get Remarketing Audiences

```bash
python3 -c "
from google.ads.googleads.client import GoogleAdsClient
client = GoogleAdsClient.load_from_storage('google-ads.yaml')
ga = client.get_service('GoogleAdsService')
query = '''
    SELECT user_list.name, user_list.size_for_search, user_list.type
    FROM user_list
    WHERE user_list.type IN ('REMARKETING', 'RULE_BASED')
'''
for row in ga.search(customer_id='[CUSTOMER_ID]', query=query):
    print(f'{row.user_list.name} ({row.user_list.size_for_search})')
"
```

Format for CSV: `"AccountName;All visitors (AdWords);All Users of GA_ID | BusinessName - BLP"`

### Step 7: Run the CSV Generator

```bash
python3 .claude/skills/pmax-builder/scripts/build_pmax_csv.py \
    --campaign-name "Pmax: Acme Plumbing" \
    --asset-group-name "General" \
    --business-name "Acme Plumbing" \
    --final-url "https://www.acmeplumbing.com/" \
    --city "Dallas" --state "TX" \
    --lat 32.7767 --lon -96.7970 --radius 40 \
    --budget-daily 10.00 \
    --sheet-id "[SHEET_ID]" \
    --video-ids "a8Nr45dNL50|GFIOY7vdf4k" \
    --remarketing-segments "Acme Plumbing;All visitors (AdWords);All Users of 12345 | Acme Plumbing - BLP" \
    --output "data/pmax-builds/acme-plumbing-pmax.csv"
```

Manual ad-copy fallback: replace `--sheet-id` with
`--headlines "H1|...|H15" --long-headlines "LH1|...|LH5" --descriptions "D1|...|D5"`.
If your `google-ads.yaml` isn't at the working directory root, add `--config path/to/google-ads.yaml`.

### Step 8: Present Output

Present output to user:
1. CSV file path
2. Summary of what was generated (rows, themes, videos)
3. Remind about manual image step
4. Note any additional instructions from the build request (pause GDN, etc.)

## CSV Format

- **Encoding:** UTF-16LE with BOM
- **Delimiter:** Tab
- **Line endings:** CRLF
- **Columns:** 115
- **Row types:** Campaign (1) + Asset Group (1) + Search Themes (14) + Location (1) + Negative Locations (238) = ~255 rows

## Standard Settings

| Setting | Value |
|---------|-------|
| Campaign Type | Performance Max |
| Networks | Google search;Search Partners;Display Network |
| Bid Strategy | Maximize conversion value |
| Budget | $10/day (standard, adjust later) |
| Targeting | Location of presence |
| Final URL expansion | Disabled |
| Text customization | Disabled |
| Image/Video enhancement | Disabled |
| Brand guidelines | Enabled |
| CTA | Automated |
| Start date | 3 business days from build |
| End date | June 30 current FY |

## Vertical Note

The shipped templates `templates/search_themes.json` and `templates/audience_signals.json`
are **multifamily / apartment defaults** — apartment-rental search themes and
Renters / Moving-Soon audience signals — even though the doc examples say "Acme
Plumbing". Import them unedited and your PMax campaign targets apartment hunters.
To adapt for your vertical:

1. Replace the `generic` and `location_specific` lists in `templates/search_themes.json` with your own service terms (`{city}` / `{state}` placeholders are substituted at build time)
2. Replace `interest_categories`, `life_events`, and `detailed_demographics` in `templates/audience_signals.json` with your vertical's audience taxonomy values (or set them to `""` to ship no audience signals beyond remarketing)
3. No script changes needed — the generator builds whatever these files contain

`campaign_settings.json` (bidding/network defaults) and `negative_locations.json`
(country exclusions) are vertical-neutral.

## Files

| File | Purpose |
|------|---------|
| `scripts/build_pmax_csv.py` | CSV generator (115 cols, UTF-16LE) |
| `templates/negative_locations.json` | 238 country exclusions |
| `templates/search_themes.json` | 14 search theme templates (8 generic + 6 location-specific) — multifamily defaults, see Vertical Note |
| `templates/audience_signals.json` | Standard audience signals — multifamily defaults, see Vertical Note |
| `templates/campaign_settings.json` | PMax campaign defaults |

## Manual Steps (Not in CSV)

1. **Images:** Download from shared folder, upload in Google Ads Editor after CSV import
2. **Pause GDN:** If build request says to pause GDN Retargeting campaign, do via API or Editor
3. **Retargeting audience:** Add to PMax asset group audience signals (included in CSV if --remarketing-segments provided)
4. **Budget adjustment:** CSV defaults to $10/day; adjust post-import based on build request budget

## Ad Copy Sheet Location

Keep each business's "PMax Ad Copy" Google Sheet in its own Drive folder.
Access goes through the Google Sheets API using the same `google-ads.yaml`
OAuth credentials as everything else in this skill — just pass the sheet ID
via `--sheet-id`.
