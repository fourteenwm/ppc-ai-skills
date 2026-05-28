---
name: ga4-lead-quality-investigation
description: Investigate Google Ads lead quality issues by cross-analyzing GA4 behavioral data with Google Ads campaign settings. Auto-invoke when user says "investigate [account] lead quality", "GA4 analysis for [campaign]", "why are [account] leads low quality", or mentions no-shows, missing phone numbers, or bot traffic. Applies 5 red-flag frameworks, hypothesis-driven cross-reference verification, and 3-tier prioritized recommendations. Read-only — no mutations.
allowed-tools: [Read, Write, Bash, Grep, Glob, Skill]
---

# GA4 Lead Quality Investigation

**Purpose:** Investigate why a Google Ads campaign is generating low-quality leads (no-shows, missing contact info, bot traffic, geographic mismatches) by cross-analyzing GA4 behavioral data with Google Ads campaign settings and producing prioritized recommendations.

**Type:** Read-only investigation skill. Reads GA4 + Google Ads data and writes an analysis document; never writes to Google Ads.

---

## Inputs

The skill expects:

- **`{CUSTOMER_ID}`** — Google Ads customer ID (e.g., `1234567890`)
- **`{CAMPAIGN_NAME}`** — exact campaign name (e.g., `Example Property - Pmax`)
- **`{GA4_PROPERTY}`** — GA4 property ID (e.g., `123456789`)
- **`{CONVERSION_EVENT}`** — GA4 event to analyze (e.g., `book_tour`, `submit_lead_form`)
- **`{ISSUE_DESCRIPTION}`** — what the user is experiencing (e.g., "leads are no-shows", "phone numbers missing")
- **`{DATE_RANGE}`** (optional) — defaults to last 14 days

---

## Auto-Load Domain Knowledge Skills

**CRITICAL:** At the start of every investigation, auto-invoke these companion skills via the Skill tool to load the frameworks, formulas, and templates:

1. `ga4-cross-analysis` — Data collection from GA4 and Google Ads APIs (structured JSON output)
2. `lead-quality-pattern-analysis` — Red flag detection frameworks (5 frameworks: landing pages, geo, devices, time, user behavior)
3. `ga4-campaign-cross-reference` — Hypothesis → Verification → Finding methodology for discrepancy identification
4. `lead-quality-recommendation-prioritization` — 3-tier priority system (Immediate / Medium / Long-term) and recommendation templates
5. `client-communication-standards` — Background → Analysis → Conclusions report formatting with "What We Looked At" attribution

Do this BEFORE collecting any data. All five companion skills are shipped as standalone skills in this repo.

---

## Investigation Protocol

### Step 1: Data Collection

**Reference skill:** `ga4-cross-analysis`

Auto-invoke the `ga4-cross-analysis` companion skill to collect:

- **Google Ads side:** campaign performance + campaign settings (geo targeting, bid strategy, URL exclusions, negative keywords, audience signals, placement exclusions, ad scheduling)
- **GA4 side:** conversion summary, landing pages, user segments (cities, devices, browsers, hourly distribution), engagement metrics

The companion skill returns structured JSON. Document:

- Data collection timestamp
- Date range analyzed
- Any data quality warnings (e.g., low conversion volume, missing events)

> **Implementation note:** The underlying data collection scripts are environment-specific — they call the Google Ads API and GA4 Data API against your accounts and properties. The `ga4-cross-analysis` companion skill documents the data contract; you adapt the scripts to your own infrastructure (credentials, customer IDs, GA4 property IDs).

---

### Step 2: Pattern Analysis (5 Frameworks)

**Reference skill:** `lead-quality-pattern-analysis`

Apply all 5 analysis frameworks from the companion skill:

| Framework | Focus | Red Flag Examples |
|---|---|---|
| **1. Landing Page Distribution** | High-intent vs low-intent pages | >50% from blog/informational |
| **2. Geographic Distribution** | Conversion locations vs target market | Conversions outside target geo, VPN indicators |
| **3. Device & Browser Patterns** | Bot indicators | Android Webview >50%, 100% mobile, unusual UAs |
| **4. Time Patterns** | Hourly conversion distribution | 1-4 AM peaks >20%, exact intervals |
| **5. User Behavior** | Engagement metrics | 100% new users, session duration <10s, 1 page/session |

**Severity classification (from companion skill decision tree):**

