# Pipeline Contract — rsa-single-account

> **Source of truth: the scripts in [`scripts/`](../scripts/).** This file restates their
> exact behavior at documentation altitude — if a script and this file disagree, the script
> wins and this file has a bug. Any change to a script's selection filters, thresholds,
> formatting, or output contract must update this file and the repo CHANGELOG. Line numbers
> reference the shipped scripts.
>
> One thing the scripts deliberately do NOT do: generate copy. Steps 1–6 gather and verify
> inputs; Step 8 lands output. Generation itself (Step 7) is performed by you, governed by
> the two companion skills — no script writes a headline.

---

## Step 1 — Account selection (`check_active_accounts.py`)

**Account-list resolution, first match wins** (`:136-152`):

1. `--accounts` registry (default `./accounts.json`) — entries used **as-is**: the script
   never checks a registry account's status, so a canceled or inaccessible registry row
   surfaces later as a per-account query error, not as a filtered row. Invalid JSON exits 1;
   a missing file (or an empty `accounts` map) falls through to the walk.
2. MCC walk — `customer_client` under the `login_customer_id` in `google-ads.yaml`, filtered
   `status = 'ENABLED' AND manager = FALSE` (`:98-108`). No `login_customer_id` and no
   registry → error + exit 1.

**"Active" gate:** one GAQL pull per account, `FROM customer WHERE segments.date DURING
THIS_MONTH` (`:160-166`); an account is listed only when month-to-date cost > $0 (`:181`).
Consequences to read correctly:

- **Zero-MTD-spend accounts print nothing** — they appear only in the
  `Total accounts checked:` count. Absent from the list ≠ absent from the MCC.
- A per-account query failure prints `{cid}: {name} - Error` (`:184-185`) and the account is
  excluded from the active list. `- Error` is not "no spend."
- `--name` filters the resolved list by case-insensitive substring **before** the spend
  check (`:154-156`); `--exclude` CIDs print `- EXCLUDED` and are never queried (`:172-174`).

**Output:** per-account lines `{cid}: {name} - ${spend:,.2f}`, a summary block, then an
`Active account IDs (for batch processing):` list (`:194-198`). Exit 0 even when zero
accounts are active.

## Step 2 — Website discovery (`get_account_website_url.py`)

CID is read from **stdin** with the prompt `Enter customer ID (no dashes): ` — dashes are
actually stripped (`:55`), so a dashed CID works (empty stdin errors + exit 1). Three
passes, each pass's failure printed and non-fatal — once a CID is read, the script always
exits 0:

1. Customer-level URL settings — also prints `Account: {descriptive_name}`, the business
   name Step 6 uses (`:63-84`).
2. Campaign URL settings, ENABLED campaigns, `LIMIT 5` (`:87-95`).
3. Ad final URLs: `FROM ad_group_ad WHERE ad_group_ad.status = 'ENABLED' LIMIT 10`
   (`:111-119`). **No campaign or ad-group status filter** — an ENABLED ad inside a paused
   campaign still contributes URLs.

**The domain vote** (`:126-151`): URLs are deduplicated into a set, domains counted per
**unique URL** (`url.split('/')[2]`), and the max prints as
`{domain} ({count} ads)` — the label says "ads" but the number is unique URLs on that
domain. `Primary website likely: https://{domain}` is a vote over at most 10 ads' URLs,
paused campaigns included — verify it is really the client's site before Step 5.

## Step 3 — Competitive analysis (`analyze_competitors_for_rsa.py`)

**Config resolution** (`:64-97`): `--vertical` defaults to `auto_repair`; an unknown
vertical warns and falls back to `auto_repair` (`:89-93`); a missing
`vertical_configs.json` warns and uses a built-in auto-repair default (`:81-83,100-133`).

**Inert config keys:** the script reads only `usp_keywords`, `service_keywords`,
`cta_keywords`, and `display_name`. The JSON's `search_term_template`,
`saturation_threshold`, and `unique_threshold` keys are **never consumed by any code
path** — the thresholds below are hardcoded in `identify_gaps()`. Editing those JSON keys
changes nothing; the keyword maps are the real per-vertical lever.

**Analysis surface** (`:205-259`): the top **5** paid ads (`ads_results[:5]`, `:213`) and
top **3** Local Service Ads (`:251`). Matching runs on `title + description`, lowercased
(`:226`) — sitelinks are fetched but never analyzed. LSAs contribute only
`social_proof_types` ratings, never USP/service/CTA counts.

**Counting is per keyword match, not per competitor** (`:229-232`): every matching fragment
appends its category once, so one ad containing `fitness`, `fitness center`, and
`24-hour fitness` scores **Fitness Center ×3 by itself**. The console label
`(mentioned by N competitors)` (`:418`) reports these match counts. Top-10 USPs, top-10
services, top-5 CTAs survive into the output (`:262-280`).

