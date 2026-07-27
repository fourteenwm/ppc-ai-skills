---
name: pmax-builder
description: Build Performance Max campaigns and output Google Ads Editor-importable CSV (115 columns, UTF-16LE). Auto-invoke when user says "build pmax", "pmax build", "new pmax campaign", "pmax csv", or references a todo file with `pmax-build` in the name. Generates CSV from a campaign brief plus YouTube videos and ad copy.
allowed-tools: [Bash, Read]
---

# PMax Campaign Builder

Build Performance Max campaigns from a campaign brief and output a Google
Ads Editor-importable CSV. Judgment calls (copy-source selection, template
editing, the final-URL rule, pre-import checks) live in
[rules.md](rules.md); exact script mechanics live in
[references/build-contract.md](references/build-contract.md).

## What this skill deliberately does NOT do

- **Never touches a live account.** No API mutations, no uploads — the
  product is a CSV file, and Google Ads Editor import is the deliberate
  human review gate between this skill and anything serving.
- **Doesn't validate your ad copy.** No length checks, no minimum-count
  checks — blank sheet rows silently shrink the copy. The console counts
  and a CSV spot-check are your gate (rules.md, invariant 4).
- **Doesn't verify the final URL.** The generator writes whatever
  `--final-url` you pass. Sourcing it from the account's live Search ads is
  an operator rule (rules.md, invariant 1), enforced by you in Step 3.
- **Doesn't write ad copy.** It ingests existing copy verbatim. Writing new
  copy is a different job — see the routing table below.
- **Doesn't handle images.** Image assets are uploaded manually in Editor
  after import (Manual Steps below).

## Prerequisites

- **Credentials:** `google-ads.yaml` at project root — see the
  [google-ads-api-setup](../google-ads-api-setup/) skill if you don't have
  one. The Sheets ad-copy mode reuses this same file's OAuth credentials for
  the Sheets API — its refresh token must carry the `spreadsheets` +
  `drive.readonly` scopes, which the setup skill's generator grants by
  default (token predates that? re-run the generator once)
- **Account:** Know the CID of the account you're building for (or maintain
  your own local `accounts.json` lookup — keep it out of source control)
- **Ad Copy:** Either read from a Google Sheet (`--sheet-id`, preferred) or
  pasted by the user (manual fallback, no Google credentials needed). Keep
  each business's "PMax Ad Copy" sheet in its own Drive folder. Choosing
  between the two modes: rules.md § "Sheets mode vs manual paste"

## Workflow

### Step 1: Parse the Build Request

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

### Step 3: Confirm the Final URL From Search

Never construct the URL from the business name or the brief — pull the root
domain the account's ENABLED Search ads actually use (the why: rules.md,
invariant 1):

```bash
python3 -c "
from google.ads.googleads.client import GoogleAdsClient
from urllib.parse import urlparse
client = GoogleAdsClient.load_from_storage('google-ads.yaml')
ga = client.get_service('GoogleAdsService')
query = '''
    SELECT ad_group_ad.ad.final_urls
    FROM ad_group_ad
    WHERE campaign.status = \"ENABLED\"
      AND ad_group.status = \"ENABLED\"
      AND ad_group_ad.status = \"ENABLED\"
      AND campaign.advertising_channel_type = \"SEARCH\"
'''
counts = {}
for batch in ga.search_stream(customer_id='[CUSTOMER_ID]', query=query):
    for row in batch.results:
        for url in row.ad_group_ad.ad.final_urls:
            host = urlparse(url if '://' in url else 'https://'+url).netloc.lower()
            if host.startswith('www.'): host = host[4:]
            counts[host] = counts.get(host, 0) + 1
for host, n in sorted(counts.items(), key=lambda x: -x[1]):
    print(f'{n:>4}  {host}')
"
```

One root → pass a URL on that root as `--final-url` in Step 8. Multiple
roots, or no Search campaigns at all → stop; rules.md § "Escalation
defaults" owns that call.

### Step 4: Get Business Location Data

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

The bundled scraper handles both current (attribute-style) and legacy (dict)
Firecrawl SDK responses, and is scrape-only by design — no LLM extraction.

### Step 5: Get Ad Copy

**From Google Sheet (preferred):** pass `--sheet-id` to the build script in
Step 8 — it reads the copy cells directly (verbatim ingestion, no retyping),
authenticating with the OAuth credentials from `google-ads.yaml` (project
root by default; override with `--config <path>`).

