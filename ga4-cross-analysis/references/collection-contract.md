# Collection Contract — shipped script mechanics + the four you-implement contracts

> **Source of truth:** `scripts/query_campaign_settings.py` is the authority for everything
> claimed about the shipped script below — line references point into it. The four
> you-implement contracts and the JSON source map are normative for this skill's protocol:
> if the script's behavior changes, update this file and the CHANGELOG in the same commit.

One script ships in this skill; four collection scripts are yours to implement. This file
owns the exact mechanics of the shipped script (what it prints, what it can't, how it
fails), the contract each you-implement script must satisfy, and the field-by-field source
map for the Step 4 JSON in SKILL.md.

---

## Shipped: `scripts/query_campaign_settings.py`

```bash
python scripts/query_campaign_settings.py <customer_id> "<campaign_name>"
```

### Invocation and credentials

- Credentials load from the literal filename `google-ads.yaml` (`:279`) — **working-directory
  relative, no fallback probe**. Run the command from a directory containing your yaml, or it
  fails with a raw `FileNotFoundError` traceback (the load happens outside the script's
  `try` block). Querying client accounts through a manager requires `login_customer_id` in
  the yaml.
- The customer ID is dash-stripped (`:276`) — `123-456-7890` and `1234567890` both work.
- The campaign name is matched **exactly and case-sensitively** (`WHERE campaign.name =`,
  `:55`), with **no status filter** — `REMOVED` and `PAUSED` campaigns match too.

### Match edge cases

- **Duplicate names:** Google allows a removed campaign to share a name with a live one.
  Every matching row prints its own `BASIC SETTINGS` block; the follow-up sections
  (geo, URL expansion, devices, networks) run against **the last match's campaign ID**
  (`:61-64`). Two `BASIC SETTINGS` blocks in one output = a removed twin exists.
- **Apostrophes:** the name is embedded in a single-quoted GAQL string (`:55`). A campaign
  name containing `'` breaks the query and exits as an API error. Rename-free workaround:
  none in this script — pull that campaign's settings via `google-ads-query` or the UI.

### Exit codes (status surface)