- **Severe Quality Issues** — >3 red flags detected
- **Moderate Quality Concerns** — 1-2 red flags detected
- **Configuration Issues** — 0 red flags but poor performance

---

### Step 3: Campaign Settings Verification

Run a campaign-settings query against the Google Ads API to capture current configuration:

```bash
python scripts/query_campaign_settings.py {CUSTOMER_ID} "{CAMPAIGN_NAME}"
```

(The script is environment-specific — see "Script Contract" below.)

**Document ALL settings:**

- Location targeting and exclusions (radius, presence vs interest)
- Audience signals
- URL exclusions (content exclusions)
- Negative keywords
- Bidding strategy and targets
- Asset groups and final URLs
- Ad scheduling (day parting)
- Placement exclusions

This becomes the "what is currently configured" baseline for Step 4.

---

### Step 4: Cross-Reference Analysis (Hypothesis → Verification → Finding)

**Reference skill:** `ga4-campaign-cross-reference`

For each red flag from Step 2, apply the companion skill's verification methodology. The core principle is: **never assume GA4 data indicates a settings problem without verification.**

**Verification template (from companion skill):**

```markdown
### Hypothesis: {What GA4 data suggests}

**Verification Method:**
1. Check {specific campaign setting}
2. Review {additional data source}

**Finding:** Already implemented / Not implemented / Partially implemented

**Evidence:** {Specific setting value or data point}

**Conclusion:** {GAP TO FIX / NO ACTION NEEDED / DATA ANOMALY}
```

**Common cross-references (from companion skill):**

1. **Geographic:** GA4 shows wrong cities BUT targeting correct → IP geolocation issue (NOT a targeting fix)
2. **Landing pages:** GA4 shows blog traffic BUT no URL exclusions → configuration gap (FIX)
3. **Devices:** GA4 shows bots BUT no placement exclusions → missing safeguards (FIX)
4. **Time:** GA4 shows 1-4 AM peak BUT no ad scheduling → consider restricting hours
5. **Audience:** GA4 shows low engagement BUT no audience signals → targeting too broad

---

### Step 5: Prioritize Recommendations (3-Tier Framework)

**Reference skill:** `lead-quality-recommendation-prioritization`

Apply the companion skill's 3-tier priority framework:

**IMMEDIATE (Today):**

- Quick wins (<1 hour, no approvals)
- Critical fixes addressing root cause
- Examples: URL exclusions for blog, mobile app placement exclusions, negative keywords

**MEDIUM (This Week):**

- Requires testing or client approval
- Strategic changes (bidding, audience signals, ad scheduling)
- Examples: conversion value rules, audience signal addition, day-parting

**LONG-TERM (This Month):**

- Strategic initiatives, requires development or multiple approvals
- Examples: offline conversion tracking, dedicated landing pages, CRM integration

**Every recommendation must be:**

1. **Verified** — confirmed as not already implemented (per Step 4)
2. **Specific** — exact steps, not generic advice
3. **Prioritized** — clear timeline
4. **Measurable** — expected impact quantified when possible

**Anti-pattern:** "Improve targeting" (vague). **Correct:** "Add `/community/*` to URL exclusions (not currently configured) — expected to reduce blog-page conversions by ~75%"

Use the companion skill's recommendation structure template for each action.

---

### Step 6: Document What Was Ruled Out

**Reference skill:** `ga4-campaign-cross-reference`

For each hypothesis that did NOT become a recommendation, document why using the companion skill's "What Was Ruled Out" template:

```markdown
### {Hypothesis}

**Initial Hypothesis:** {What we thought}
**Verification Method:** {How we checked}
**Finding:** Already implemented / Not applicable / Data anomaly
**Evidence:** {Specific data or settings}
```

This prevents redundant recommendations and demonstrates thoroughness.

---

### Step 7: Generate Analysis Document

**Reference skill:** `client-communication-standards`

Create a comprehensive markdown document using the **Background → Analysis → Conclusions** framework (EXACTLY 3 sections per the companion skill).

Every finding in the Analysis section must include a "What We Looked At:" attribution showing the data source.

---

## Adaptive Investigation

The skill is NOT required to run all steps. Use judgment:

- **Stop early** if Step 1 data collection fails or returns insufficient volume (<20 conversions in date range)
- **Deep dive** if bot traffic detected (Framework 3 + 4 red flags) — investigate user agents, IP patterns, form submission timing
- **Pivot** if geographic issues dominate (Framework 2 red flag) — cross-reference with targeting settings before recommending fixes
- **Expand date range** if low conversion volume prevents pattern detection