`Competitors Found` = **all** returned ads + LSAs (`:282`), uncapped — the count can exceed
the 5 + 3 actually analyzed.

**Gap logic — hardcoded thresholds** (`:287-337`):

- "Common" competitor USP = frequency ≥ **2** (`:306-309`).
- Saturated = frequency ≥ **3** → `DE-EMPHASIZE` (`:328-335`).
- Unique-to-client = a client USP with no bidirectional substring overlap against any
  common competitor **category label** (`:316-319`). Label-vs-free-text comparison is
  coarse — e.g. "ASE Certified Master Technicians" does not substring-match the label
  "Licensed/Certified" and would flag unique even when certification claims are saturated.
  Treat unique flags as advisory; the saturation counts are the reliable half.
- `underemphasized_by_competitors` and `differentiation_angles` are initialized and **never
  populated** (`:298-303`) — always empty in the output.

**The example-USP artifact** (`:430-441`): the script computes its gap analysis against
four **hardcoded example client USPs** (the console prints
`Example client USPs (replace with actual from website):` first). In
`competitive_insights.json`, everything under `gap_analysis` and `rsa_insights` that names
client USPs reflects those examples — only `competitor_analysis` (the counts) is real
account data. At Step 7 you re-apply the 2+/3+ logic to the client's **real** USPs from the
Step-5 scrape.

**Artifact:** `competitive_insights.json` in the working directory (`:476-483`) —
`competitor_analysis` + `gap_analysis` + `rsa_insights` + `vertical`. No timestamp inside.
Missing `SERP_API_KEY` or a failed SERP call → `[ERROR] Failed to retrieve competitor data`
+ exit 1 (`:403-405`).

## Step 4 — Campaign structure (`get_search_campaign_structure.py`)

One GAQL query (`:60-74`), all four conditions:

```
campaign.status = 'ENABLED'
AND campaign.advertising_channel_type = 'SEARCH'
AND campaign.name LIKE '%Search%'
AND ad_group.status = 'ENABLED'
```

`FROM ad_group`, ordered by campaign then ad group name. Input CID may carry dashes
(stripped, `:124`).

**Zero rows exits like a failure:** an empty result is falsy, so the script prints
`Found 0 ad groups across campaigns:` and then `[ERROR] Failed to retrieve campaign
structure` + exit 1 (`:128-132`) — the same exit as a real API error. The console above the
`[ERROR]` line is how you tell them apart. An account whose Search campaigns aren't *named*
with "Search" hits this path by design — adapt the LIKE clause to your naming convention,
in your fork.

## Step 5 — Scrape + extraction (`scrape_website_firecrawl.py`)

**Page set:** homepage, plus at most one services page and one about page auto-discovered
via Firecrawl's site map (`:102-161`). Discovery = first mapped URL containing
`/{keyword}` (or ending with it) from `['services','service','repairs','repair']` /
`['about','about-us','company','who-we-are']` (`:122-143`). Sub-pages are only scraped when
distinct from the homepage URL (`:146,155`).

**Failure asymmetry:** an empty/failed **homepage** scrape raises → `ERROR: …` + exit 1
(`:89-90,376-378`) — this is the workflow's hard STOP. A failed site **map** or sub-page
scrape only logs a warning and proceeds homepage-only (`:163-164`).

**Extraction contract** (`:200-284`): content concatenated homepage → services → about,
**truncated to the first 10,000 characters** (`:210`) — a long homepage can crowd the
services/about content out of the LLM's view entirely. Model `claude-haiku-4-5-20251001`,
`max_tokens=2048` (`:263-267`). Prompt-governed JSON schema (`:212-259`):

| Key | Constraint (from the prompt) |
|---|---|
| `services` | up to 20, Title Case |
| `credentials` | exact wording from the site |
| `features` | descriptive phrases, max 25 chars each, incl. hours |
| `history` | `{established_year, years_in_business, family_owned, notes}` |
| `specializations` | niches, brands, capabilities |

Markdown fences are stripped if present (`:272-275`); a response that still fails
`json.loads` raises → exit 1 (`:288-291`). The schema is prompt-enforced, not validated —
off-schema keys print as zero counts rather than erroring.

**Cache:** `--output <path>` writes the **extraction only** (`:367-370`) — no raw page
text, no URL, no timestamp inside the file. Re-verifying a claim against the actual site
text means re-scraping or scrolling the run's console.

## Step 6 — GBP reviews (`get_gmb_reviews.py`)

