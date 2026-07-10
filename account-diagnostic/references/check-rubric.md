# Check Rubric — all 44 checks, exact criteria

Per-check verdict criteria for the 42-point diagnostic (44 with the
local-service preset). Use this to answer "why did check N fire?" without
reading the engine.

> **Source of truth:** `scripts/run_diagnostic.py`. This document mirrors its
> thresholds as of the 2026-07-10 revision. If you change a check in the
> script, update the matching row here and add a CHANGELOG entry.

Where the two vertical presets differ, thresholds are shown as
**PM** (`property-management`) / **LS** (`local-service`). A check that can't
be evaluated (no data, no campaigns of that type) reports **N/A** and never
counts against the score.

---

## Conversion Tracking (1-3)

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 1 | Primary conversion actions exist | ≥1 primary action | Actions exist, none marked primary | No conversion actions at all — **auto-red** |
| 2 | Primary actions firing recently | Every primary fired within 14 days | Worst primary 15–30 days silent | Any primary >30 days silent (never-fired in the 90-day window counts as 90) |
| 3 | No orphaned/duplicate actions | No duplicate action names | Duplicate names found | — (never RED) |

Notes: store-visit and app-install conversion types are ignored. Check 2 looks
back 90 days regardless of `--days`, and deliberately does NOT filter to
enabled campaigns — tag health is account-level (a paused campaign shouldn't
make its conversion action look dead).

## Budget & Pacing (4-6)

| # | Check | GREEN | YELLOW | RED | $ impact |
|---|-------|-------|--------|-----|----------|
| 4 | Account is spending | Budget set and MTD spend > $0 | — | Budget set, $0 MTD spend — **auto-red** | daily budget × 30 |
| 5 | MTD pacing within tolerance | \|variance\| ≤ **8% PM / 10% LS** | \|variance\| ≤ 15% | \|variance\| > 15% | variance % × monthly budget |
| 6 | Projected EOM spend on target | Projection 90–110% of budget | 80–90% or 110–120% | Outside 80–120% | \|projection − budget\| |

Notes: "monthly budget" is **estimated** as the sum of enabled campaigns'
daily budgets × days in month — if the contracted budget differs, pacing
variance is partly an artifact (see the false-alarm table in `rules.md`).
Variance = (expected-to-date − actual MTD) / expected; positive = underspent.
`--pacing-threshold` overrides the preset tolerance. N/A on day 1 of the month.

## Impression Share (7-9) — Search campaigns only, spend-weighted

| # | Check | GREEN | YELLOW | RED | $ impact |
|---|-------|-------|--------|-----|----------|
| 7 | Search IS adequate | >60% | 31–60% | ≤30% | — |
| 8 | Budget Lost IS controlled | <10% | 10–24% | ≥25% | lookback spend × Budget-Lost-IS % |
| 9 | Rank Lost IS manageable | <40% | 40–59% | ≥60% | — |

## Quality Score (10-11) — keywords with QS data

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 10 | Average QS healthy | ≥6.0 | 4.0–5.9 | <4.0 |
| 11 | Low-QS concentration acceptable | <15% of keywords below QS 5 | 15–29% | ≥30% |

## Search Terms (12-13) — lookback window, enabled campaigns

| # | Check | GREEN | YELLOW | RED | $ impact |
|---|-------|-------|--------|-----|----------|
| 12 | Zero-conv search term waste controlled | <5% of spend | 5–14% | ≥15% | total zero-conversion spend |
| 13 | No high-spend zero-conv terms | 0 terms over the floor | 1–2 terms | 3+ terms | summed spend of flagged terms |

Floor per term: **$100 PM / $50 LS** (preset knob `st_high_spend_floor`).

## Keyword Health (14-16)

| # | Check | GREEN | YELLOW | RED | $ impact |
|---|-------|-------|--------|-----|----------|
| 14 | Keywords are serving | >90% with impressions | 76–90% | ≤75% | — |
| 15 | No high-spend zero-conv keywords | 0 keywords over the floor | 1–2 | 3+ | summed spend of flagged keywords |
| 16 | Match type distribution intentional | Broad <50%, or any broad share with ≥10 campaign negatives | 50–79% broad with <10 negatives | ≥80% broad with <10 negatives | — |

Floor per keyword: **$200 PM / $100 LS** (preset knob `kw_high_spend_floor`).

## Creative & Ads (17-22) — enabled ads in enabled ad groups/campaigns

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 17 | No disapproved ads | 0 | 1–2 | 3+ (**auto-red** if >75% of all enabled ads) |
| 18 | No DKI in use | No `{KeyWord:...}` insertion in RSA copy | — | Any DKI found (trademark risk) |
| 19 | Auto-created assets disabled | Text asset automation OFF on all non-PMAX campaigns | — | ON anywhere (Google default is ON) |
| 20 | Destination URLs valid | Every ad has a final URL | 1–2 ads missing URLs | 3+ ads missing URLs |
| 21 | No outdated seasonal copy | No seasonal/holiday/stale-year patterns in RSA copy | *(LS verdict)* | *(PM verdict)* — preset knob `seasonal_severity` |
| 22 | Auto-applied recommendations disabled | None enabled (ad-rotation type is exempt) | Non-high-risk types enabled | Any high-risk type: bids, keywords, broad match, RSAs |

## RSA Assets (23-25) — headline/description assets, lookback window

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 23 | Assets have performance data | >75% labeled (past LEARNING) | 51–75% | ≤50% |
| 24 | LOW-rated assets controlled | <15% LOW | 15–29% | ≥30% |
| 25 | BEST-rated assets exist | BEST in headlines AND descriptions | BEST in one of the two | No BEST anywhere |

