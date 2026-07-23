# Refresh Contract — selection, file formats, merge mechanics, sheet output

> **Source of truth:** `scripts/rsa_refresh_generator.py` and
> `scripts/rsa_baseline_snapshot.py` — the scripts win over this document.
> Mirrors the shipped revision as of 2026-07-23. Any behavior change in
> either script must update this contract and the CHANGELOG in the same
> commit. The copy-quality standard itself lives in the other three
> reference files; this file owns the *mechanics*.

What the pipeline selects, what each stage reads and writes, what the merge
guarantees (and what it doesn't), and exactly what lands in the sheet.
Judgment about *using* any of this lives in [`rules.md`](../rules.md).

---

## Selection scope

One account per run (`--cid`, required). The RSA query pulls ads where:

- `ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD`
- `ad_group_ad.status = ENABLED`
- `campaign.status = ENABLED`

There is **no ad-group status filter** — an enabled ad inside a paused ad
group is still selected (it isn't serving, but it will appear in the sheet).
Paused ads and paused campaigns are invisible to the refresh.

## Asset performance labels

A second query reads `ad_group_ad_asset_view` (enabled assets, enabled
campaigns) and merges labels into the ad data **by exact asset text**:

- Ad has rows in the view, text matches → that asset's label
  (`BEST` / `GOOD` / `LOW` / `LEARNING` / `PENDING`).
- Ad has rows in the view, text doesn't match any of them → `UNKNOWN`.
- Ad has **no** rows in the view at all → every asset on it is `NO_DATA`.
- The whole performance query fails (permissions, API error) → a console
  warning (`Warning: Could not query asset performance`) and **every ad**
  gets `NO_DATA` on every asset. The run continues — label failure is
  non-fatal, so an all-`NO_DATA` context is a query failure symptom, not an
  account trait ([`rules.md`](../rules.md) false-alarm table).

## Stage 1 — `--prepare-for-claude` → `rsa_context_{cid}.json`

Written to the working directory. Fields:

| Field | Content |
|---|---|
| `cid`, `account_name` | Account identity |
| `property_url` | The **first returned ad's** final URL — this is what gets scraped. Multi-domain accounts: verify it before trusting the scrape |
| `features` | Property name / city / state / amenity lists. Without the compliance module (below), only `property_name` is filled — parsed from the URL domain. Carries `scrape_failed: true` when scraping failed |
| `website_text` | Scraped site content, capped at 15,000 characters. **Empty when the scrape failed** |
| `gmb_social_proof` | Review data from the SERP hook, or `null` |
| `competitor_insights` | Competitor USP/gap analysis from the SERP hook, or `null` |
| `ads` | Per ad ID: `ad_group_name`, `campaign_name`, `existing_headlines`, `headlines_needed`, `existing_descriptions`, `customizer_descriptions` |
| `instructions` | The generation brief: `references/pm-headline-structure.md` + `references/description-voice-lifting.md` **embedded verbatim**, plus inline social-proof / competitor / quality rules. `hallucination-filter.md` is NOT embedded — Stage 2 loads it from the skill folder |

`headlines_needed` = 15 minus the count of existing headlines whose label is
anything **other than** `LOW`. Customizers, `UNKNOWN`, and `NO_DATA` all
count as "not LOW," so the number is a conservative sizing hint for refresh
mode — not an order. Rebuild mode ignores it. If the performance query
failed (all `NO_DATA`), this reads 0 everywhere.

**Stage 1 does not stop on a failed scrape.** The context JSON is written
anyway, with `scrape_failed: true` and empty `website_text`. The early-exit
that writes error rows applies only to non-prepare runs. Checking
`scrape_failed` before generating is Stage 2's first duty.

## Stage 2 — the agent writes `copy_{cid}.json`

```json
{
  "headlines": {"AD_ID_1": ["H1", "H2", "..."], "AD_ID_2": ["..."]},
  "descriptions": ["D1", "D2", "D3"]
}
```

- Headline lists are keyed by ad ID (string or int both resolve).
- Descriptions are account-wide — 3 generated, applied to every ad.
- A legacy flat format (`{"AD_ID": [headlines]}` with no `descriptions` key)
  is still accepted; original descriptions are then carried forward.
  `--headlines-file` is a deprecated alias for `--copy-file`.

## Stage 3 — `--copy-file` merge mechanics

What the merge guarantees, in order, per ad:

1. **Customizer headlines** (`{CUSTOMIZER.…}` pattern) are preserved first,
   with their pin state, logged in `Changes Made`. **This is the only
   mechanical preservation.** A BEST or GOOD headline survives only if
   Stage 2 re-included its text in the copy file.
2. Copy-file headlines are added in list order until the ad holds 15.
3. Headlines **over 30 characters are skipped**, each logged
   (`Skipped (>30 chars): …`) — over-limit copy never reaches the sheet.
4. Duplicates are dropped by case-insensitive exact text — **silently** (no
   `Changes Made` line for a dedupe drop).
5. An ad ending up **below 10 headlines is skipped entirely**: console
   `[SKIP] Ad group '…' has only N/15 headlines (below minimum 10)`, and the
   ad is excluded from **both** sheet tabs. The console is the only record.
6. Descriptions: customizer descriptions preserved in place, then generated
   descriptions fill to 4 total; over-90-character descriptions are skipped
   with a log line.

**Stage 3 re-runs the whole pipeline** — it re-queries live ads and
re-scrapes the site before merging:

- Ads changed between stages: copy keyed to a now-gone ad ID is ignored; a
  new ad not in the copy file gets customizers only (usually <10 → skipped).
- **A resume-time scrape failure writes error rows even though your copy
  file is fine** — the scrape-failed gate fires on every non-prepare run,
  and the re-scraped content is not otherwise used by the merge. Site down
  at resume ⇒ retry Stage 3 when it's back; the copy file is untouched.

On a failed scrape outside prepare mode, every ad's row becomes 15 headlines
+ 4 descriptions of `SCRAPE FAILED - NO COPY GENERATED` with an ERROR change
note — written to the sheet (append rules below) unless `--dry-run`.

## Scrape ladder

1. **Firecrawl** (`FIRECRAWL_API_KEY`): markdown scrape of `property_url`,
   then a site map and **one** additional page whose URL contains
   `amenities` / `features` / `floor-plan` / `floorplan`, appended.
2. **requests + BeautifulSoup** fallback: page text (nav/footer/script
   stripped), meta description prepended, capped at 15,000 chars.
3. **Playwright** fallback: 3 attempts with escalating wait strategies,
   capped at 15,000 chars.

All three fail → `scrape_failed` (fork by mode described above).

## Optional enrichment hooks — gating

| Env var | Loads | Effect when present |
|---|---|---|
| `COMPLIANCE_PATH` | `compliance/ad_copy_validator.py` | Geographic validation of generated headlines at Stage 3 (`--strict` blocks output on errors; default flags only) AND property metadata (`property_name`/`city`/`state`) from its `property_locations.json` |
| `SERP_API_PATH` | `get_gmb_reviews.py` + `analyze_competitors_for_rsa.py` | Stage-1 GMB social proof + competitor USP/gap analysis added to the context JSON |

Both are optional; the script prints a note and skips cleanly when a module
isn't loadable. **The two hooks are coupled:** the GMB lookup fires only
when `property_name` + `city` + `state` are all present, and the competitor
analysis only with `city` + `state` — and without the compliance module the
URL fallback fills `property_name` only. So `SERP_API_PATH` alone prints
`[GMB] Missing property name/city/state` / `[COMPETITOR] Missing city/state`
and skips. That is expected gating, not a bug.

Public modules that satisfy the SERP hook: the
[`rsa-single-account`](../../rsa-single-account/) skill ships
`get_gmb_reviews.py` (exposing `get_apartment_social_proof`) and
`analyze_competitors_for_rsa.py` plus `vertical_configs.json` with a
`property_management` vertical — the exact functions this hook imports.
Point `SERP_API_PATH` at that skill's `scripts/` directory (needs
`SERP_API_KEY`).

## Validation statuses (Refreshed tab)

| Value | Meaning |
|---|---|
| `N/A` | No compliance module loaded (the default public configuration) |
| `SKIPPED` | `--skip-validation` passed |
| `VALID` / `N ERRORS` | Module ran; errors listed in `Validation Errors` |

`--strict` with any geographic error **blocks the sheet write entirely**.

## In-script filter helpers — status

The script defines `HALLUCINATION_PATTERNS`, `is_unverified_copy`,
`filter_hallucinated_headlines`, `generate_keyword_headlines`,
`generate_brand_headline`, and `has_cta`, but **the shipped three-stage flow
never calls them** — they are import-available scaffolding and an executable
statement of the headline taxonomy. Copy quality is enforced at Stage 2 by
the agent following the reference files (which the context JSON embeds),
not by mechanical stripping at Stage 3. The only mechanical gates on copy
are the ones listed in the merge section: 30/90 length, dedupe, the 15/4
caps, and the <10 skip.

## Sheet contract

Sheets auth: `token-sheets.json` if present, else the OAuth credentials in
`google-ads.yaml` (needs the `spreadsheets` scope). Both paths overridable
(`--sheets-token`, `--config`).

Two tabs, created if missing:

**`Original RSAs`** — columns in order: Account Name, Customer ID (dashed),
Campaign, Ad Group, Ad ID, then Headline 1 … Headline 15 **each followed by
its own `H{n} Performance` column** (30 columns interleaved), then
Description 1–4, Path 1, Path 2, Final URL. 42 columns total.

**`Refreshed RSAs`** (Google Ads Editor-ready) — columns in order: Account
Name, Customer ID (dashed), Campaign, Ad Group, Headline 1–15,
Description 1–4, Path 1, Path 2, Final URL, Ad ID, Validation Status,
Validation Errors, Changes Made. 30 columns total.

Write mode:

- **Default is APPEND** — data rows are added below whatever the tab holds;
  the header row is only written when the tab is new or empty. Re-running
  the same account without `--clear` stacks old and new rows.
- `--clear` wipes both tabs and rewrites header + data.
- Skipped ads (<10 headlines) appear in **neither** tab.
- **Neither tab carries a run timestamp.** Append mode is how multi-account
  batches accumulate into one sheet; dating individual runs is on you
  (see "Reading run state cold").

## Baseline contract (`rsa_baseline_snapshot.py`)

Four GAQL statements: keyword `quality_info` + impressions (LAST_30_DAYS,
enabled keyword/ad group/campaign), RSA ad-level impressions/clicks/
conversions (LAST_30_DAYS), RSA ad strength (no date segment — it's an
attribute), and campaign impression-share metrics (Search + Performance
Max, LAST_30_DAYS, impression-weighted).

- **IWQS** = impression-weighted average Quality Score over keywords with
  impressions > 0 and a real QS. Rating: `< 5` NEEDS WORK, `< 7` AVERAGE,
  else HEALTHY; no scored keywords → `0.0` + `NO DATA`.
- QS component splits are impression-weighted percentages; an empty bucket
  renders `N/A`.
- Each query failure is **non-fatal**: a console warning and `N/A` cells in
  the row. An all-`N/A` row means the queries failed (access, wrong CID) —
  not an empty account.
- **Asset label counts come from the generator's performance data.** A
  **standalone** run has none and writes `0` in all four Assets columns —
  a mode artifact, not "no labeled assets." Only the integrated capture
  (Stage 1 with `--baseline-sheet-id`) fills them. `PENDING` is counted
  internally but has no column.
- Output: one row appended to an **`RSA Baseline`** tab (created with
  headers if missing), 33 columns `A:AG`, including Capture Date and
  Capture Time — the only timestamps this skill writes anywhere.

Invocation: standalone CLI (`--cid --account-name --sheet-id`), or
automatically in Stage 1 via `--baseline-sheet-id` (skipped on `--copy-file`
resume — the baseline belongs to *before*). A baseline failure warns and
the refresh continues.

## Reading run state cold

From the filesystem and sheet alone:

- `rsa_context_{cid}.json` exists → Stage 1 ran (file mtime = when).
  `copy_{cid}.json` exists → Stage 2 ran. Both are runtime artifacts in the
  working directory — never part of the skill folder.
- The `RSA Baseline` tab is the only dated log: one row per capture.
- `Original RSAs` / `Refreshed RSAs` rows accumulate undated under the
  append default. If tab contents must identify their run, use `--clear`
  per re-run (single account) or pair the run with a baseline capture.
- Skipped ad groups exist **only** in the run's console output — a cold
  session cannot recover them from the sheet.