**Lookup** (`:74-106`): one SERP query `"{business_name} {location}"`; reads the
`local_results` panel. **No panel** → `[WARNING] No local results found for {name}` and an
empty result, exit 0 (`:96-102`) — distinct from a **failed SERP call**, which exits 1 via
`[ERROR] Failed to retrieve GBP reviews` (`:311-313`). The script never verifies the panel
belongs to the client — check the printed `Name:` against the business before using
anything below it.

**Rating headline — the 4.5 gate** (`:172-198`): `RATING_THRESHOLD = 4.5` (`:173`); a
rating+count headline is generated only when rating ≥ 4.5 **and** a review count exists
(`:176`). The threshold applies in **both** modes — `--apartment` changes only the
attribution noun (Resident vs Customer, `:167`). Count formatting (`:177-182`):
≥ 1000 → floor-to-thousands + `+` (2,347 → `2000+`); under 1000 → literal count + `+`.
Three formats are tried **first-fit ≤ 30 chars**, one headline max (`:185-198`); the third
pattern appends `+` to the already-suffixed count (`250++ Reviews`) — a latent quirk
reachable only when the first two patterns exceed 30 chars.

**Snippet headlines** (`:200-228`): top 5 snippets fetched (`:117`); a review missing its
own rating **inherits the business rating** (`:119`). The 5-star filter is exact equality
(`rating == 5`, `:202`) — and when *no* snippet passes it, the code falls back to **all
snippets, low-rated ones included** (`:205`). Each shipped snippet carries
`original_rating` — read it, and the full quote, before using the headline. Truncation
ladder (`:210-219`): < 22 chars whole → first sentence if < 22 → first ~18 chars to a word
boundary; format `"{snippet}" - {attribution}` must fit 30 (`:221-222`).

**Caps and keys:** at most **2** social-proof headlines returned (`:231`);
`rating_meets_threshold` reports the 4.5 test (`:235`). `get_apartment_social_proof()`
(`:239-266`) is the importable convenience wrapper (city + state → location) that the
sibling `rsa-refresh` skill consumes.

## Step 8 — Sheet write (`write_rsa_to_sheet.py`)

**Auth ladder** (`:70-109`): `--sheets-token` file (default `./token-sheets.json`,
spreadsheets scope) if it exists and loads → otherwise OAuth client + refresh token from
`--config google-ads.yaml` (that token must have been granted the spreadsheets scope — the
[google-ads-api-setup](../../google-ads-api-setup/) generator mints it by default). Neither
→ error + exit 1.

**Input:** `--sheet-id` accepts a bare ID or a full URL (`:60-67`). The JSON is validated
for **key presence only** (`:215-221`) — `account_name, campaign_name, ad_group_name,
headlines, descriptions` per entry; a missing key exits 1 naming the index and key.
**Nothing validates counts or lengths**: more than 15 headlines (or 4 descriptions) is
written as-is and **shifts every later column right** (`:148-166` pads short lists with
`''` but never truncates long ones); 30/90-char and Title Case discipline exist only in
your Step-7 validation.

**Write** (`:134-178`): clears `A:Z` on the **first tab** of the target spreadsheet, then
writes from `A1`, `valueInputOption='RAW'`. Header row = 22 columns:
`Account | Campaign | Ad Group | Headline 1–15 | Description 1–4` (A–V). One row per ad
group. No timestamp is written. Success prints `[SUCCESS] Successfully wrote to Google
Sheet` + the sheet URL; any Sheets error → `[ERROR] Failed to write to Google Sheet` +
exit 1.

Point `--sheet-id` only at a **dedicated** spreadsheet — whatever lives in A:Z on its first
tab is erased every run.

---

## Reading run state cold

No script writes a timestamp anywhere — file modification times and the Sheet's revision
history are the only clocks. What the working directory tells you:

| Artifact | Written by | Presence means |
|---|---|---|
| `competitive_insights.json` | Step 3 script | SERP analysis ran; counts real, client-USP fields are the example artifact |
| `website_data.json` (or your `--output` name) | Step 5 script | scrape + extraction succeeded — the verification source exists |
| `rsa_data.json` | **you, at Step 7** | generation finished and was serialized for the sheet write; a script wrote none of it |
| The output Sheet (first tab, A–V) | Step 8 script | last successful write — contents always reflect the most recent run only (clear-then-write) |

A directory with the two cache JSONs but no `rsa_data.json` = a run that stopped before
generation; resume at Step 7 without re-spending scrape/SERP credits. The Sheet holding
rows for an account ≠ those rows were imported — import happens in Google Ads Editor, and
[`change-history-checker`](../../change-history-checker/) is how you confirm what actually
landed afterward.
