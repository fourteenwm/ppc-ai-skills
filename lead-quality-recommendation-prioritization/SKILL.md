---
name: lead-quality-recommendation-prioritization
description: Recommendation prioritization framework with implementation timelines for lead quality investigations. Auto-invoke when generating recommendations, prioritizing actions, or creating implementation plans. Provides 3-tier priority system (Immediate/Medium/Long-term) with structured recommendation templates.
allowed-tools: [Read]
---

# Lead Quality Recommendation Prioritization Skill

**Purpose:** Provides standardized methodology for prioritizing and structuring lead quality recommendations with clear implementation timelines and success metrics.

**Type:** Domain knowledge skill (auto-invoked)

---

## Core Principle: Actionable, Verified, Prioritized

**Every recommendation must be:**
1. **Verified** - Confirmed as not already implemented
2. **Specific** - Exact steps, not generic advice
3. **Prioritized** - Clear timeline (Immediate/Medium/Long-term)
4. **Measurable** - Expected impact quantified when possible

**Anti-Pattern to Avoid:**
- ❌ "Improve targeting" (too vague)
- ❌ "Add negative keywords" (already done? which keywords?)
- ❌ "Optimize campaign" (no specific action)

**Correct Pattern:**
- ✅ "Add `/blog/*` to URL exclusions (not currently configured) - Expected to reduce conversions from blog pages by ~75%"

---

## Three-Tier Priority System

### 🚨 Tier 1: IMMEDIATE ACTIONS (Implement Today)

**Criteria for Immediate Priority:**
- Quick wins (can be done in <1 hour)
- Critical fixes (>3 red flags, severe quality issues)
- High impact, low effort
- No approvals or testing required
- Directly addresses root cause

**Time Frame:** Today (same day)

**Examples:**
- Adding URL exclusions for blog content
- Excluding mobile app placements
- Pausing underperforming campaigns
- Adding negative keywords for irrelevant queries

---

### ⚠️ Tier 2: MEDIUM-TERM ACTIONS (This Week)

**Criteria for Medium Priority:**
- Requires testing or validation
- Needs approval from client or stakeholder
- Medium effort (2-4 hours implementation)
- Strategic changes (bidding strategy, audience signals)
- Requires monitoring period before next step

**Time Frame:** Within 7 days

**Examples:**
- Adding conversion value rules
- Implementing audience signals
- Creating new campaigns or ad groups
- Adjusting budgets based on quality performance
- Setting up ad scheduling restrictions

---

### ℹ️ Tier 3: LONG-TERM STRATEGIES (This Month)

**Criteria for Long-term Priority:**
- Strategic initiatives (requires planning)
- Requires development work (landing pages, tracking)
- Needs multiple stakeholder approvals
- High effort (>1 week implementation)
- Foundational changes to account structure

**Time Frame:** Within 30 days

**Examples:**
- Implementing offline conversion tracking
- Creating dedicated thank-you pages with quality differentiation
- Building new landing pages
- Restructuring campaign architecture
- Implementing CRM integrations

---

## Recommendation Structure Template

### Standard Recommendation Format

```markdown
#### {Priority Emoji} {Action Number}. {Action Name}

**Current State:** {What exists now - be specific}

**Recommendation:** {Specific change to implement}

**Implementation Steps:**
1. {Step 1 - exact instruction}
2. {Step 2 - exact instruction}
3. {Step 3 - exact instruction}

**Expected Impact:**
- {Quantified metric if possible}
- {Timeline for seeing results}

**Verification Before Implementing:**
- [ ] Not already configured (checked {date})
- [ ] Technically feasible (confirmed {method})
- [ ] No conflicts with other campaigns
```

---

## Recommendation Examples by Tier

### Example 1: IMMEDIATE - URL Exclusions

