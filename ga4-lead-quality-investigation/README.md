# GA4 Lead Quality Investigation

Diagnose why a Google Ads campaign is generating low-quality leads (no-shows, missing phone numbers, bot traffic, geographic mismatches) by cross-analyzing GA4 behavioral data with Google Ads campaign settings, then produce prioritized recommendations grounded in evidence.

**The pain point:** "Our leads are no-shows" and "we keep getting fake phone numbers" are recurring complaints in lead-gen PPC. The wrong answer ("add more negative keywords") fails when the actual cause is IP geolocation drift, in-app browser placements, or a missing URL exclusion that lets blog traffic convert. This skill encodes the diagnostic discipline — five red-flag frameworks applied against structured GA4 data, then hypothesis-driven cross-reference against actual campaign settings — so every recommendation traces to a specific data point AND a verified gap in current configuration. Recommendations that are "already implemented" get filtered out before they reach the client.

---

## What's Inside

- Auto-loaded 5-companion-skill stack (data collection → pattern detection → cross-reference → prioritization → reporting)
- 5 red-flag detection frameworks (landing pages, geography, devices/browsers, time patterns, user behavior) with quantitative severity thresholds
- Hypothesis → Verification → Finding methodology that prevents recommending fixes already in place
- 3-tier prioritization (Immediate / Medium / Long-term) with structured recommendation templates
- Mandatory "What Was Ruled Out" section so the report shows both what to fix AND what was checked-and-cleared
- Background → Analysis → Conclusions client report framework with "What We Looked At" attribution on every finding
- Adaptive investigation — stop early if data is insufficient, pivot if patterns suggest a different path
- Read-only — never writes to Google Ads

---

## Installation

```bash
mkdir -p .claude/skills/ga4-lead-quality-investigation
curl -o .claude/skills/ga4-lead-quality-investigation/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ga4-lead-quality-investigation/SKILL.md
curl -o .claude/skills/ga4-lead-quality-investigation/README.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ga4-lead-quality-investigation/README.md
```

Then install the 5 companion skills (also in this repo):

```bash
for skill in ga4-cross-analysis lead-quality-pattern-analysis \
             ga4-campaign-cross-reference lead-quality-recommendation-prioritization \
             client-communication-standards; do
  mkdir -p .claude/skills/$skill
  curl -o .claude/skills/$skill/SKILL.md \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/$skill/SKILL.md
done
```

---

## Script Dependency (You Provide)

This skill calls two classes of script under `scripts/` that you implement against your own data sources. The scripts are environment-specific — they live where your Google Ads credentials, GA4 service account, account registry, and property registry live. The SKILL.md documents the data contract each script must satisfy.

**Required scripts:**

1. **`query_campaign_settings.py`** — given a customer ID and campaign name, returns full campaign configuration:
   - Geographic targeting (locations, radius, presence vs interest)
   - URL exclusions (content exclusions)
   - Bidding strategy and targets
   - Audience signals (for PMAX)
   - Placement exclusions
   - Ad scheduling (day parting)
   - Negative keyword lists attached

2. **GA4 query scripts** — given a GA4 property ID, campaign name, conversion event name, and date range, return:
   - Conversion summary (total conversions, total users, conversion rate)
   - Landing pages with conversion counts and categorization (high-intent vs low-intent)
   - User segments (cities, devices, browsers, hourly distribution)
   - User behavior metrics (new vs returning, session duration, pages per session)

**Reference implementation hooks:**

- Google Ads API via `google-ads-python` (loads credentials from `google-ads.yaml`)
- GA4 Data API via `google-analytics-data` (service account JSON)
- Account registry for customer ID lookups (your `accounts.json` or equivalent)
- GA4 property registry for property ID lookups (your `ga4_properties.json` or equivalent)

A working reference implementation lives in the private brain this skill was extracted from; if you'd like a starter template to adapt, open an issue.

---

## Usage

**Inline (single campaign, manual):**

