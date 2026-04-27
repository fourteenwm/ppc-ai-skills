---
name: budget-recommendation-calculator
description: Calculates conservative budget recommendations for Google Ads accounts based on pacing variance, impression share analysis, and performance constraints. Auto-invoke when creating budget recommendations, investigating underspending, or determining optimal budget increases. Enforces 5-10% increase limits and performance safeguards.
allowed-tools: [Read]
---

# Budget Recommendation Calculator Skill

**Purpose:** Provides standardized methodology for calculating conservative, data-driven budget recommendations that balance pacing targets with performance goals.

**Type:** Domain knowledge skill (auto-invoked)

---

## Core Principles

### Budget Philosophy
1. **Primary Goal:** Hit monthly spend targets (pacing within tolerance)
2. **Secondary Goal:** Maintain acceptable CPA/ROAS performance
3. **Conservative Approach:** 5-10% increases (not aggressive jumps)
4. **Algorithm Safety:** Avoid shocking smart bidding algorithms
5. **Performance Guardrails:** Never increase if performance is failing

### Why Conservative Increases?
- **Smart bidding needs time to adapt** (3-7 day ramp-up period)
- **Large budget jumps risk CPA spikes** (algorithm overspends during adjustment)
- **Multiple small increases > one large increase** (safer, more controllable)
- **Client trust:** Predictable, controlled spend changes

---

## Budget Recommendation Decision Tree

### Decision Point 1: Should We Increase Budget?

#### ✅ YES - Increase Budget if ALL of the following are true:
1. **Pacing Variance Check:**
   - Standard tolerance portfolios: Underspending beyond ±8% monthly tolerance
   - Tight tolerance portfolios: Underspending beyond ±5% monthly tolerance
   - At least 5 days into the month (exclude early-month variance)

2. **Performance Check:**
   - CPA is acceptable (within goal or <20% over)
   - OR ROAS is acceptable (within goal or >80% of target)
   - No major quality issues flagged

3. **Impression Share Check:**
   - Budget Lost IS >10% (spend potential exists)
   - OR Rank Lost IS >50% + any Budget Lost IS (competitive pressure + budget constraint)

4. **Recent Changes Check:**
   - NO budget increase in last 7 days (avoid ramp-up period)
   - NO recent campaign launches in last 7 days
   - NO major targeting changes in last 7 days

#### ❌ NO - Do NOT Increase Budget if ANY of the following are true:
1. **Performance Failure:**
   - CPA >20% over goal (need quality fixes first)
   - ROAS <80% of target (efficiency issues)
   - Cost per conversion increasing >20% week-over-week

2. **Recent Changes:**
   - Budget increased within last 7 days (still ramping)
   - New campaigns launched within last 7 days
   - Major targeting/bidding changes within last 7 days

3. **Low Demand:**
   - Search IS >80% AND Budget Lost IS <10% (capturing most demand)
   - No spend potential (already maximizing available impressions)

4. **Month Timing:**
   - Less than 5 days into month (early-month variance normal)
   - Less than 3 days left in month (too late for meaningful impact)

---

## Budget Increase Calculation Methods

### Method 1: Pacing-Based Calculation (Primary Method)

**When to use:** Standard underspending investigation with clear pacing variance

**Formula:**
```
Target Monthly Budget = Current Monthly Budget × (1 + (Pacing Variance × Adjustment Factor))

Where:
- Pacing Variance = % Over/Under from monthly spend target
- Adjustment Factor = 0.5 to 1.0 (conservative to moderate)
```

**Example 1: Moderate Underspending (+13%)**
```
Current Monthly Budget: $1,000
Pacing Variance: +13.18% (underspending by 13.18%)
Adjustment Factor: 0.5 (conservative - only close half the gap)

Target Monthly Budget = $1,000 × (1 + (0.1318 × 0.5))
                      = $1,000 × 1.0659
                      = $1,065.90

Rounded: $1,065 (6.5% increase) ✅ WITHIN 5-10% RANGE
```

**Example 2: Severe Underspending (+25%)**
```
Current Monthly Budget: $1,000
Pacing Variance: +25% (underspending by 25%)
Adjustment Factor: 0.4 (very conservative - cap at 10% increase)

Target Monthly Budget = $1,000 × (1 + (0.25 × 0.4))
                      = $1,000 × 1.10
                      = $1,100

Result: $1,100 (10% increase) ✅ AT MAX 10% INCREASE
Note: "Will require additional increases after ramp-up period"
```

**Adjustment Factor Guidelines:**
- **0.3-0.4:** Very conservative (use for >20% variance, performance concerns)
- **0.5:** Standard conservative (use for 10-20% variance)
- **0.6-0.7:** Moderate (use for 5-10% variance, strong performance)
- **0.8-1.0:** Aggressive (use for <5% variance, excellent performance)

