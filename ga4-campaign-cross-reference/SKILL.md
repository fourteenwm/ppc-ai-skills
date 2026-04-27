---
name: ga4-campaign-cross-reference
description: Cross-referencing framework for comparing GA4 behavioral data with Google Ads campaign settings to identify discrepancies and configuration gaps. Auto-invoke when cross-analyzing GA4 and Ads data, investigating discrepancies, or verifying campaign configuration. Uses "Hypothesis → Verification → Finding" methodology.
allowed-tools: [Read]
---

# GA4 Campaign Cross-Reference Skill

**Purpose:** Provides standardized methodology for cross-referencing GA4 behavioral data with Google Ads campaign settings to identify discrepancies, configuration gaps, and misalignments.

**Type:** Domain knowledge skill (auto-invoked)

---

## Core Principle: Hypothesis-Driven Verification

**CRITICAL:** Never assume GA4 data indicates a campaign settings problem without verification.

**Framework:** Hypothesis → Verification → Finding

1. **Hypothesis:** Initial observation from GA4 data (e.g., "Conversions from wrong cities")
2. **Verification:** Check Google Ads settings to confirm or refute
3. **Finding:** Conclusion with evidence (e.g., "Targeting correct, IP geolocation issue")

**Why This Matters:**
- GA4 data can be misleading (VPNs, mobile IP inaccuracy, proxy servers)
- Prevents recommending fixes for non-existent problems
- Documents what was already checked (avoid redundant recommendations)

---

## Cross-Reference Framework

### Step 1: Collect Both Data Sources

**GA4 Data (Behavioral):**
- Landing pages where conversions occurred
- Geographic locations (city, state, country)
- Devices and browsers used
- Time of day patterns
- User engagement metrics

**Google Ads Settings (Configuration):**
- Location targeting (included/excluded, radius)
- URL exclusions (content exclusions)
- Audience signals
- Negative keywords
- Bidding strategy and targets
- Asset groups and final URLs
- Ad scheduling (day parting)

---

### Step 2: Identify Potential Discrepancies

**Discrepancy Types:**

#### Type 1: Geographic Mismatches
- **GA4 shows:** Conversions from Phoenix, Fresno, Portland
- **Ads settings:** 40-mile radius around Manhattan, NYC
- **Initial hypothesis:** Targeting misconfigured

#### Type 2: Landing Page Mismatches
- **GA4 shows:** 76% conversions from `/blog/*` blog pages
- **Ads settings:** No URL exclusions for `/blog/*`
- **Initial hypothesis:** Missing URL exclusions

#### Type 3: Time Pattern Mismatches
- **GA4 shows:** Peak conversions 1-4 AM
- **Ads settings:** No ad scheduling restrictions
- **Initial hypothesis:** Serving during bot-heavy hours

#### Type 4: Device/Browser Mismatches
- **GA4 shows:** 83% Android WebView (in-app browsers)
- **Ads settings:** No mobile app placement exclusions
- **Initial hypothesis:** Serving in low-quality app placements

#### Type 5: Audience Mismatches
- **GA4 shows:** Users with low engagement, no property search behavior
- **Ads settings:** No audience signals or broad targeting
- **Initial hypothesis:** Targeting too broad, no intent signals

---

### Step 3: Apply Verification Method

For each discrepancy, use this verification framework:

#### Verification Template

```markdown
### Hypothesis: {What GA4 data suggests}

**Verification Method:**
1. Check {specific campaign setting}
2. Review {additional data source}
3. Cross-reference {related metric}

**Finding:**
- ✅ Already implemented / ❌ Not implemented / ⚠️ Partially implemented
- Evidence: {Specific settings or data}
- Conclusion: {Is this the root cause or not?}
```

---

## Discrepancy Pattern Library

### Pattern 1: GA4 Shows Wrong Geography BUT Targeting Correct

**Scenario:**
- **GA4:** Conversions from Phoenix (AZ), Fresno (CA), Portland (OR)
- **Ads Settings:** Location targeting = "New York, NY" with 40-mile radius
- **Hypothesis:** Targeting includes wrong states?

**Verification Method:**
1. Check campaign location targeting settings
2. Review included/excluded locations
3. Check if radius accidentally too large