---

## Tools Used

- **Skill** — Auto-invoke 5 domain-knowledge companion skills (CRITICAL — use at start)
- **Read** — Access existing reports, scripts, account/property reference files
- **Write** — Create analysis document
- **Bash** — Execute campaign-settings and GA4 query scripts
- **Grep / Glob** — Find prior analyses, related scripts, account references

---

## Script Contract

The skill assumes two classes of script under `scripts/`:

1. **`query_campaign_settings.py`** — given a customer ID and campaign name, returns campaign configuration (geo targeting, URL exclusions, bid strategy, audience signals, ad scheduling, placement exclusions).
2. **GA4 query scripts** — given a GA4 property ID, campaign name, conversion event, and date range, return: conversion summary, landing pages, user segments (city / device / browser / hour), engagement metrics.

Both are environment-specific — they live where your Google Ads credentials, GA4 service account, account registry, and property registry live. This repo documents the skill's data contract; you implement the scripts against your own infrastructure.

**Reference implementation hooks:**

- Google Ads API access via `google-ads-python` (loads credentials from `google-ads.yaml`)
- GA4 Data API access via `google-analytics-data` (service account JSON)
- Account registry for CID lookups (your `accounts.json` or equivalent)
- GA4 property registry for property ID lookups (your `ga4_properties.json` or equivalent)

---

## Output Format

Return findings using the Background → Analysis → Conclusions framework:

```markdown
# {Account} {Campaign} — GA4 Lead Quality Analysis & Recommendations

**Date:** {Analysis Date}
**Campaign:** {Full Campaign Name}
**Customer ID:** {CID}
**GA4 Property:** {Property ID}
**Analysis Period:** {Date Range}

---

## Background

{Client concern — what they're seeing/experiencing}
{Investigation scope — what we analyzed and why}
{2-3 paragraphs maximum}

---

## Analysis

### Pattern Analysis Findings (5 Frameworks)

**What We Looked At:** Output of ga4-cross-analysis companion skill, {N} conversions over {date_range}

**Red Flags Detected:** {Count from lead-quality-pattern-analysis companion skill}

#### Framework 1: Landing Page Distribution ({N} conversions)

| Category | Conversions | % of Total | Top Examples |
|----------|-------------|------------|--------------|
| {Category} | {Count} | {%} | {Examples} |

**Red Flag Assessment:** {Apply Framework 1 thresholds from companion skill}
**Finding:** {Key insight}

#### Framework 2: Geographic Distribution

| Location | Conversions | Users | Notes |
|----------|-------------|-------|-------|
| {City} | {Count} | {Users} | {From Framework 2} |

**Red Flag Assessment:** {Apply Framework 2 thresholds}
**Finding:** {Key insight}

#### Framework 3: Device & Browser Analysis

| Device/Browser | Conversions | % | Bot Indicator? |
|----------------|-------------|---|----------------|
| {Device} | {Count} | {%} | {From Framework 3} |

**Red Flag Assessment:** {Apply Framework 3 thresholds}
**Finding:** {Key insight}

#### Framework 4: Time Patterns

| Hour | Conversions | % | Red Flag? |
|------|-------------|---|-----------|
| {Hour} | {Count} | {%} | {From Framework 4} |

**Red Flag Assessment:** {Apply Framework 4 thresholds}
**Finding:** {Key insight}

#### Framework 5: User Behavior

- **New vs Returning:** {Ratio}
- **Avg Session Duration:** {Duration}
- **Pages per Session:** {Pages}

**Red Flag Assessment:** {Apply Framework 5 thresholds}
**Finding:** {Key insight}

**Severity Classification:** {Severe / Moderate / Configuration}

---

### Campaign Settings Verification

**What We Looked At:** Output of `query_campaign_settings.py` for campaign {NAME}

- **Location Targeting:** {Settings}
- **URL Exclusions:** {Current exclusions or "None"}
- **Negative Keywords:** {Count and themes}
- **Audience Signals:** {Current signals}
- **Placement Exclusions:** {Current exclusions or "None"}
- **Ad Scheduling:** {Current schedule or "None"}
- **Bidding Strategy:** {Strategy + target}

---

### Cross-Reference Analysis (Hypothesis → Verification → Finding)

**What We Looked At:** GA4 pattern data + campaign settings

#### Hypothesis 1: {Name}

**GA4 Data Suggests:** {Observation}
**Campaign Settings Show:** {Configuration}
**Verification:** {How we checked}
**Finding:** {Gap to fix / Already configured / Data anomaly}
**Evidence:** {Specific settings or data}

{Repeat for each hypothesis}

---

### What Was Ruled Out

**What We Looked At:** Same data sources as above, applied to refuted hypotheses

#### {Hypothesis}

**Initial Hypothesis:** {What we thought}
**Verification Method:** {How we checked}
**Finding:** Already implemented / Not applicable
**Evidence:** {Specific data or settings}

---

## Conclusions

### Root Cause

{Primary issue identified via cross-reference analysis}

### Comprehensive Recommendations

#### IMMEDIATE ACTIONS (Implement Today)

##### 1. {Action Name}

- **Current State:** {What exists now}
- **Recommendation:** {Specific change}
- **Implementation Steps:**
  1. {Step 1}
  2. {Step 2}
- **Expected Impact:** {Quantified if possible}

#### MEDIUM-TERM ACTIONS (This Week)

##### 1. {Action Name}

{Use companion skill template}

#### LONG-TERM STRATEGIES (This Month)

##### 1. {Strategy Name}

{Use companion skill template}

### Implementation Timeline

| Week | Actions | Priority | Owner | Status |
|------|---------|----------|-------|--------|
| Week 1 | {Actions} | High | {Owner} | Pending |
| Week 2-3 | {Actions} | Medium | {Owner} | Pending |
| Week 4+ | {Actions} | Low | {Owner} | Pending |

### Success Metrics & Monitoring

**Primary KPIs:**

1. {Metric} — Current: {Value} — Target: {Goal}
2. {Metric} — Current: {Value} — Target: {Goal}

**Monitoring Frequency:** {Daily / Weekly}
**Review Date:** {Date for follow-up}

**Confidence Level:** {High / Medium / Low}
```