**HARD CAP: Never exceed 10% increase in single change**

---

### Method 2: Impression Share-Based Calculation (Alternative)

**When to use:** When Budget Lost IS is very high (>30%) and you want to estimate full spend potential

**Formula:**
```
Estimated Full Spend Potential = Current Spend ÷ (1 - Budget Lost IS)
```

**Example:**
```
Current MTD Spend: $500
Budget Lost IS: 40% (0.40)

Estimated Full Spend Potential = $500 ÷ (1 - 0.40)
                                = $500 ÷ 0.60
                                = $833 (for current MTD period)

If we're 50% through month:
Projected Monthly Spend Potential = $833 × 2 = $1,666

Current Monthly Budget: $1,000
Spend Potential: $1,666

Gap: $666 (66% increase needed)

APPLY 10% CAP:
Recommended: $1,100 (10% increase)
Note: "Significant untapped spend potential - will require multiple increases"
```

**Use Case:** This method is good for understanding total opportunity, but ALWAYS apply 5-10% cap to actual recommendation.

---

### Method 3: Daily Budget Calculation (Tactical)

**When to use:** When you need to translate monthly budget to daily budget for Google Ads implementation

**Formula:**
```
Daily Budget = Monthly Budget ÷ Days in Month
```

**Example: October (31 days)**
```
Recommended Monthly Budget: $1,100
Days in October: 31

Daily Budget = $1,100 ÷ 31 = $35.48/day

Rounded: $35.50/day (Google Ads allows 2 decimal places)
```

**Example: February (28 days)**
```
Recommended Monthly Budget: $1,400
Days in February: 28

Daily Budget = $1,400 ÷ 28 = $50.00/day
```

**IMPORTANT:** Google Ads can spend up to 2x daily budget on any single day, but will not exceed monthly total (daily budget × days in month).

---

## Budget Recommendation Output Format

### Standard Recommendation Template

```
================================================================================
BUDGET RECOMMENDATION
================================================================================

CURRENT STATE:
- Current Monthly Budget: $X,XXX
- Current Daily Budget: $XX.XX/day
- MTD Spend (through Day XX): $X,XXX
- Pacing Variance: +X.X% (UNDERSPENDING by X.X%)
- % Through Month: XX.X%
- % Spent: XX.X%

PERFORMANCE CHECK:
- Cost per Conversion: $XX.XX (Goal: $XX.XX) ✅ WITHIN GOAL
- [or ROAS: X.Xx (Goal: X.Xx) ✅ WITHIN GOAL]
- Performance allows for budget increase

IMPRESSION SHARE ANALYSIS:
- Search Impression Share: XX%
- Budget Lost IS: XX% (spend potential exists)
- Rank Lost IS: XX% (competitive pressure)
- Diagnosis: Budget constraint is primary limiter

RECOMMENDATION:
✅ Increase Monthly Budget: $X,XXX → $X,XXX (+X.X%)
✅ New Daily Budget: $XX.XX/day

Rationale:
- Pacing variance (+X.X%) exceeds ±8% tolerance
- Budget Lost IS (XX%) indicates spend potential
- CPA performance acceptable (within goal)
- Conservative X.X% increase to move toward pacing target

Expected Outcome:
- Reduce pacing variance from +X.X% to ~+X.X% (closer to ±8% range)
- Maintain acceptable CPA performance
- Algorithm will ramp up over 3-5 days

Next Steps:
1. Implement budget increase in Google Ads
2. Monitor daily for 5-7 days during ramp-up period
3. Re-evaluate pacing after ramp-up period
4. Consider additional increase if still underspending after 7 days

Confidence Level: High
================================================================================
```

---

### Alternative: Do NOT Increase Budget Template

```
================================================================================
BUDGET RECOMMENDATION
================================================================================

CURRENT STATE:
- Current Monthly Budget: $X,XXX
- MTD Spend (through Day XX): $X,XXX
- Pacing Variance: +X.X% (UNDERSPENDING by X.X%)

PERFORMANCE CHECK:
- Cost per Conversion: $XX.XX (Goal: $XX.XX) ❌ OVER GOAL (+XX%)
- [or ROAS: X.Xx (Goal: X.Xx) ❌ BELOW GOAL]
- Performance does NOT allow for budget increase

RECOMMENDATION:
❌ Do NOT Increase Budget

Rationale:
- CPA is XX% over goal (quality issues present)
- Increasing budget would worsen CPA (more spend on inefficient traffic)
- Need quality improvements first (ad relevance, landing page, keywords)

Alternative Actions:
1. Improve ad relevance (align ad copy with keywords)
2. Optimize landing pages (speed, mobile experience, relevance)
3. Refine keyword quality (pause low-performing keywords)
4. Re-evaluate budget after quality improvements stabilize

Expected Timeline:
- Quality improvements: 2-3 weeks to stabilize
- Re-evaluate budget after CPA returns to goal range
- Budget increase only if CPA acceptable AND still underspending

Confidence Level: High
================================================================================
```