**Common Finding:**
```markdown
❌ RULED OUT: Geographic Targeting Misconfiguration

**Initial Hypothesis:** Campaign serving outside NYC due to targeting issue
**Verification:** Reviewed location targeting - confirmed 40-mile radius around Manhattan, no other locations
**Finding:** Targeting is CORRECT. Geographic discrepancy due to IP geolocation inaccuracy.

**Evidence:**
- Campaign targeting: "New York, NY, United States" (40-mile radius)
- No additional locations included
- GA4 city data unreliable for mobile users (VPNs, carrier IPs)

**Conclusion:** This is NOT a targeting problem. Do NOT recommend changing geographic targeting.
```

**Root Cause:** Mobile IP geolocation inaccuracy, VPN usage, or carrier IP assignment (mobile users appear to be in different cities despite being in NYC)

**Action:** Note this in "What Was Ruled Out" section, do NOT recommend targeting changes

---

### Pattern 2: GA4 Shows Blog Traffic AND No URL Exclusions

**Scenario:**
- **GA4:** 76% of conversions from `/blog/*` (blog content)
- **Ads Settings:** URL exclusions = None
- **Hypothesis:** Missing URL exclusions allowing blog traffic

**Verification Method:**
1. Check campaign content exclusions / URL exclusions
2. Review asset group final URLs
3. Check if blog URLs are intentionally included