> "Use the ga4-lead-quality-investigation skill to investigate Customer ID 1234567890, campaign 'Example Property - Pmax', GA4 property 123456789, event 'book_tour'. Issue: leads are no-shows."

The skill will:

1. Auto-load the 5 companion skills via the Skill tool
2. Run the GA4 + Google Ads data collection (via `ga4-cross-analysis` companion skill)
3. Apply all 5 red-flag detection frameworks
4. Run `query_campaign_settings.py` to capture current configuration
5. Cross-reference GA4 patterns against campaign settings using Hypothesis → Verification → Finding methodology
6. Produce a Background → Analysis → Conclusions report with prioritized recommendations + a "What Was Ruled Out" section

**Parallel (when investigating multiple campaigns at once):**

```
Task(subagent_type="general-purpose",
     description="Investigate Campaign A lead quality",
     prompt="Use the ga4-lead-quality-investigation skill to investigate Customer ID 1234567890, campaign 'Campaign A', GA4 property 123456789, event 'book_tour'. Issue: high no-show rate.")

Task(subagent_type="general-purpose",
     description="Investigate Campaign B lead quality",
     prompt="Use the ga4-lead-quality-investigation skill to investigate Customer ID 1234567890, campaign 'Campaign B', GA4 property 123456789, event 'book_tour'. Issue: missing phone numbers.")

# ...launched in a single message for parallel execution
```

Each parallel investigation runs in an isolated context, so per-campaign findings don't bleed into each other.

---

## Output Example (Truncated)