---

## Special Cases & Edge Cases

### Case 1: Ramp-Up Period (Recent Budget Increase)

**Pattern:**
- Budget increased within last 7 days
- Currently underspending vs. new budget
- Impression share metrics not stabilized

**Recommendation:**
```
❌ Do NOT Increase Budget (ramp-up period)

Rationale:
- Budget increased X days ago (recent change)
- Smart bidding algorithm needs 3-7 days to adjust
- Current underspending is expected during ramp-up

Action: Monitor for 3-5 more days
Timeline: Re-evaluate on [Date] (7 days after increase)
```

---

### Case 2: Low Demand (High Search IS, Low Budget Lost IS)

**Pattern:**
- Search IS >80%
- Budget Lost IS <10%
- Still underspending vs. budget

**Recommendation:**
```
❌ Do NOT Increase Budget (low demand, not constraint)

Rationale:
- Already capturing XX% of available impressions
- Budget Lost IS only X% (minimal spend potential)
- Underspending is due to low search volume, not budget limit

Alternative Options:
1. Accept as normal (low demand market)
2. Consider REDUCING budget to match actual demand
3. Expand targeting (new keywords, broader match, new geos)

Note: Increasing budget will NOT increase spend in this scenario
```

---

### Case 3: Shared Budget Dynamics

**Pattern:**
- Multiple campaigns share one budget
- One campaign dominating spend (>80% of shared budget)
- Other campaigns starved (<20% of shared budget)

**Recommendation:**
```
⚠️ Shared Budget Reallocation (not just increase)

Current Shared Budget: $X,XXX/month
Campaign A: $X,XXX (XX%) - dominating
Campaign B: $XXX (XX%) - starved

Options:
1. Increase shared budget (+5-10%) → benefits Campaign A primarily
2. Split into individual budgets → granular control
3. Adjust campaign priorities (Google Ads beta feature)

Recommended: Split into individual budgets
- Campaign A Individual Budget: $X,XXX
- Campaign B Individual Budget: $XXX
- Allows precise pacing control per campaign
```

---

### Case 4: End-of-Month Catch-Up

**Pattern:**
- Less than 7 days left in month
- Significant underspending (>15%)
- Need to catch up quickly

**Recommendation:**
```
⚠️ End-of-Month Catch-Up (aggressive but necessary)

Current Pacing: +XX% underspending
Days Remaining: X days

Option 1: Conservative Approach
- Increase budget +5-10% (standard)
- Accept that we won't fully catch up this month
- Focus on preventing next month's underspending

Option 2: Aggressive Catch-Up (if performance allows)
- Calculate daily deficit: $(Monthly Budget - MTD Spend) ÷ Days Remaining
- Temporary daily budget increase
- Return to normal after month-end

Recommended: Option 1 (conservative)
- Avoid algorithm shock from large temporary increase
- Better to start next month correctly than force current month
```

---

## Integration with Other Skills

### Prerequisite Skills:
1. **impression-share-diagnostics** — Determines if budget is the constraint
2. A pacing data source — Google Sheet, spreadsheet, or direct API query for MTD spend vs. target

### Workflow:
```
1. impression-share-diagnostics → Diagnoses root cause (budget constraint?)
2. Check pacing variance against your portfolio's tolerance
3. THIS SKILL → Calculates budget recommendation (how much to increase?)
4. Verify current budget data before writing changes
```

---

## Quality Checks Before Recommending

### Pre-Flight Checklist:
✅ Pacing variance exceeds your portfolio's tolerance (typically ±5% to ±10%)
✅ At least 5 days into month (not early-month variance)
✅ CPA within goal or <20% over (performance acceptable)
✅ Budget Lost IS >10% OR Rank Lost IS >50% (constraint exists)
✅ No budget increase in last 7 days (not in ramp-up)
✅ Increase is 5-10% (conservative range)
✅ Daily budget calculation is correct (monthly ÷ days in month)

### If ANY check fails:
- Do NOT recommend budget increase
- Explain which check failed and why
- Provide alternative recommendation

---

## Related Skills in This Repo

- **[impression-share-diagnostics](../impression-share-diagnostics/)** — Root cause diagnosis before recommendation
- **[mutation-safety](../mutation-safety/)** — Two-step approval protocol for writing budget changes to live accounts
- **[gaql-query-patterns](../gaql-query-patterns/)** — GAQL templates for pulling budget and spend data

---

Built by [Kurt Henninger](https://fourteenwebmedia.com). More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