```markdown
#### 🚨 1. Exclude Blog/Community Content from Performance Max

**Current State:**
- No URL exclusions configured
- 76.2% of conversions (64 of 84) coming from `/blog/*` blog pages
- Blog content = moving tips, neighborhood guides (informational, not property-focused)

**Recommendation:**
Add content exclusions for blog/informational URLs to focus spend on property/conversion pages

**Implementation Steps:**
1. Navigate to Performance Max campaign settings
2. Go to "Content" → "Exclusions" → "Excluded content"
3. Add the following URL patterns:
 - `*acme-plumbing.com/blog/*`
 - `*acme-plumbing.com/blog/*`
 - `*acme-plumbing.com/news/*`
4. Save changes

**Expected Impact:**
- Reduce conversions from blog traffic by ~75% (64 → 16 conversions)
- Improve lead quality by focusing on users viewing service pages
- May see 20-30% decrease in total conversions, but 50%+ improvement in show-up rate
- Should see impact within 3-5 days

**Verification:**
- ✅ Confirmed no URL exclusions currently configured (checked 2025-10-24)
- ✅ Blog URLs account for majority of low-quality conversions
- ✅ No risk to service page conversions (separate URL structure)
```

---

### Example 2: MEDIUM - Conversion Value Rules

```markdown
#### ⚠️ 2. Implement Conversion Value Rules Based on User Engagement

**Current State:**
- All conversions assigned equal value ($1 default)
- Bidding strategy = Maximize Conversion Value
- GA4 shows wide variance in user engagement (some <10 sec, some >5 min sessions)
- Algorithm can't differentiate high-engagement vs low-engagement conversions

**Recommendation:**
Create conversion value rules that assign higher value to engaged users

**Implementation Steps:**
1. Go to Tools → Conversions → Select "contact_form_submission"
2. Click "Value rules" → "New rule"
3. Create rules based on conditions:
 - **Rule 1 (High Value):** IF session duration >120 sec AND pages/session >3 → Value = $5
 - **Rule 2 (Medium Value):** IF session duration 30-120 sec → Value = $3
 - **Rule 3 (Low Value):** IF session duration <30 sec → Value = $1
4. Enable rules and monitor for 7 days
5. Review value distribution in reporting

**Expected Impact:**
- Algorithm will optimize toward higher-engagement users
- May see 10-20% decrease in conversion volume
- Should see 30-50% improvement in lead quality (measured by show-up rate)
- Requires 2-week learning period for Smart Bidding to adapt

**Verification:**
- ✅ Conversion value rules not currently configured (checked 2025-10-24)
- ⚠️ Requires client approval (data-driven value assignment)
- ✅ Compatible with Maximize Conversion Value strategy
- ⚠️ Need to monitor for 7-14 days before evaluating effectiveness
```

---

### Example 3: LONG-TERM - Offline Conversion Tracking

```markdown
#### ℹ️ 3. Implement Offline Conversion Tracking for Tour Attendance

**Current State:**
- Only tracking "contact_form" conversion (initial form submission)
- No tracking of actual tour attendance
- High no-show rate (~80%) but Google Ads doesn't know which leads showed up
- Algorithm optimizing for form fills, not quality attendees

**Recommendation:**
Implement offline conversion tracking to feed tour attendance data back to Google Ads

**Implementation Plan:**

**Phase 1: CRM Integration (Week 1-2)**
1. Work with client to access business CRM
2. Identify tour scheduling and attendance tracking fields
3. Map CRM data fields to Google Ads offline conversion schema

**Phase 2: API Setup (Week 2-3)**
4. Set up Google Ads Offline Conversion API access
5. Create conversion action "tour_attended" in Google Ads
6. Build data pipeline from CRM to Google Ads (daily sync)

**Phase 3: Testing (Week 3-4)**
7. Test with 1 week of historical data
8. Verify conversions appearing correctly in Google Ads
9. Confirm GCLID matching between initial conversion and attendance

**Phase 4: Activation (Week 4)**
10. Switch bidding optimization to "tour_attended" instead of "contact_form"
11. Monitor for 2-week learning period
12. Evaluate quality improvement

**Expected Impact:**
- Algorithm optimizes for users who actually attend tours (not just submit forms)
- Should see 50-70% improvement in show-up rate over 30 days
- May see initial conversion volume decrease as algorithm learns
- Long-term: Higher quality leads, better ROAS, happier client

**Dependencies:**
- ⚠️ Requires client CRM access and cooperation
- ⚠️ Requires development work (API integration)
- ⚠️ Requires minimum 30 conversions/month for Smart Bidding to work
- ℹ️ 4-6 week implementation timeline

**Success Metrics:**
- Show-up rate increases from 20% → 50%+ within 60 days
- Cost per attended tour becomes primary KPI
- Algorithm learns to identify high-intent users
```

---

## "What Was Ruled Out" Framework

**Purpose:** Document what was checked but didn't pan out, preventing redundant recommendations in future analyses.

**Why This Matters:**
- Shows thoroughness of investigation
- Prevents recommending already-implemented fixes
- Builds client trust (demonstrates due diligence)
- Helps future analysts avoid duplicate work

---

### "What Was Ruled Out" Template

```markdown
### ❌ {Idea/Recommendation}

**Initial Hypothesis:** {What we thought might be the problem}

**Verification Method:** {How we checked}

**Finding:** {Already implemented / Not applicable / Won't solve problem}

**Evidence:** {Specific data or settings that prove this}

**Conclusion:** {Why this isn't recommended}
```

---

### Example: Geographic Targeting Ruled Out

```markdown
### ❌ Adjust Geographic Targeting to Exclude Out-of-State Traffic

**Initial Hypothesis:**
Campaign serving ads to users in Phoenix, Fresno, Portland (outside NYC) due to targeting misconfiguration

**Verification Method:**
- Reviewed campaign location targeting settings
- Checked included/excluded locations
- Verified targeting radius

**Finding:** Already correctly configured

**Evidence:**
- Location targeting: "New York, NY, United States" with 40-mile radius
- No additional locations included
- No broad targeting or "Presence or Interest" settings
- GA4 shows conversions from outside NYC, but campaign IS NOT targeting those locations

**Conclusion:**
Geographic discrepancy is due to IP geolocation inaccuracy (common for mobile users, VPNs, carrier IPs), NOT a targeting problem. The campaign settings are correct - do NOT change targeting.

**Supporting Data:**
- 83.3% of conversions from Android Webview (known for IP geolocation issues)
- 100% mobile traffic (mobile carrier IPs often mislocated)
- Actual user addresses (from form data) are in NYC, despite GA4 showing other cities
```

---

## Implementation Timeline Template

**Purpose:** Provide week-by-week roadmap for all recommendations

```markdown
## Implementation Timeline

| Week | Actions | Priority | Owner | Status |
|------|---------|----------|-------|--------|
| Week 1 (Current) | • Add `/blog/*` URL exclusions<br>• Exclude mobile app placements<br>• Add negative keywords for irrelevant terms | 🚨 High | Media Buyer | ⏳ Pending |
| Week 2 | • Implement conversion value rules<br>• Add audience signals (in-market potential customers)<br>• Monitor quality improvements | ⚠️ Medium | Media Buyer | ⏳ Pending |
| Week 3 | • Review conversion value distribution<br>• Adjust rules based on learning<br>• Begin offline conversion planning | ⚠️ Medium | Media Buyer + Client | ⏳ Pending |
| Week 4 | • Initiate CRM integration for offline conversions<br>• Build data pipeline<br>• Create "tour_attended" conversion action | ℹ️ Low | Developer + Media Buyer | ⏳ Pending |
```

---

## Success Metrics & Monitoring Template

**Purpose:** Define how to measure if recommendations are working

```markdown
## Success Metrics & Monitoring

**Primary KPIs:**
1. **Show-up Rate** (tours attended ÷ tours booked)
 - Current: ~20%
 - Target: >50% within 30 days
 - Measurement: Client CRM data

2. **Cost per Attended Tour** (spend ÷ tours attended)
 - Current: ~$250 (estimated, based on 20% show-up rate)
 - Target: <$100 within 60 days
 - Measurement: Google Ads spend ÷ CRM tour attendance

3. **Conversion Rate from Service Pages** (conversions ÷ clicks on service pages)
 - Current: Unknown (mixed with blog traffic)
 - Target: Establish baseline after URL exclusions
 - Measurement: GA4 landing page report + Google Ads

**Secondary KPIs:**
- Conversion volume (expect 20-30% decrease initially, then stabilize)
- CPA (may increase initially, but quality improves)
- Conversion value (if value rules implemented)

**Monitoring Frequency:**
- **Daily (Week 1):** Check for implementation errors, monitor conversion volume
- **Weekly (Weeks 2-4):** Review quality metrics, adjust rules as needed
- **Monthly:** Full analysis report comparing before/after

**Review Date:** {30 days from implementation}
```

---

## Prioritization Decision Tree

Use this tree to determine priority tier for each recommendation:

```
START: Is this recommendation verified as not already implemented?
 └─ NO → Do NOT recommend (document in "What Was Ruled Out")
 └─ YES → Continue

Can this be implemented in <1 hour with no approvals?
 └─ YES → Is impact high (addresses root cause)?
 └─ YES → 🚨 IMMEDIATE PRIORITY
 └─ NO → ⚠️ MEDIUM PRIORITY (quick but not critical)
 └─ NO → Continue

Does this require client approval or testing?
 └─ YES → ⚠️ MEDIUM PRIORITY
 └─ NO → Continue

Does this require >1 week implementation or development work?
 └─ YES → ℹ️ LONG-TERM PRIORITY
 └─ NO → ⚠️ MEDIUM PRIORITY (moderate effort)
```

---

## Quality Checks Before Recommending

**Pre-Flight Checklist:**

Before adding any recommendation to final report:

- [ ] **Verified not already implemented** (checked campaign settings on {date})
- [ ] **Specific and actionable** (not generic advice like "improve quality")
- [ ] **Implementation steps provided** (exact instructions, not just "do this")
- [ ] **Expected impact quantified** (% change, timeline, metric)
- [ ] **Priority tier assigned** (Immediate / Medium / Long-term)
- [ ] **Verification evidence documented** (how we confirmed it's not already done)
- [ ] **No conflicts with other recommendations** (actions don't contradict each other)
- [ ] **Technically feasible** (confirmed possible in Google Ads platform)

**If ANY checklist item fails:**
- Do NOT include recommendation
- Either fix the gap (add missing details) or document in "What Was Ruled Out"

---

## Integration with Investigation Workflow

### Pre-Recommendations (Pattern Analysis & Cross-Reference):
1. **lead-quality-pattern-analysis** - Identifies red flags and issues
2. **ga4-campaign-cross-reference** - Verifies what's already configured vs gaps

### During Recommendations (This Skill):
3. Apply prioritization decision tree to each finding
4. Structure recommendations using templates
5. Create "What Was Ruled Out" documentation
6. Build implementation timeline

### Post-Recommendations (Output):
7. **client-communication-standards** - Format final report
8. Include success metrics and monitoring plan
9. Deliver with clear next steps

---

## Real-World Example: Example PMAX Prioritization

### Findings from Analysis:
- 5 red flags detected (🚨 Severe)
- 3 configuration gaps confirmed
- 2 hypotheses ruled out

### Recommendations Generated:

**🚨 IMMEDIATE (3 actions):**
1. Add `/blog/*` URL exclusions → Addresses 76.2% blog traffic
2. Reduce budget during seasonal decline → Preserves budget for better timing
3. Pause AI Max campaign → Underperforming, cannibalizing Pmax budget

**⚠️ MEDIUM (2 actions):**
4. Implement conversion value rules → Requires testing, client awareness
5. Review mobile app placements → Requires deeper placement report analysis

**ℹ️ LONG-TERM (2 actions):**
6. Dual thank-you page setup → Requires client dev work
7. Offline conversion tracking → Requires CRM integration (4-6 weeks)

**❌ RULED OUT (2 hypotheses):**
1. Geographic targeting changes → Verified targeting correct, IP geolocation issue
2. Add negative keywords → Already comprehensive list configured

### Implementation Timeline:
- **Week 1:** All IMMEDIATE actions completed
- **Week 2-3:** MEDIUM actions implemented and monitored
- **Week 4+:** LONG-TERM planning initiated

### Result:
Clear action plan with specific next steps, verified recommendations, and documented due diligence (ruled-out items)

---

## When to Use This Skill

### Auto-Invoked When:
- Generating lead quality recommendations
- Prioritizing investigation findings
- Creating implementation timelines
- Documenting "What Was Ruled Out"
- User asks "what should I do about {lead quality issue}"

### Manual Invocation:
- Campaign audits (organizing findings)
- Client reports (structuring recommendations)
- Monthly reviews (prioritizing fixes)

---

## Related Skills & Documentation

**Related Skills:**
- **lead-quality-pattern-analysis** - Identifies issues that become recommendations
- **ga4-campaign-cross-reference** - Verifies what's already done (prevents duplicate recommendations)
- **client-communication-standards** - Formatting for final report delivery
- **budget-recommendation-calculator** - Similar prioritization framework for budget changes

**Related Documentation:**
- Example PMAX GA4 Analysis (example of full recommendation structure)
- GA4 Cross-Analysis System Overview
- Client communication examples

---

**Created:** 2025-11-01
**Extracted From:** ga4-lead-quality-investigation-agent.md (Prioritize Recommendations & Output sections)
**Status:** Active