The sheet layout the script expects (first tab, column A, rows 4-18 /
22-26 / 28-32 — and the row-20 slot it deliberately ignores) is documented
in [references/build-contract.md](references/build-contract.md) § "The
Google Sheet contract". **After the read, check the printed counts against
what the sheet should contain** — blank or misplaced rows are skipped
silently.

**Manual fallback:** User pastes headlines/descriptions into conversation;
pass them via `--headlines` / `--long-headlines` / `--descriptions` (all
three required; no Google credentials needed).

### Step 6: Extract Video IDs

Parse YouTube URLs from the build request:
```
https://youtu.be/a8Nr45dNL50 -> a8Nr45dNL50
https://youtu.be/GFIOY7vdf4k -> GFIOY7vdf4k
```

`youtu.be`, `watch?v=`, and `/embed/` URLs extract automatically; anything
else (shorts links especially) passes through verbatim — hand the script
bare 11-character IDs when in doubt (contract § "Video ID extraction").

### Step 7: Get Remarketing Audiences

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

### Step 8: Run the CSV Generator

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

### Step 9: Verify and Present

1. Read the console summary against rules.md's false-alarm table — counts
   vs the source, the `Dates:` line (late-June trap), theme/row totals
2. Spot-check the CSV's asset-group row (copy slots, Video ID columns)
3. Present: CSV path, what was generated (rows, themes, videos), the manual
   image step, and any extra instructions from the build request (pause
   GDN, etc.)

## CSV Format

UTF-16LE with BOM, tab-delimited, CRLF, exactly 115 columns per row —
~255 rows with the shipped templates. Full row-assembly and encoding
mechanics: [references/build-contract.md](references/build-contract.md).
Campaign defaults (networks, bidding, automation opt-outs) live in
`templates/campaign_settings.json`; start/end dates are script-computed
(3 business days out / June 30 of the current fiscal year).

## Vertical Note

The shipped `search_themes.json` and `audience_signals.json` are
**multifamily/apartment defaults** — import them unedited and your campaign
targets apartment hunters, whatever you sell. Editing them for your vertical
(which file, which fields, what the inert keys are): rules.md § "Editing the
templates for your vertical".

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — workflow + routing |
| `rules.md` | Judgment layer: invariants, copy-source decision, template editing, false alarms, escalation |
| `examples.md` | Three worked builds (copy-count catch, vertical adaptation, the late-June date trap) |
| `references/build-contract.md` | Line-derived script mechanics: sheet contract, caps, dates, row assembly, encoding, inert template keys |
| `scripts/build_pmax_csv.py` | CSV generator (115 cols, UTF-16LE) |
| `scripts/scrape_website_firecrawl.py` | Website scraper (address sourcing for Step 4B) — scrape-only |
| `templates/negative_locations.json` | 238 country exclusions |
| `templates/search_themes.json` | 14 search theme templates (8 generic + 6 location-specific) — multifamily defaults, see Vertical Note |
| `templates/audience_signals.json` | Standard audience signals — multifamily defaults, see Vertical Note |
| `templates/campaign_settings.json` | PMax campaign defaults |

## After a Run

The generated CSV at `--output` (house convention:
`data/pmax-builds/<business>-pmax.csv`) is the run's only artifact — the
scripts write nothing else, and no account state changes until a human
imports the file in Google Ads Editor. The console summary is not persisted;
a cold session reconstructs any build by reading the CSV itself (or simply
regenerating it — builds are deterministic for the same inputs except the
two computed dates). Scrape runs (Step 4B) persist only if you passed
`--output` to the scraper.

## Manual Steps (Not in CSV)

1. **Images:** Download from shared folder, upload in Google Ads Editor after CSV import
2. **Pause GDN:** If build request says to pause GDN Retargeting campaign, do via API or Editor
3. **Retargeting audience:** Add to PMax asset group audience signals (included in CSV if --remarketing-segments provided)
4. **Budget adjustment:** CSV defaults to $10/day; adjust post-import based on build request budget

## When to Load What

| Moment | Load |
|---|---|
| Before any build — mode choice, template edits, the URL rule | [rules.md](rules.md) |
| Exact ingestion/caps/dates/encoding questions | [references/build-contract.md](references/build-contract.md) |
| First build, or something looks off in the summary | [examples.md](examples.md) |
| No `google-ads.yaml` yet, or a Sheets 403 | [google-ads-api-setup](../google-ads-api-setup/) |
| Writing NEW ad copy for the sheet (not ingesting existing copy) | [ad-copy-generation-framework](../ad-copy-generation-framework/) + [ad-copy-verification-standard](../ad-copy-verification-standard/) |
| After every Editor import — confirm the automation opt-outs landed | [pmax-asset-automation](../pmax-asset-automation/) |