| Outcome | Console | Exit code |
|---|---|---|
| Campaign found | Full sections, ends `CAMPAIGN SETTINGS QUERY COMPLETE` | 0 |
| Campaign not found | Header block, then `ERROR: Campaign '<name>' not found` (`:90-92`) | **0** — a wrapper checking exit codes reads this as success |
| Google Ads API error (bad CID, permissions, broken GAQL — incl. an apostrophe in the name) | `Google Ads API Error: …` + per-error lines (`:260-264`) | 1 |
| Missing arguments | Usage text (`:268-274`) | 1 |
| `google-ads.yaml` missing, or token refresh fails | Raw Python traceback (outside the script's error handling) | 1 |

The script writes **nothing to disk** — console is the only output surface.

### What each section prints — and what it cannot

- **BASIC SETTINGS** — status, channel type (subtype only when set), daily budget from
  micros, bid strategy type. A target detail line prints for **exactly three strategy
  types**: `TARGET_CPA`, `TARGET_ROAS`, and `MAXIMIZE_CONVERSION_VALUE` (which prints
  `Target ROAS: Not set (maximize without constraint)` when uncapped) (`:76-86`). Every
  other strategy — `MAXIMIZE_CONVERSIONS` included — gets a type line with no target
  detail. The three branches read **campaign-level** target fields only: a campaign
  attached to a portfolio bid strategy shows the type with no target, because the target
  lives on the portfolio resource this script never queries.
- **GEOGRAPHIC TARGETING** — targeted, proximity, and excluded locations. Locations print
  as **numeric geo target IDs, never names** (`:129`), capped at the **first 10** per list
  (`:128`, `:138`). Proximity (radius) targets print only a count plus
  `Proximity targeting detected` — **the radius value is never printed** (`:132-134`).
  `No location targeting found (targeting all locations)` prints whenever there are no
  positive locations and no proximities — **including when excluded locations exist**
  (`:142-143`); read that combination as "all locations minus the exclusions."
  `negative_geo_target_type` is selected by the query (`:152`) but never printed.
- **LOCATION TARGETING TYPE** — translates `PRESENCE` and `AREA_OF_INTEREST` into plain
  language (`:163-170`). When the setting is unset the header prints with no type line.
- **URL EXPANSION** — one of two lines from `url_expansion_opt_out` (`:186-189`). The
  field is a **Performance Max setting**; for any non-PMax campaign it holds the proto
  default and the line always reads `URL Expansion: Enabled…` — meaningless there. The
  hardcoded note (`:191-192`) is load-bearing: **specific URL exclusion rules are not
  retrievable by this script** — they come from the UI (Campaign Settings → URL exclusions).
- **DEVICE TARGETING** — per-device bid adjustments computed as `(modifier − 1) × 100`.
  A modifier of `0.0` — which is also how the API represents a full device opt-out — is
  falsy and falls back to `1.0` (`:215`), so **an excluded device prints
  `No bid adjustment`**. Verify suspected device exclusions in the UI.
- **NETWORK SETTINGS** — four raw booleans (`True`/`False`), printed in the order
  Google Search, Search Partners, Display Network, Search Network (`:250-253`).

---

## You implement (contract per script)

These four are environment-specific — they depend on your GA4 property ID, event names,
dimensions, and where your credentials and registries live — so they're documented as
contracts rather than shipped as generic scripts:

1. **`query_campaign_performance.py`** — given a customer ID and campaign name, return
   campaign spend, conversions, conversion value, and ROAS for the date range. The
   [google-ads-query](../../google-ads-query/) skill ships a campaign-performance GAQL
   template that satisfies this contract as-is.
2. **`query_ga4_campaign_conversions.py`** — given a GA4 property ID, campaign name, and
   event name, return the conversion summary: total conversions, total users,
   conversion rate.
3. **`query_ga4_user_segments.py`** — given the same inputs, return user segments:
   cities, devices, browsers, hourly distribution.
4. **`query_ga4_landing_pages.py`** — given the same inputs, return landing pages with
   conversion counts, users, and a high-intent vs low-intent categorization.

### GA4-side implementation notes

1. Install `google-analytics-data` (`pip install google-analytics-data`).
2. Reuse the same OAuth client as the Google Ads API — but note that **scopes are fixed
   when a refresh token is minted; you cannot add a scope to an existing token.** Add
   `https://www.googleapis.com/auth/analytics.readonly` to the `SCOPES` list in the
   [google-ads-api-setup](../../google-ads-api-setup/) skill's `generate_credentials.py`,
   re-run the consent flow once, and paste the **new** refresh token into your
   `google-ads.yaml`. The re-minted token covers Ads + Sheets + Drive-read + GA4-read in
   one credential. (A GA4 service-account JSON works too, if you'd rather keep the
   credentials separate.)
3. Query the GA4 Data API (`runReport`) for:
   - `landing_pages`: dimensions `[sessionDefaultChannelGrouping, landingPage]`,
     metrics `[conversions, sessions, totalUsers]`, filter on the Google Ads campaign
     as source/medium or session campaign ID.
   - `user_segments`: dimensions like `[city, deviceCategory, browser, hour]`,
     metrics `[conversions, totalUsers]`, filter on your event of interest.
   - `conversion_summary`: metrics `[conversions, totalUsers, sessions]` filtered to the
     specific event name (e.g. `contact_form_submission`).

GA4 Data API reference: https://developers.google.com/analytics/devguides/reporting/data/v1

---

## Step 4 JSON — field source map

The output shape lives in SKILL.md § Step 4 (one home; not restated here). This table says
where each field's **value** legitimately comes from. A field with no legitimate source in
your environment stays out of the JSON or ships as `null` with a note — never invented.

| Field | Source |
|---|---|
| `metadata.*` | Operator/agent — inputs plus the run date |
| `google_ads.campaign_performance.*` | Your `query_campaign_performance.py` (or the google-ads-query template) |
| `campaign_settings.bid_strategy`, `budget_daily` | Shipped script — BASIC SETTINGS block |
| `campaign_settings.geo_targeting.type` | Shipped script — LOCATION TARGETING TYPE block |
| `campaign_settings.geo_targeting.locations` | Shipped script prints **IDs only** — names need a geo-target-constant lookup (yours) or the UI |
| `campaign_settings.geo_targeting.radius_miles` | **Not in the shipped output** — UI, or your own proximity query |
| `campaign_settings.url_exclusions` | **UI only** — the script cannot retrieve URL exclusion rules |
| `ga4.conversion_summary` | Your `query_ga4_campaign_conversions.py` |
| `ga4.landing_pages` | Your `query_ga4_landing_pages.py` |
| `ga4.user_segments.*` | Your `query_ga4_user_segments.py` |

---

## After a run

Nothing lands in this skill's folder. The shipped script is console-only; the assembled
JSON exists where the agent puts it — returned in-chat by default, or written to a file
only when the operator asks. If you need a durable record of what was collected, save the
JSON alongside the investigation it feeds (its `metadata.analysis_date` and
`metadata.date_range` make it self-describing later).
