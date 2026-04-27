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

- **Credentials:** Valid Google Ads API credentials at `./google-ads.yaml`
- **Account:** Know the CID of the account you're building for (or maintain
  your own local `accounts.json` lookup — keep it out of source control)
- **Ad Copy:** Either pasted by user or read from a Google Sheet via Sheets API

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
    if 'PROPERTY_NAME' in acc.get('name', '').lower():
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
# Scrape property website for address
python scripts/scrape_website_firecrawl.py --url "PROPERTY_URL"
# Then geocode the address using Nominatim
```

### Step 4: Get Ad Copy

**From Google Sheet (shared folder):**
```bash
python3 -c "
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

with open('token.json') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)
service = build('sheets', 'v4', credentials=creds)

# Read ad copy from the property's sheet
# Rows 3-17: 15 headlines (30 chars each)
# Rows 22-26: 5 long headlines (90 chars each)
# Rows 28-32: 5 descriptions (90 chars each)
result = service.spreadsheets().values().get(
    spreadsheetId='[SHEET_ID]',
    range='A3:A32'
).execute()
values = result.get('values', [])
"
```

**Sheet format (confirmed):**
- Rows 3-17: 15 headlines (30 chars each) -> CSV cols 38-52
- Rows 19-20: Short headline (60 chars) -> IGNORE
- Rows 22-26: 5 long headlines (90 chars) -> CSV cols 53-57
- Rows 28-32: 5 descriptions (90 chars) -> CSV cols 58-62

**Manual fallback:** User pastes headlines/descriptions into conversation.

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
    --headlines "H1|H2|H3|H4|H5|H6|H7|H8|H9|H10|H11|H12|H13|H14|H15" \
    --long-headlines "LH1|LH2|LH3|LH4|LH5" \
    --descriptions "D1|D2|D3|D4|D5" \
    --video-ids "a8Nr45dNL50|GFIOY7vdf4k" \
    --remarketing-segments "Acme Plumbing;All visitors (AdWords);All Users of 12345 | Acme Plumbing - BLP" \
    --output "data/pmax-builds/acme-plumbing-pmax.csv"
```

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

## Files

| File | Purpose |
|------|---------|
| `scripts/build_pmax_csv.py` | CSV generator (115 cols, UTF-16LE) |
| `templates/negative_locations.json` | 238 country exclusions |
| `templates/search_themes.json` | 14 search theme templates (8 generic + 6 location-specific) |
| `templates/audience_signals.json` | Standard standard audience signals |
| `templates/campaign_settings.json` | Standardax campaign defaults |

## Manual Steps (Not in CSV)

1. **Images:** Download from shared folder, upload in Google Ads Editor after CSV import
2. **Pause GDN:** If build request says to pause GDN Retargeting campaign, do via API or Editor
3. **Retargeting audience:** Add to PMax asset group audience signals (included in CSV if --remarketing-segments provided)
4. **Budget adjustment:** CSV defaults to $10/day; adjust post-import based on build request budget

## Ad Copy Sheet Location

Each business has a sub-folder with a "PMax Ad Copy" Google Sheet.
Access via Google Sheets API with `credentials/token-sheets.json`.
