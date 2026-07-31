# Worked Examples — GA4 Cross-Analysis

Three collection reads. All names, IDs, and figures are synthetic; console output follows
the shipped script's exact print format. The judgment rules live in
[`rules.md`](rules.md); script mechanics in
[`references/collection-contract.md`](references/collection-contract.md).

---

## Example 1 — Full collection: the targeting-type line changes the whole story

**Ask:** "Run GA4 cross-analysis for Acme Plumbing's PMax — leads have been weak."
Inputs: CID `1234567890`, campaign `Pmax: Plumbing Leads`, GA4 property `123456789`,
event `contact_form_submission`, last 14 days.

**Settings side (shipped script):**

```
====================================================================================================
CAMPAIGN SETTINGS: Pmax: Plumbing Leads
====================================================================================================
Customer ID: 1234567890
Campaign: Pmax: Plumbing Leads

BASIC SETTINGS
====================================================================================================
Campaign ID: 22334455667
Status: ENABLED
Type: PERFORMANCE_MAX
Budget: $250.00
Bid Strategy: MAXIMIZE_CONVERSION_VALUE
  Target ROAS: Not set (maximize without constraint)

GEOGRAPHIC TARGETING
====================================================================================================
Targeted Locations: 1 location(s)
  - Geo Target ID: 1023191

LOCATION TARGETING TYPE
====================================================================================================
Presence or Interest: People in, regularly in, OR interested in your targeted locations

URL EXPANSION
====================================================================================================
URL Expansion: Enabled (Google may expand to similar URLs)

Note: Specific URL exclusion rules not accessible via API
Manual check required in Google Ads UI: Campaign Settings -> URL exclusions

DEVICE TARGETING
====================================================================================================
No device bid adjustments configured

NETWORK SETTINGS
====================================================================================================
Google Search: True
Search Partners: False
Display Network: True
Search Network: True

====================================================================================================
CAMPAIGN SETTINGS QUERY COMPLETE
====================================================================================================
```

**The collection reads, before any GA4 data arrives:**

- Geo Target ID `1023191` resolves to New York, NY — the JSON gets the name, sourced
  "geo-constant lookup," not the bare ID.
- The load-bearing line is `Presence or Interest` — this campaign accepts people
  *interested in* New York, not just people in it. Carried into the JSON as
  `"type": "AREA_OF_INTEREST"`.
- `URL Expansion: Enabled` is meaningful here (this IS a PMax campaign), and the note
  means `url_exclusions` can only come from the UI. A UI check finds none configured →
  `"url_exclusions": []`, sourced "UI check 2026-07-31."

**GA4 side (your implemented contract scripts):** conversion summary 84 conversions /
45 users; landing pages led by `/blog/how-to-choose-a-plumber` (25 of 84); cities led by
Phoenix and Fresno; 82 of 84 conversions mobile, browser split 70 Android Webview / 14
Chrome; hourly peak 1–4 AM.

**Assembled output (abridged — full shape in SKILL.md § Step 4):**

```json
{
  "metadata": { "customer_id": "1234567890", "campaign_name": "Pmax: Plumbing Leads",
                "ga4_property_id": "123456789", "event_name": "contact_form_submission",
                "date_range": "last_14_days", "analysis_date": "2026-07-31" },
  "google_ads": {
    "campaign_settings": {
      "geo_targeting": { "type": "AREA_OF_INTEREST", "locations": ["New York, NY (1023191)"] },
      "bid_strategy": "MAXIMIZE_CONVERSION_VALUE", "budget_daily": 250.00,
      "url_exclusions": []
    }
  },
  "ga4": { "conversion_summary": { "total_conversions": 84, "total_users": 45 } }
}
```

**Where this stops:** the dataset now holds two loaded observations — distant cities
under `AREA_OF_INTEREST`, and blog-heavy landing pages with zero URL exclusions. Whether
the first is an IP-geolocation artifact or working-as-configured interest targeting, and
whether the second is the real lead-quality culprit, is
[ga4-campaign-cross-reference](../ga4-campaign-cross-reference/) territory — hand the
JSON over; don't verdict here.

---

## Example 2 — Settings-only verify, and the exit code that lies

**Ask:** "Check if City Dental PMAX has correct geo targeting." No GA4 side needed —
settings-only is still this skill.

First run:

```
====================================================================================================
CAMPAIGN SETTINGS: City Dental - Serach
====================================================================================================
Customer ID: 0987654321
Campaign: City Dental - Serach

ERROR: Campaign 'City Dental - Serach' not found
```

Two reads that prevent a wrong report:

1. **The shell says success.** Not-found prints `ERROR:` and exits 0 — anything keying on
   the exit code (a wrapper, a `&&` chain) sails past it. The console line is the only
   signal.
2. **Matching is exact and case-sensitive** — here it's a typo (`Serach`), but a casing
   difference or a trailing space fails identically. Get the exact name from your
   registry or a campaign-list pull via [google-ads-query](../google-ads-query/) rather
   than retyping from memory. (Names containing an apostrophe can't be queried by this
   script at all — that campaign's settings come from `google-ads-query` or the UI.)

The corrected run returns `PRESENCE` targeting with one location — the verify closes
with a two-line settings summary, no JSON assembly needed for a single-block ask.

---

## Example 3 — The ask that routes past this skill

**Ask:** "Our PMax leads are all no-shows. Figure out why."

That's a verdict request, not a collection request. The honest response names the
boundary and routes: [ga4-lead-quality-investigation](../ga4-lead-quality-investigation/)
owns the full investigation — red-flag frameworks, hypothesis testing, prioritized
recommendations — and auto-loads this skill for its data collection step. Jumping
straight to collection here produces a dataset with no investigation to feed.

**The variant worth doing immediately:** the operator hasn't implemented the GA4-side
scripts yet. Per rules.md § Partial data, run the settings side now and ship the JSON
with the `ga4` object absent and a one-line declaration ("GA4 contract scripts not yet
implemented — behavioral side pending"). The settings verification is real work done
today; the declared gap tells the investigation exactly what's missing — and the
contract's GA4 implementation notes are the build path for closing it.