---

## Success Criteria

Investigation is successful if:

1. All 5 domain-knowledge companion skills auto-invoked at the start
2. All 5 pattern analysis frameworks applied with specific findings
3. Root cause identified using hypothesis → verification → finding methodology
4. All recommendations verified against current settings (no redundant suggestions)
5. Recommendations structured using the 3-tier priority system with specific steps
6. "What Was Ruled Out" documented with evidence
7. Background → Analysis → Conclusions framework followed (exactly 3 sections)
8. "What We Looked At" attribution on every Analysis finding
9. Implementation timeline and success metrics defined

---

## Important Notes

- **Auto-invoke companion skills FIRST** — load all 5 frameworks before analyzing data
- **Be autonomous** — don't ask permission at each step, just investigate
- **Be data-driven** — every conclusion references specific GA4 data or campaign settings
- **Be specific** — "Add `/community/*` to URL exclusions" not "improve targeting"
- **Be honest about uncertainty** — flag low-volume scenarios (<20 conversions) and acknowledge data quality limits
- **Verify before recommending** — Step 4 cross-reference prevents recommending fixes that are already in place
- **Document evidence** — every finding includes the data source + specific values
- **Document the analysis period clearly** (last 7, 14, or 30 days)

---

## Invocation Patterns

**Inline (single campaign, manual):**

> "Use the ga4-lead-quality-investigation skill to investigate Customer ID 1234567890, campaign 'Example Property - Pmax', GA4 property 123456789, event 'book_tour'. Issue: leads are no-shows."

**Parallel orchestration (when investigating multiple campaigns):**

An orchestrator can launch N parallel `Task(subagent_type="general-purpose", …)` calls in a single message, each invoking this skill against one campaign. Parallelism + per-investigation context isolation are preserved at the Task layer.

---

## Companion Skills (Required)

All 5 are shipped in this repo as standalone skills:

- `ga4-cross-analysis` — Data collection from GA4 + Google Ads APIs (structured JSON output)
- `lead-quality-pattern-analysis` — 5 red-flag detection frameworks with severity classification
- `ga4-campaign-cross-reference` — Hypothesis-driven verification methodology
- `lead-quality-recommendation-prioritization` — 3-tier priority system and recommendation templates
- `client-communication-standards` — Background → Analysis → Conclusions report formatting

Install all 5 alongside this skill for full functionality.