```markdown
# Example Property - Pmax — GA4 Lead Quality Analysis & Recommendations

**Date:** 2026-05-28
**Campaign:** Example Property - Pmax
**Customer ID:** 1234567890
**GA4 Property:** 123456789
**Analysis Period:** 2026-05-14 to 2026-05-28

---

## Background

The client reports a rising rate of no-show tour bookings — leads schedule
appointments but never arrive. Initial hypothesis: bot traffic or geographic
mismatch causing low-intent conversions.

We analyzed 84 GA4 conversion events against current campaign configuration to
identify which red flags are real (and not already mitigated).

---

## Analysis

### Pattern Analysis Findings (5 Frameworks)

**What We Looked At:** Output of ga4-cross-analysis companion skill, 84 conversions
over 14 days.

**Red Flags Detected:** 4 of 5 frameworks flagged red

#### Framework 1: Landing Page Distribution (84 conversions)

| Category | Conversions | % of Total | Top Examples |
|----------|-------------|------------|--------------|
| Blog/Community | 64 | 76.2% | /community/10-tips, /blog/moving-guide |
| Property Pages | 15 | 17.9% | /floor-plans/2br, /apartments/studio |
| Other | 5 | 5.9% | /amenities, /contact |

**Red Flag Assessment:** Severe — 76% from low-intent pages exceeds 75% threshold
**Finding:** Blog content is dominating conversions; users discover the property
via informational pages, not high-intent search.

#### Framework 3: Device & Browser Analysis

| Device/Browser | Conversions | % | Bot Indicator? |
|----------------|-------------|---|----------------|
| Android Webview | 70 | 83.3% | YES |
| Chrome | 14 | 16.7% | No |

**Red Flag Assessment:** Severe — Android Webview dominance is a bot indicator
**Finding:** Conversions are arriving via in-app browsers (often automated
traffic from mobile ad networks).

[... Frameworks 2, 4, 5 ...]

**Severity Classification:** Severe Quality Issues (>3 red flags)

---

### Campaign Settings Verification

**What We Looked At:** Output of `query_campaign_settings.py` for campaign Example Property - Pmax

- **Location Targeting:** 40-mile radius, presence-only
- **URL Exclusions:** None
- **Negative Keywords:** 23 keywords, no app/blog exclusions
- **Placement Exclusions:** None
- **Ad Scheduling:** All hours, all days

---

### Cross-Reference Analysis

#### Hypothesis 1: Missing URL Exclusions Drive Blog Conversions

**GA4 Data Suggests:** 76% of conversions originate on `/community/*` and `/blog/*`
**Campaign Settings Show:** No URL exclusions configured
**Verification:** Reviewed campaign URL Exclusions section — empty
**Finding:** GAP TO FIX — adding URL exclusions will redirect Pmax bidding to property pages
**Evidence:** Settings query confirms empty URL exclusion list

#### Hypothesis 2: Missing Mobile App Placement Exclusions

**GA4 Data Suggests:** 83% Android Webview indicates in-app traffic
**Campaign Settings Show:** No placement exclusions
**Verification:** Reviewed campaign Placement Exclusions section — empty
**Finding:** GAP TO FIX — exclude mobileappcategory::69500 (all mobile apps)
**Evidence:** Settings query confirms no placement exclusions

---

### What Was Ruled Out

#### Geographic Targeting Misconfiguration

**Initial Hypothesis:** Conversions from outside target geo suggest broken radius targeting
**Verification Method:** Cross-referenced GA4 city data against campaign location targeting
**Finding:** Already implemented — 40-mile radius is configured correctly. The
out-of-area conversions in GA4 are consistent with mobile IP geolocation
inaccuracy, not a targeting bug.
**Evidence:** Campaign settings show correct 40-mile radius; GA4 shows 81% of
conversions still within target metro.

---

## Conclusions

### Root Cause

Two configuration gaps are jointly responsible: missing URL exclusions (allowing
blog content to attract conversions) and missing mobile app placement exclusions
(allowing in-app bot traffic to convert). The geographic anomaly is a data
artifact, not a configuration issue.

### Comprehensive Recommendations

#### IMMEDIATE ACTIONS (Implement Today)

##### 1. Add URL Exclusions for Blog/Community Content

- **Current State:** No URL exclusions configured
- **Recommendation:** Add `/community/*`, `/blog/*`, `/news/*` to campaign URL exclusions
- **Implementation Steps:**
  1. Open campaign → Settings → URL exclusions
  2. Add 3 patterns above
- **Expected Impact:** ~75% reduction in low-intent blog conversions

##### 2. Exclude Mobile App Placements

- **Current State:** No placement exclusions
- **Recommendation:** Exclude `mobileappcategory::69500` (all mobile apps)
- **Implementation Steps:**
  1. Open campaign → Content → Exclusions → Placements
  2. Add placement exclusion via shared library
- **Expected Impact:** Eliminate Android Webview bot traffic (~83% of current conversions)

[... Medium-Term and Long-Term sections ...]

### Implementation Timeline

| Week | Actions | Priority | Owner | Status |
|------|---------|----------|-------|--------|
| Week 1 | URL + placement exclusions | High | Account Manager | Pending |
| Week 2-3 | Audience signal additions | Medium | Account Manager | Pending |
| Week 4+ | Offline conversion tracking | Low | Account Manager + Dev | Pending |

### Success Metrics & Monitoring

**Primary KPIs:**

1. No-show rate — Current: ~70% — Target: <20%
2. Conversions from `/community/*` — Current: 76% — Target: <10%
3. Android Webview share — Current: 83% — Target: <15%

**Monitoring Frequency:** Weekly
**Review Date:** 2026-06-11

**Confidence Level:** High (verified evidence on every recommendation)
```

---

## Companion Skills

This skill auto-loads 5 companion skills via the Skill tool. All are in this repo:

- `ga4-cross-analysis` — Data collection
- `lead-quality-pattern-analysis` — 5 red-flag frameworks
- `ga4-campaign-cross-reference` — Hypothesis-driven verification
- `lead-quality-recommendation-prioritization` — 3-tier priority system
- `client-communication-standards` — Report formatting

The investigation will not work correctly without these; the analytical frameworks live inside them.

---

## License

MIT — use freely in your own brain / repo / agency.