## Account Settings (26-29)

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 26 | Location targeting set correctly | All campaigns PRESENCE | — | Any campaign PRESENCE_OR_INTEREST |
| 27 | Content suitability configured | LIMITED or STANDARD inventory | Any other value | EXPANDED_INVENTORY |
| 28 | Auto-applied recommendations off | No non-exempt subscription enabled | — | Any enabled |
| 29 | Geographic exclusions present | ≥1 negative location anywhere | *(LS verdict)* | *(PM verdict)* — preset knob `geo_exclusion_severity` |

Note: 22 and 28 read the same subscription data; 28 is the stricter
account-level pass (any non-exempt type → RED), 22 grades by risk tier.

## PMAX Config (30-34) — N/A if no PMAX campaigns

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 30 | Text asset automation disabled | OFF on all PMAX campaigns | — | ON anywhere (default ON) |
| 31 | Image asset automation disabled | Extraction AND enhancement OFF everywhere | — | Either ON anywhere |
| 32 | Final URL expansion disabled | OFF on all PMAX campaigns | — | ON anywhere (default ON) |
| 33 | Search themes present | Asset groups exist (verify themes in UI — API can't read them) | — | No asset groups |
| 34 | Audience signals present | Asset groups exist (verify signals in UI) | — | No asset groups |

## Negative Keywords (35-36) — Search campaigns

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 35 | Adequate negative coverage | Avg ≥ **20 PM / 10 LS** campaign-level negatives per Search campaign | Avg ≥ **10 PM / 5 LS** | Below the yellow bar |
| 36 | No negative keyword conflicts | 0 exact-text collisions with active keywords | 1–3 | 4+ |

Note: check 35 counts **campaign-level** negatives only — shared-list
negatives don't register here. An account run entirely on shared lists can
show a false RED; verify before acting (see `rules.md`).

## Placement Safety (37-38) — lookback placements

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 37 | No suspicious placements | 0 flagged website placements (spammy TLDs / spam name patterns) | 1–5 | 6+ |
| 38 | No brand-unsafe placements | 0 flagged YouTube placements (kids/adult/gambling patterns) | 1–3 | 4+ |

## Extensions (39-40) — account-level assets

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 39 | Core extensions present | ≥4 sitelinks AND ≥4 callouts | One of the two | Neither |
| 40 | Supplemental extensions present | ≥1 structured snippet AND ≥1 image | One of the two | Neither |

Note: counts come from customer-level (account) assets. Campaign-level-only
extension setups can undercount here — verify placement before acting.

## Local Service (41-42) — local-service preset only

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 41 | Call extensions present | ≥1 CALL asset link serving (campaign or account level) | — | None — critical for phone-driven businesses |
| 42 | Location extensions present | ≥1 LOCATION asset link serving | None detected — verify Business Profile linkage | — (soft by design: GBP-sourced links can hide from the scan) |

## Video & DGen Automation (43-44) — all verticals

| # | Check | GREEN | YELLOW | RED |
|---|-------|-------|--------|-----|
| 43 | PMAX video enhancements disabled | `GENERATE_ENHANCED_YOUTUBE_VIDEOS` OFF on all PMAX campaigns | — | ON anywhere (default ON when unset) |
| 44 | DGen ad-level automation disabled | All 5 ad-level settings OFF across every multi-asset / video-responsive Demand Gen ad | — | Any setting ON on any ad |

Check 44 exists because Demand Gen automation lives on the **ad**
(`ad_group_ad.ad_group_ad_asset_automation_settings`), not the campaign —
campaign-scoped audits structurally can't see it. Settings inspected: design
versions for images, generate-videos-from-assets, vertical videos, shorter
videos, landing-page preview. All default **ON** except landing-page preview.
Carousel and product ads carry no automation settings and are skipped;
ended-but-enabled campaigns are excluded.

---

## Scoring

- **Auto-red circuit breakers** (any one forces overall RED): check 1 with no
  conversion actions, check 4 with budget-but-zero-spend, check 17 with >75%
  of ads disapproved.
- **Overall RED:** any auto-red, or 3+ RED checks.
- **Overall YELLOW:** 1–2 RED, or 6+ YELLOW.
- **Overall GREEN:** everything else.
- **Estimated waste/mo** = sum of all dollar impacts. Checks 5 and 6 measure
  the same pacing gap two ways, and search-term waste (12–13) overlaps keyword
  waste (15) — read the total as a **ceiling**, not a precise loss figure.

---

## Preset knobs

The engine is vertical-agnostic; these eight values are what a preset sets.
`--pacing-threshold` is the only CLI override — for anything else, add your
own preset to `VERTICAL_PRESETS` in the script (copy a block, tune, run with
`--vertical your-preset`).

| Knob | property-management | local-service | Governs |
|------|--------------------:|--------------:|---------|
| `pacing_threshold` | 8 | 10 | Check 5 tolerance (±%) |
| `seasonal_severity` | RED | YELLOW | Check 21 verdict when seasonal copy found |
| `geo_exclusion_severity` | RED | YELLOW | Check 29 verdict when zero exclusions |
| `neg_green_bar` | 20 | 10 | Check 35 GREEN threshold (avg negatives/campaign) |
| `neg_yellow_bar` | 10 | 5 | Check 35 YELLOW threshold |
| `st_high_spend_floor` | $100 | $50 | Check 13 per-term spend floor |
| `kw_high_spend_floor` | $200 | $100 | Check 15 per-keyword spend floor |
| `check_call_location_ext` | off | on | Whether checks 41-42 run |

Picking between the two shipped presets: strict-pacing lead-gen portfolios →
`property-management`; phone-driven local businesses → `local-service`.
Neither fits? Start from `property-management` and loosen — its defaults are
the conservative ones.