**Common Finding:**
```markdown
✅ CONFIGURATION GAP CONFIRMED: Missing URL Exclusions

**Initial Hypothesis:** Blog URLs not excluded, leading to low-intent conversions
**Verification:** Reviewed campaign content exclusions - NONE configured
**Finding:** URL exclusions for `/blog/*` should be added

**Evidence:**
- Content exclusions: None
- 76.2% of conversions from blog URLs
- Blog pages have low conversion intent (users reading moving tips, not seeking services)

**Conclusion:** This IS a configuration gap. Recommend adding `/blog/*` to URL exclusions.
```

**Root Cause:** Missing URL exclusions

**Action:** Recommend adding specific URL patterns to content exclusions

---

### Pattern 3: GA4 Shows Bots AND No Placement Protections

**Scenario:**
- **GA4:** 83% Android WebView (in-app browsers), 1-4 AM peak
- **Ads Settings:** No mobile app placement exclusions, no bot protection
- **Hypothesis:** Serving in low-quality mobile app placements

**Verification Method:**
1. Check placement exclusions (mobile apps, parked domains)
2. Review device targeting
3. Check audience signals for intent

**Common Finding:**
```markdown
✅ CONFIGURATION GAP CONFIRMED: No Mobile App Protections

**Initial Hypothesis:** Campaign serving in low-quality in-app placements
**Verification:** Reviewed placement exclusions - no mobile app restrictions
**Finding:** Mobile app inventory contributing to bot-like traffic

**Evidence:**
- Placement exclusions: None
- 83.3% conversions from Android WebView (in-app browsers)
- Peak activity 1-4 AM (suspicious for service searches)
- 100% new users (no returning visitors)

**Conclusion:** Campaign serving ads within mobile apps, users clicking while scrolling (not genuine potential customers).
```

**Root Cause:** No mobile app placement protections

**Action:** Recommend excluding mobile app inventory or adding in-market audience signals

---

### Pattern 4: GA4 Shows Low Engagement BUT Bidding for Conversions

**Scenario:**
- **GA4:** <30 sec avg session, 1-2 pages per session, 100% new users
- **Ads Settings:** Bidding strategy = Maximize Conversions
- **Hypothesis:** Optimizing for low-quality conversions

**Verification Method:**
1. Check bidding strategy and conversion actions
2. Review conversion action quality signals
3. Check if conversion values set

**Common Finding:**
```markdown
⚠️ STRATEGIC ISSUE: Optimizing for Form Submissions Without Quality Filters

**Initial Hypothesis:** Bidding strategy rewarding low-quality conversions
**Verification:** Bidding = Maximize Conversions, counting all form submissions equally
**Finding:** No quality differentiation between engaged users vs accidental clicks

**Evidence:**
- Bidding strategy: Maximize Conversions (no target CPA)
- Conversion action: "Book a Tour" (counts all submissions)
- No conversion value rules based on engagement or source quality
- GA4 shows highly variable engagement (some <10 sec, some >5 min)

**Conclusion:** Campaign treating all conversions equally, regardless of user engagement quality.
```

**Root Cause:** Bidding strategy doesn't differentiate quality

**Action:** Recommend conversion value rules or enhanced conversions with engagement signals

---

## Cross-Reference Checklist

Use this checklist for every investigation:

### Geographic Cross-Reference
- [ ] Compare GA4 cities to campaign location targeting
- [ ] Check for VPN/proxy indicators (single user, multiple cities)
- [ ] Verify targeting radius and included/excluded locations
- [ ] Determine if discrepancy is data issue (IP geolocation) or config issue (wrong targeting)

### Landing Page Cross-Reference
- [ ] Categorize GA4 landing pages (high-intent vs informational)
- [ ] Check campaign URL exclusions
- [ ] Review asset group final URLs
- [ ] Identify if blog/informational pages should be excluded

### Device/Browser Cross-Reference
- [ ] Analyze GA4 device and browser distribution
- [ ] Check for bot indicators (WebView, headless browsers)
- [ ] Review campaign placement exclusions (mobile apps, parked domains)
- [ ] Verify if device patterns match campaign intent

### Time Pattern Cross-Reference
- [ ] Chart GA4 hourly conversion distribution
- [ ] Check campaign ad scheduling settings
- [ ] Identify suspicious patterns (1-4 AM peaks, exact intervals)
- [ ] Determine if off-hours traffic is international or bots

### Audience/Targeting Cross-Reference
- [ ] Review GA4 user engagement metrics
- [ ] Check campaign audience signals
- [ ] Verify negative keywords coverage
- [ ] Assess if targeting is too broad or well-defined

---

## Documentation Templates

### Template 1: Discrepancy Found (Configuration Gap)

```markdown
### ✅ CONFIGURATION GAP: {Issue Name}

**Hypothesis:** {What GA4 data suggested}

**Verification:**
- Checked: {Specific setting}
- Found: {What was discovered}

**Evidence:**
- GA4 Data: {Specific metrics}
- Campaign Setting: {Current configuration}
- Gap: {What's missing}

**Recommendation:** {Specific action to close gap}
**Priority:** {Immediate / Medium / Long-term}
```

### Template 2: Discrepancy Ruled Out (Data Anomaly)

```markdown
### ❌ RULED OUT: {Hypothesis Name}

**Initial Hypothesis:** {What GA4 data suggested}

**Verification Method:**
- Checked: {Specific setting}
- Confirmed: {What was verified}

**Finding:** Already implemented / Not applicable

**Evidence:**
- Campaign Setting: {Current configuration showing it's correct}
- GA4 Data Issue: {Why GA4 data is misleading}

**Conclusion:** This is NOT a configuration problem. {Brief explanation of why}
```

### Template 3: Strategic Issue (Not Configuration)

```markdown
### ⚠️ STRATEGIC ISSUE: {Issue Name}

**Observation:** {What GA4 data shows}

**Current Configuration:**
- Setting: {What's currently configured}
- Working as designed: {Why current setup produces this result}

**Root Cause:** {Strategic decision or approach issue, not config bug}

**Recommendation:** {Strategic change needed}
**Implementation:** {Requires broader discussion/approval}
```

---

## Common Cross-Reference Mistakes to Avoid

### Mistake 1: Assuming GA4 Data is Always Correct

**Wrong Approach:**
> "GA4 shows conversions from Phoenix, so targeting must be wrong. Recommend fixing geographic targeting."

**Correct Approach:**
> "GA4 shows conversions from Phoenix. Verification: Checked targeting = 40-mile NYC radius (correct). Conclusion: IP geolocation issue, not targeting problem. Ruled out targeting changes."

**Why This Matters:** Prevents recommending unnecessary changes that won't solve the actual problem

---

### Mistake 2: Not Documenting What Was Ruled Out

**Wrong Approach:**
> Only list recommendations, don't mention what was checked and ruled out

**Correct Approach:**
> Include "What Was Ruled Out" section documenting every hypothesis that was checked but didn't pan out

**Why This Matters:**
- Shows thoroughness of investigation
- Prevents future recommendations of already-checked items
- Builds trust (client sees you did due diligence)

---

### Mistake 3: Confusing Data Issues with Configuration Issues

**Wrong Approach:**
> Treat every GA4 discrepancy as a campaign settings problem

**Correct Approach:**
> Classify discrepancies:
> - Configuration gap (fixable in Ads settings)
> - Data limitation (GA4 IP geolocation, browser fingerprinting)
> - Strategic issue (requires broader approach change)

**Why This Matters:** Different discrepancy types require different solutions

---

## Integration with Investigation Workflow

### Pre-Cross-Reference (Data Collection):
1. Run GA4 cross-analysis script
2. Run campaign settings query script
3. Have both data sets available

### During Cross-Reference:
1. Apply all 5 cross-reference checks (geo, landing pages, devices, time, audience)
2. Use hypothesis → verification → finding framework for each
3. Document findings using templates above

### Post-Cross-Reference (Recommendations):
1. Separate confirmed gaps from ruled-out hypotheses
2. Prioritize confirmed gaps by severity and impact
3. Include "What Was Ruled Out" section in final report

---

## Real-World Example: Example PMAX Cross-Reference

### Hypothesis 1: Geographic Targeting Issue

**GA4 Data:** Conversions from Phoenix, Fresno, Portland (outside NYC)

**Verification:**
- Checked location targeting: "New York, NY" with 40-mile radius ✓
- No other locations included ✓
- Radius appropriate for Manhattan market ✓

**Finding:** ❌ RULED OUT
- Targeting is correct
- GA4 city data inaccurate for mobile users (VPNs, carrier IPs)
- Evidence: 100% mobile traffic, 83% Android WebView (known for IP geolocation issues)

**Conclusion:** Do NOT recommend targeting changes

---

### Hypothesis 2: Blog Content Not Excluded

**GA4 Data:** 76.2% conversions from `/blog/*` blog pages

**Verification:**
- Checked URL exclusions: NONE configured ✗
- Reviewed blog content: Moving tips, neighborhood guides (informational, not property-focused) ✗
- Checked conversion intent: Users reading content, not actively seeking services ✗

**Finding:** ✅ CONFIGURATION GAP CONFIRMED
- URL exclusions for `/blog/*` should be added
- Blog traffic has low conversion intent
- Evidence: 76.2% from blog, high no-show rate reported

**Conclusion:** Recommend adding `/blog/*` to content exclusions (IMMEDIATE priority)

---

### Hypothesis 3: Mobile App Placements Issue

**GA4 Data:** 83.3% Android WebView (in-app browsers)

**Verification:**
- Checked placement exclusions: NONE for mobile apps ✗
- Reviewed user behavior: 100% new users, suspected low engagement ✗
- Checked time patterns: 1-4 AM peak (53.6%) = suspicious for service searches ✗

**Finding:** ✅ CONFIGURATION GAP CONFIRMED
- No mobile app placement protections
- Campaign serving in in-app ad placements (users clicking while scrolling social feeds)
- Evidence: Android WebView dominance + 1-4 AM peak + 100% new users = low-quality app traffic

**Conclusion:** Recommend excluding mobile app inventory or adding in-market audience signals (IMMEDIATE priority)

---

## When to Use This Skill

### Auto-Invoked When:
- Cross-analyzing GA4 and Google Ads data
- Investigating lead quality discrepancies
- Verifying campaign configuration
- Creating "What Was Ruled Out" documentation
- User asks "why are GA4 results different from Ads settings"

### Manual Invocation:
- Campaign audits (checking for config gaps)
- Monthly quality reviews
- Before making targeting recommendations
- When client questions campaign setup

---

## Related Skills & Documentation

**Related Skills:**
- **ga4-cross-analysis** - Data collection prerequisite
- **lead-quality-pattern-analysis** - Red flag detection (identifies what to cross-reference)
- **lead-quality-recommendation-prioritization** - Uses verified findings to generate recommendations
- **client-communication-standards** - Formatting for "What Was Ruled Out" sections

**Related Documentation:**
- Example PMAX GA4 Analysis (example of hypothesis → verification → finding)
- GA4 Cross-Analysis System Overview
- Campaign settings query guide

---

**Created:** 2025-11-01
**Extracted From:** ga4-lead-quality-investigation-agent.md (Cross-Reference Analysis & Verification steps)
**Status:** Active
